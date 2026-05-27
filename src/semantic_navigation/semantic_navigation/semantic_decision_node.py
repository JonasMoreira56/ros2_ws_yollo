import json
import math
from dataclasses import dataclass

from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import OccupancyGrid, Odometry
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import Image
from std_msgs.msg import String
from tf2_ros import Buffer, TransformListener


@dataclass(frozen=True)
class SemanticRule:
    semantic_type: str
    action: str
    cost: int
    priority: int


@dataclass
class SemanticMark:
    x: float
    y: float
    cost: int
    radius: float
    label: str
    expires_at_nanoseconds: int


class SemanticDecisionNode(Node):

    RULES = {
        'person': SemanticRule('person', 'slow_or_avoid', 75, 80),
        'bicycle': SemanticRule('bicycle', 'avoid_laterally', 85, 70),
        'trash_bin': SemanticRule('trash_bin', 'fixed_obstacle', 90, 65),
        'backpack': SemanticRule('backpack', 'small_obstacle', 60, 50),
        'cone': SemanticRule('cone', 'forbidden_area', 100, 90),
        'sign': SemanticRule('sign', 'visual_reference', 25, 20),
    }

    CLASS_ALIASES = {
        'bin': 'trash_bin',
        'garbage bin': 'trash_bin',
        'garbage can': 'trash_bin',
        'stop sign': 'sign',
        'traffic cone': 'cone',
        'trash bin': 'trash_bin',
        'trash can': 'trash_bin',
        'trash_bin': 'trash_bin',
    }

    def __init__(self):
        super().__init__('semantic_decision_node')

        self.declare_parameter('detections_topic', '/yolo/detections')
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('map_topic', '/map')
        self.declare_parameter('decision_topic', '/semantic/decision')
        self.declare_parameter('semantic_costmap_topic', '/semantic/costmap')
        self.declare_parameter('cmd_vel_topic', '/semantic/cmd_vel')
        self.declare_parameter(
            'reference_goal_topic',
            '/semantic/reference_goal',
        )
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('confidence_min', 0.35)
        self.declare_parameter('front_zone_ratio', 0.35)
        self.declare_parameter('near_box_height_ratio', 0.42)
        self.declare_parameter('caution_box_height_ratio', 0.22)
        self.declare_parameter('camera_horizontal_fov_deg', 70.0)
        self.declare_parameter('distance_scale_m', 0.9)
        self.declare_parameter('min_estimated_distance_m', 0.7)
        self.declare_parameter('max_estimated_distance_m', 7.0)
        self.declare_parameter('semantic_mark_radius_m', 0.55)
        self.declare_parameter('semantic_mark_ttl_s', 6.0)
        self.declare_parameter('detections_stale_s', 1.0)
        self.declare_parameter('publish_rate_hz', 5.0)
        self.declare_parameter('clear_linear_speed', 0.0)
        self.declare_parameter('slow_linear_speed', 0.12)
        self.declare_parameter('avoid_angular_speed', 0.55)
        self.declare_parameter('publish_cmd_vel', True)

        self.map_frame = self.get_parameter('map_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.latest_image_size = None
        self.latest_detections = None
        self.latest_detection_token = None
        self.latest_detection_time = None
        self.last_marked_detection_token = None
        self.latest_odom = None
        self.latest_map = None
        self.semantic_marks = []

        detections_topic = self.get_parameter('detections_topic').value
        image_topic = self.get_parameter('image_topic').value
        odom_topic = self.get_parameter('odom_topic').value
        map_topic = self.get_parameter('map_topic').value
        decision_topic = self.get_parameter('decision_topic').value
        semantic_costmap_topic = (
            self.get_parameter('semantic_costmap_topic').value
        )
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        reference_goal_topic = (
            self.get_parameter('reference_goal_topic').value
        )

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.create_subscription(
            String,
            detections_topic,
            self.detections_callback,
            10,
        )
        self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            qos_profile_sensor_data,
        )
        self.create_subscription(
            Odometry,
            odom_topic,
            self.odom_callback,
            10,
        )
        self.create_subscription(
            OccupancyGrid,
            map_topic,
            self.map_callback,
            1,
        )

        self.decision_pub = self.create_publisher(String, decision_topic, 10)
        self.costmap_pub = self.create_publisher(
            OccupancyGrid,
            semantic_costmap_topic,
            1,
        )
        self.cmd_vel_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        self.reference_goal_pub = self.create_publisher(
            PoseStamped,
            reference_goal_topic,
            10,
        )

        publish_rate = self.get_parameter('publish_rate_hz').value
        self.create_timer(1.0 / publish_rate, self.publish_decision)

        self.get_logger().info(
            'Semantic decision node ready: '
            f'detections={detections_topic}, map={map_topic}, '
            f'decision={decision_topic}, costmap={semantic_costmap_topic}, '
            f'cmd_vel={cmd_vel_topic}'
        )

    def detections_callback(self, msg):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warn(f'Ignoring invalid detection JSON: {exc}')
            return

        detections = payload.get('detections', [])
        if not isinstance(detections, list):
            self.get_logger().warn('Ignoring detection JSON without a list.')
            return

        self.latest_detections = payload
        self.latest_detection_token = self.make_detection_token(payload)
        self.latest_detection_time = self.get_clock().now()

    def image_callback(self, msg):
        self.latest_image_size = (msg.width, msg.height)

    def odom_callback(self, msg):
        self.latest_odom = msg

    def map_callback(self, msg):
        self.latest_map = msg

    def publish_decision(self):
        now = self.get_clock().now()
        now_ns = now.nanoseconds
        self.prune_semantic_marks(now_ns)

        observations = []
        command = self.build_clear_command()
        state = 'clear'
        reason = 'no_recent_semantic_detection'

        if self.has_fresh_detections(now):
            add_marks = (
                self.latest_detection_token != self.last_marked_detection_token
            )
            observations = self.build_observations(add_marks)
            if add_marks and observations:
                self.last_marked_detection_token = self.latest_detection_token

            state, reason, command = self.select_command(observations)

        self.publish_decision_message(state, reason, command, observations)
        self.publish_command(command)
        self.publish_semantic_costmap()

    def has_fresh_detections(self, now):
        no_detection = (
            self.latest_detections is None
            or self.latest_detection_time is None
        )
        if no_detection:
            return False

        stale_s = self.get_parameter('detections_stale_s').value
        age = now - self.latest_detection_time
        return age.nanoseconds <= int(stale_s * 1e9)

    def build_observations(self, add_marks):
        image_width, image_height = self.get_image_size()
        pose = self.get_robot_pose()
        detections = self.latest_detections.get('detections', [])
        observations = []

        for detection in detections:
            observation = self.describe_detection(
                detection,
                image_width,
                image_height,
                pose,
            )
            if observation is None:
                continue

            observations.append(observation)
            if add_marks and observation.get('map_point') is not None:
                self.add_semantic_mark(observation)
                if observation['semantic_type'] == 'sign':
                    self.publish_reference_goal(observation)

        return observations

    def describe_detection(self, detection, image_width, image_height, pose):
        confidence = float(detection.get('confidence', 0.0))
        if confidence < self.get_parameter('confidence_min').value:
            return None

        class_name = str(detection.get('class_name', '')).strip()
        semantic_class = self.normalize_class_name(class_name)
        rule = self.RULES.get(semantic_class)
        if rule is None:
            return None

        bbox = detection.get('bbox_xyxy', [])
        if len(bbox) != 4:
            return None

        x1, y1, x2, y2 = [float(value) for value in bbox]
        box_width = max(1.0, x2 - x1)
        box_height = max(1.0, y2 - y1)
        center_x = x1 + box_width / 2.0
        lateral = ((center_x / image_width) - 0.5) * 2.0
        height_ratio = min(1.0, box_height / image_height)
        width_ratio = min(1.0, box_width / image_width)
        zone = self.classify_zone(lateral, height_ratio)
        distance_m = self.estimate_distance(height_ratio)
        map_point = self.project_to_map(lateral, distance_m, pose)

        return {
            'class_name': class_name,
            'semantic_type': rule.semantic_type,
            'action': rule.action,
            'confidence': round(confidence, 3),
            'priority': rule.priority,
            'cost': rule.cost,
            'zone': zone,
            'lateral_offset': round(lateral, 3),
            'bbox_height_ratio': round(height_ratio, 3),
            'bbox_width_ratio': round(width_ratio, 3),
            'estimated_distance_m': round(distance_m, 2),
            'map_point': map_point,
        }

    def get_image_size(self):
        if self.latest_image_size is not None:
            return self.latest_image_size
        return (640, 480)

    def normalize_class_name(self, class_name):
        normalized = class_name.lower().replace('-', ' ').replace('_', ' ')
        normalized = ' '.join(normalized.split())
        return self.CLASS_ALIASES.get(normalized, normalized)

    def classify_zone(self, lateral, height_ratio):
        front_limit = self.get_parameter('front_zone_ratio').value
        near_limit = self.get_parameter('near_box_height_ratio').value
        caution_limit = self.get_parameter('caution_box_height_ratio').value

        side = 'front'
        if lateral < -front_limit:
            side = 'left'
        elif lateral > front_limit:
            side = 'right'

        depth = 'far'
        if height_ratio >= near_limit:
            depth = 'near'
        elif height_ratio >= caution_limit:
            depth = 'caution'

        return f'{side}_{depth}'

    def estimate_distance(self, height_ratio):
        scale = self.get_parameter('distance_scale_m').value
        min_distance = self.get_parameter('min_estimated_distance_m').value
        max_distance = self.get_parameter('max_estimated_distance_m').value
        distance = scale / max(height_ratio, 0.05)
        return min(max(distance, min_distance), max_distance)

    def project_to_map(self, lateral, distance_m, pose):
        if pose is None:
            return None

        x, y, yaw = pose
        half_fov = math.radians(
            self.get_parameter('camera_horizontal_fov_deg').value / 2.0
        )
        bearing = lateral * half_fov
        point_x = x + distance_m * math.cos(yaw + bearing)
        point_y = y + distance_m * math.sin(yaw + bearing)

        return {
            'frame_id': self.map_frame,
            'x': round(point_x, 3),
            'y': round(point_y, 3),
        }

    def get_robot_pose(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                self.map_frame,
                self.base_frame,
                Time(),
                timeout=Duration(seconds=0.02),
            )
            translation = transform.transform.translation
            rotation = transform.transform.rotation
            return (
                translation.x,
                translation.y,
                self.yaw_from_quaternion(rotation),
            )
        except Exception:
            return self.get_odom_pose()

    def get_odom_pose(self):
        if self.latest_odom is None:
            return None

        pose = self.latest_odom.pose.pose
        return (
            pose.position.x,
            pose.position.y,
            self.yaw_from_quaternion(pose.orientation),
        )

    def select_command(self, observations):
        actionable = [
            item for item in observations
            if item['semantic_type'] != 'sign'
        ]
        if not actionable:
            return 'clear', 'only_visual_references_or_no_action', (
                self.build_clear_command()
            )

        ranked = sorted(
            actionable,
            key=lambda item: (
                self.zone_priority(item['zone']),
                item['priority'],
                item['confidence'],
            ),
            reverse=True,
        )
        main = ranked[0]
        zone = main['zone']
        semantic_type = main['semantic_type']
        lateral = main['lateral_offset']

        command = self.build_clear_command()
        if zone == 'front_near':
            command.linear.x = 0.0
            command.angular.z = self.avoid_turn(lateral)
            if semantic_type == 'person':
                speed = self.get_parameter('slow_linear_speed').value
                command.linear.x = speed
                return 'slow', 'person_close_in_front', command
            return 'avoid', f'{semantic_type}_blocking_front', command

        if zone == 'front_caution':
            command.linear.x = self.get_parameter('slow_linear_speed').value
            command.angular.z = self.avoid_turn(lateral) * 0.5
            return 'slow', f'{semantic_type}_ahead', command

        if zone.endswith('_near') and semantic_type in ('person', 'bicycle'):
            command.linear.x = self.get_parameter('slow_linear_speed').value
            command.angular.z = self.avoid_turn(lateral) * 0.4
            return 'caution', f'{semantic_type}_near_side', command

        return 'clear', 'semantic_objects_not_on_path', command

    def zone_priority(self, zone):
        priorities = {
            'front_near': 100,
            'front_caution': 80,
            'left_near': 60,
            'right_near': 60,
            'left_caution': 40,
            'right_caution': 40,
        }
        return priorities.get(zone, 10)

    def build_clear_command(self):
        command = Twist()
        command.linear.x = self.get_parameter('clear_linear_speed').value
        return command

    def avoid_turn(self, lateral):
        turn = self.get_parameter('avoid_angular_speed').value
        if lateral < -0.1:
            return -turn
        if lateral > 0.1:
            return turn
        return turn

    def publish_decision_message(self, state, reason, command, observations):
        message = {
            'header': {
                'stamp': self.stamp_dict(),
                'frame_id': self.map_frame,
            },
            'state': state,
            'reason': reason,
            'command_hint': {
                'linear_x': round(command.linear.x, 3),
                'angular_z': round(command.angular.z, 3),
            },
            'observations': observations,
        }

        msg = String()
        msg.data = json.dumps(message)
        self.decision_pub.publish(msg)

    def publish_command(self, command):
        if self.get_parameter('publish_cmd_vel').value:
            self.cmd_vel_pub.publish(command)

    def add_semantic_mark(self, observation):
        map_point = observation['map_point']
        ttl_s = self.get_parameter('semantic_mark_ttl_s').value
        radius = self.get_parameter('semantic_mark_radius_m').value
        expires_at = self.get_clock().now().nanoseconds + int(ttl_s * 1e9)
        self.semantic_marks.append(SemanticMark(
            x=map_point['x'],
            y=map_point['y'],
            cost=observation['cost'],
            radius=radius,
            label=observation['semantic_type'],
            expires_at_nanoseconds=expires_at,
        ))

    def prune_semantic_marks(self, now_ns):
        self.semantic_marks = [
            mark for mark in self.semantic_marks
            if mark.expires_at_nanoseconds >= now_ns
        ]

    def publish_semantic_costmap(self):
        if self.latest_map is None:
            return

        msg = OccupancyGrid()
        msg.header = self.latest_map.header
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.info = self.latest_map.info
        data = list(self.latest_map.data)

        for mark in self.semantic_marks:
            self.paint_mark(data, msg.info, mark)

        msg.data = data
        self.costmap_pub.publish(msg)

    def paint_mark(self, data, info, mark):
        resolution = info.resolution
        origin_x = info.origin.position.x
        origin_y = info.origin.position.y
        center_x = int((mark.x - origin_x) / resolution)
        center_y = int((mark.y - origin_y) / resolution)
        radius_cells = max(1, int(mark.radius / resolution))

        for dy in range(-radius_cells, radius_cells + 1):
            for dx in range(-radius_cells, radius_cells + 1):
                if dx * dx + dy * dy > radius_cells * radius_cells:
                    continue
                cell_x = center_x + dx
                cell_y = center_y + dy
                if not self.cell_inside(info, cell_x, cell_y):
                    continue
                index = cell_y * info.width + cell_x
                data[index] = max(int(data[index]), mark.cost)

    def cell_inside(self, info, cell_x, cell_y):
        return (
            0 <= cell_x < info.width
            and 0 <= cell_y < info.height
        )

    def publish_reference_goal(self, observation):
        map_point = observation.get('map_point')
        if map_point is None:
            return

        goal = PoseStamped()
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.header.frame_id = self.map_frame
        goal.pose.position.x = map_point['x']
        goal.pose.position.y = map_point['y']
        goal.pose.orientation.w = 1.0
        self.reference_goal_pub.publish(goal)

    def make_detection_token(self, payload):
        header = payload.get('header', {})
        stamp = header.get('stamp', {})
        return (
            int(stamp.get('sec', 0)),
            int(stamp.get('nanosec', 0)),
            len(payload.get('detections', [])),
        )

    def stamp_dict(self):
        stamp = self.get_clock().now().to_msg()
        return {
            'sec': stamp.sec,
            'nanosec': stamp.nanosec,
        }

    def yaw_from_quaternion(self, quaternion):
        siny_cosp = 2.0 * (
            quaternion.w * quaternion.z + quaternion.x * quaternion.y
        )
        cosy_cosp = 1.0 - 2.0 * (
            quaternion.y * quaternion.y + quaternion.z * quaternion.z
        )
        return math.atan2(siny_cosp, cosy_cosp)


def main(args=None):
    rclpy.init(args=args)
    node = SemanticDecisionNode()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
