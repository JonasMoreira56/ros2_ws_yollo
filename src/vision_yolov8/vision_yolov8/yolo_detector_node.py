import json

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    from cv_bridge import CvBridge
except ImportError:
    CvBridge = None


class YoloDetectorNode(Node):

    def __init__(self):
        super().__init__('yolo_detector')

        self.declare_parameter('model', 'yolov8n.pt')
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('confidence', 0.25)
        self.declare_parameter('iou', 0.45)
        self.declare_parameter('max_detections', 100)
        self.declare_parameter('device', '')
        self.declare_parameter('annotated_topic', '/yolo/annotated_image')
        self.declare_parameter('detections_topic', '/yolo/detections')
        self.declare_parameter('publish_annotated', True)

        model_path = self.get_parameter('model').value
        image_topic = self.get_parameter('image_topic').value
        annotated_topic = self.get_parameter('annotated_topic').value
        detections_topic = self.get_parameter('detections_topic').value
        publish_annotated = self.get_parameter('publish_annotated').value

        if YOLO is None:
            raise RuntimeError(
                'Missing Python package "ultralytics". Install it in the '
                'same Python environment used by ROS 2 Jazzy.'
            )

        self.publish_annotated = publish_annotated
        self.model = YOLO(model_path)
        self.bridge = CvBridge() if CvBridge is not None else None
        self.class_names = self.model.names

        self.image_sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            qos_profile_sensor_data,
        )
        self.annotated_pub = None
        if self.publish_annotated:
            self.annotated_pub = self.create_publisher(
                Image,
                annotated_topic,
                qos_profile_sensor_data,
            )
        self.detections_pub = self.create_publisher(String, detections_topic, 10)

        self.get_logger().info(
            f'YOLOv8 ready: model={model_path}, input={image_topic}, '
            f'annotated={annotated_topic if publish_annotated else "disabled"}, '
            f'detections={detections_topic}'
        )

    def image_callback(self, msg):
        frame = self.ros_image_to_bgr(msg)
        if frame is None:
            return

        confidence = self.get_parameter('confidence').value
        iou = self.get_parameter('iou').value
        max_detections = self.get_parameter('max_detections').value
        device = self.get_parameter('device').value or None
        results = self.model.predict(
            source=frame,
            conf=confidence,
            iou=iou,
            max_det=max_detections,
            device=device,
            verbose=False,
        )

        result = results[0]
        detections = {
            'header': {
                'stamp': {
                    'sec': msg.header.stamp.sec,
                    'nanosec': msg.header.stamp.nanosec,
                },
                'frame_id': msg.header.frame_id,
            },
            'detections': self.format_detections(result),
        }

        detections_msg = String()
        detections_msg.data = json.dumps(detections)
        self.detections_pub.publish(detections_msg)

        if self.annotated_pub is not None:
            annotated_frame = result.plot()
            self.annotated_pub.publish(self.bgr_to_ros_image(annotated_frame, msg))

    def format_detections(self, result):
        detections = []
        if result.boxes is None:
            return detections

        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                'class_id': class_id,
                'class_name': self.get_class_name(class_id),
                'confidence': confidence,
                'bbox_xyxy': [x1, y1, x2, y2],
            })
        return detections

    def get_class_name(self, class_id):
        if isinstance(self.class_names, dict):
            return self.class_names.get(class_id, str(class_id))

        try:
            return self.class_names[class_id]
        except (IndexError, TypeError):
            return str(class_id)

    def ros_image_to_bgr(self, msg):
        if self.bridge is not None:
            try:
                return self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            except Exception as exc:
                self.get_logger().warn(
                    f'cv_bridge failed, trying manual conversion: {exc}'
                )

        try:
            image = np.frombuffer(msg.data, dtype=np.uint8)
            image = image.reshape((msg.height, msg.step))
            channels = msg.step // msg.width
            image = image[:, :msg.width * channels]
            image = image.reshape((msg.height, msg.width, channels))
        except ValueError as exc:
            self.get_logger().error(f'Invalid image layout: {exc}')
            return None

        if msg.encoding == 'bgr8':
            return image
        if msg.encoding == 'rgb8':
            return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if msg.encoding == 'rgba8':
            return cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        if msg.encoding == 'bgra8':
            return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        if msg.encoding == 'mono8':
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        self.get_logger().error(f'Unsupported image encoding: {msg.encoding}')
        return None

    def bgr_to_ros_image(self, frame, source_msg):
        if self.bridge is not None:
            try:
                msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
                msg.header = source_msg.header
                return msg
            except Exception as exc:
                self.get_logger().warn(
                    f'cv_bridge publish failed, using manual conversion: {exc}'
                )

        msg = Image()
        msg.header = source_msg.header
        msg.height = frame.shape[0]
        msg.width = frame.shape[1]
        msg.encoding = 'bgr8'
        msg.is_bigendian = False
        msg.step = frame.shape[1] * 3
        msg.data = frame.tobytes()
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectorNode()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
