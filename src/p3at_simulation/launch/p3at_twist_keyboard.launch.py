from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    speed = LaunchConfiguration('speed')
    turn = LaunchConfiguration('turn')

    teleop_twist_keyboard = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        parameters=[{
            'speed': ParameterValue(speed, value_type=float),
            'turn': ParameterValue(turn, value_type=float),
        }],
        remappings=[
            ('cmd_vel', '/cmd_vel'),
        ],
        output='screen',
        emulate_tty=True,
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'speed',
            default_value='0.35',
            description='Initial linear speed in meters per second.',
        ),
        DeclareLaunchArgument(
            'turn',
            default_value='0.75',
            description='Initial angular speed in radians per second.',
        ),
        teleop_twist_keyboard,
    ])
