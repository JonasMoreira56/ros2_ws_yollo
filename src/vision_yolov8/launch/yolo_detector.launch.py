from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    model = LaunchConfiguration('model')
    image_topic = LaunchConfiguration('image_topic')
    confidence = LaunchConfiguration('confidence')
    device = LaunchConfiguration('device')

    return LaunchDescription([
        DeclareLaunchArgument('model', default_value='yolov8n.pt'),
        DeclareLaunchArgument('image_topic', default_value='/camera/image_raw'),
        DeclareLaunchArgument('confidence', default_value='0.25'),
        DeclareLaunchArgument('device', default_value=''),
        Node(
            package='vision_yolov8',
            executable='yolo_detector',
            name='yolo_detector',
            output='screen',
            parameters=[{
                'model': model,
                'image_topic': image_topic,
                'confidence': confidence,
                'device': device,
            }],
        ),
    ])
