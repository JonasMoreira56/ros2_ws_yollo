from glob import glob

import os

from setuptools import setup

package_name = 'p3at_simulation'


def package_files(pattern):
    return [
        path for path in glob(pattern)
        if not path.endswith(':Zone.Identifier')
    ]


data_files = [
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    (
        os.path.join('share', package_name, 'launch'),
        package_files('launch/*.launch.py'),
    ),
    (os.path.join('share', package_name, 'urdf'), package_files('urdf/*')),
    (os.path.join('share', package_name, 'worlds'), package_files('worlds/*')),
]

for dirpath, _, filenames in os.walk('meshes'):
    src_files = [
        os.path.join(dirpath, filename)
        for filename in filenames
        if not filename.endswith(':Zone.Identifier')
    ]
    if not src_files:
        continue
    install_path = os.path.join('share', package_name, dirpath)
    data_files.append((install_path, src_files))


setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='edson',
    maintainer_email='edson@todo.todo',
    description='Gazebo simulation package for a Pioneer 3-AT robot.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)
