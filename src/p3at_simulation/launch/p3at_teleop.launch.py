from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    speed = LaunchConfiguration('speed')
    turn = LaunchConfiguration('turn')
    repeat_rate = LaunchConfiguration('repeat_rate')

    keyboard_teleop = Node(
        package='p3at_simulation',
        executable='keyboard_teleop',
        name='p3at_keyboard_teleop',
        parameters=[{
            'speed': ParameterValue(speed, value_type=float),
            'turn': ParameterValue(turn, value_type=float),
            'repeat_rate': ParameterValue(repeat_rate, value_type=float),
        }],
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
        DeclareLaunchArgument(
            'repeat_rate',
            default_value='10.0',
            description='Command publication rate in Hz.',
        ),
        keyboard_teleop,
    ])
