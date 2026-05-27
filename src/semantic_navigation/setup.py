from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'semantic_navigation'


setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py')),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jonas',
    maintainer_email='jonasmoreira076@gmail.com',
    description='Semantic decision layer for ROS 2 navigation experiments.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            (
                'semantic_decision_node = '
                'semantic_navigation.semantic_decision_node:main'
            ),
        ],
    },
)
