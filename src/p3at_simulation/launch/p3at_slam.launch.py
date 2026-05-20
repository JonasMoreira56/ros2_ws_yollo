import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share_dir = get_package_share_directory('p3at_simulation')
    slam_toolbox_share_dir = get_package_share_directory('slam_toolbox')

    use_sim_time = LaunchConfiguration('use_sim_time')
    rviz = LaunchConfiguration('rviz')
    rviz_config = LaunchConfiguration('rviz_config')
    teleop = LaunchConfiguration('teleop')

    p3at_praca_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share_dir, 'launch', 'p3at_praca.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
        }.items(),
    )

    slam_toolbox_launch = TimerAction(
        period=3.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        slam_toolbox_share_dir,
                        'launch',
                        'online_async_launch.py',
                    )
                ),
                launch_arguments={
                    'use_sim_time': use_sim_time,
                }.items(),
            )
        ],
    )

    start_rviz = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                arguments=['-d', rviz_config],
                parameters=[{'use_sim_time': use_sim_time}],
                condition=IfCondition(rviz),
                output='screen',
            )
        ],
    )

    start_keyboard_teleop = TimerAction(
        period=6.0,
        actions=[
            Node(
                package='p3at_simulation',
                executable='keyboard_teleop',
                name='p3at_keyboard_teleop',
                parameters=[{
                    'speed': 0.35,
                    'turn': 0.75,
                    'repeat_rate': 10.0,
                }],
                condition=IfCondition(teleop),
                output='screen',
                emulate_tty=True,
            )
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation time.',
        ),
        DeclareLaunchArgument(
            'rviz',
            default_value='true',
            description='Start RViz.',
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=os.path.join(
                pkg_share_dir,
                'rviz',
                'p3at_slam.rviz',
            ),
            description='RViz configuration file.',
        ),
        DeclareLaunchArgument(
            'teleop',
            default_value='true',
            description='Start keyboard teleoperation.',
        ),
        p3at_praca_launch,
        slam_toolbox_launch,
        start_rviz,
        start_keyboard_teleop,
    ])
