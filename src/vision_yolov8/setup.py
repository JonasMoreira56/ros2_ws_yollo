from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'vision_yolov8'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'README.md', 'requirements.txt']),
        (
            os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py')),
        ),
    ],
    scripts=[
        'scripts/yolo_detector',
    ],
    install_requires=[
        'setuptools',
        'ultralytics>=8.0.0,<9.0.0',
    ],
    zip_safe=True,
    maintainer='jonas',
    maintainer_email='jonasmoreira076@gmail.com',
    description='ROS 2 Jazzy Python node for Ultralytics YOLOv8 detections.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={},
)
