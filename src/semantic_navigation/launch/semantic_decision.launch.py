from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    detections_topic = LaunchConfiguration('detections_topic')
    image_topic = LaunchConfiguration('image_topic')
    odom_topic = LaunchConfiguration('odom_topic')
    map_topic = LaunchConfiguration('map_topic')
    decision_topic = LaunchConfiguration('decision_topic')
    semantic_costmap_topic = LaunchConfiguration('semantic_costmap_topic')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    reference_goal_topic = LaunchConfiguration('reference_goal_topic')
    map_frame = LaunchConfiguration('map_frame')
    base_frame = LaunchConfiguration('base_frame')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'detections_topic',
            default_value='/yolo/detections',
        ),
        DeclareLaunchArgument(
            'image_topic',
            default_value='/camera/image_raw',
        ),
        DeclareLaunchArgument('odom_topic', default_value='/odom'),
        DeclareLaunchArgument('map_topic', default_value='/map'),
        DeclareLaunchArgument(
            'decision_topic',
            default_value='/semantic/decision',
        ),
        DeclareLaunchArgument(
            'semantic_costmap_topic',
            default_value='/semantic/costmap',
        ),
        DeclareLaunchArgument(
            'cmd_vel_topic',
            default_value='/semantic/cmd_vel',
        ),
        DeclareLaunchArgument(
            'reference_goal_topic',
            default_value='/semantic/reference_goal',
        ),
        DeclareLaunchArgument('map_frame', default_value='map'),
        DeclareLaunchArgument('base_frame', default_value='base_link'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        Node(
            package='semantic_navigation',
            executable='semantic_decision_node',
            name='semantic_decision_node',
            output='screen',
            parameters=[{
                'detections_topic': detections_topic,
                'image_topic': image_topic,
                'odom_topic': odom_topic,
                'map_topic': map_topic,
                'decision_topic': decision_topic,
                'semantic_costmap_topic': semantic_costmap_topic,
                'cmd_vel_topic': cmd_vel_topic,
                'reference_goal_topic': reference_goal_topic,
                'map_frame': map_frame,
                'base_frame': base_frame,
                'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
            }],
        ),
    ])
