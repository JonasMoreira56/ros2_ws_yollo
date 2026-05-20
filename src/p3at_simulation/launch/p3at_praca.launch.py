import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_share_dir = get_package_share_directory('p3at_simulation')
    world_path = os.path.join(pkg_share_dir, 'worlds', 'praca_ao_ar_livre.sdf')
    use_sim_time = LaunchConfiguration('use_sim_time')

    p3at_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share_dir, 'launch', 'p3at_gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_path,
            'spawn_x': '-8.5',
            'spawn_y': '0.0',
            'spawn_z': '0.14',
            'spawn_yaw': '0.0',
            'use_sim_time': use_sim_time,
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation time.',
        ),
        p3at_launch,
    ])
