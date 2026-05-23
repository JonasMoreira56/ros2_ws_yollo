from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    model = LaunchConfiguration('model')
    image_topic = LaunchConfiguration('image_topic')
    confidence = LaunchConfiguration('confidence')
    iou = LaunchConfiguration('iou')
    max_detections = LaunchConfiguration('max_detections')
    device = LaunchConfiguration('device')
    annotated_topic = LaunchConfiguration('annotated_topic')
    detections_topic = LaunchConfiguration('detections_topic')
    publish_annotated = LaunchConfiguration('publish_annotated')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument('model', default_value='yolov8n.pt'),
        DeclareLaunchArgument('image_topic', default_value='/camera/image_raw'),
        DeclareLaunchArgument('confidence', default_value='0.25'),
        DeclareLaunchArgument('iou', default_value='0.45'),
        DeclareLaunchArgument('max_detections', default_value='100'),
        DeclareLaunchArgument('device', default_value=''),
        DeclareLaunchArgument(
            'annotated_topic',
            default_value='/yolo/annotated_image',
        ),
        DeclareLaunchArgument('detections_topic', default_value='/yolo/detections'),
        DeclareLaunchArgument('publish_annotated', default_value='true'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        Node(
            package='vision_yolov8',
            executable='yolo_detector',
            name='yolo_detector',
            output='screen',
            parameters=[{
                'model': model,
                'image_topic': image_topic,
                'confidence': ParameterValue(confidence, value_type=float),
                'iou': ParameterValue(iou, value_type=float),
                'max_detections': ParameterValue(max_detections, value_type=int),
                'device': device,
                'annotated_topic': annotated_topic,
                'detections_topic': detections_topic,
                'publish_annotated': ParameterValue(
                    publish_annotated,
                    value_type=bool,
                ),
                'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
            }],
        ),
    ])
