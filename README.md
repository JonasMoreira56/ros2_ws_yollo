# ROS 2 P3AT Simulation Workspace

Este repositorio contem um workspace ROS 2 para simulacao do robo Pioneer 3-AT
no Gazebo Sim, com sensores simulados e uma base inicial para deteccao visual
com YOLOv8.

## O Que Existe Ate Aqui

- Pacote `p3at_simulation`
  - Modelo do robo P3AT em URDF/Xacro.
  - Malhas 3D do robo e sensores.
  - Launch principal para abrir o robo no Gazebo.
  - Cenario de praca ao ar livre.
  - Marcadores de ponto inicial e ponto final no cenario.
  - Ponte ROS 2 <-> Gazebo para clock, comandos, odometria, laser, camera e TF.
  - Launch integrado com SLAM Toolbox, RViz e controle por teclado.

- Pacote `vision_yolov8`
  - No Python ROS 2 Jazzy para executar Ultralytics YOLOv8 sobre imagens da
    camera.
  - Publicacao de imagem anotada.
  - Publicacao de deteccoes em JSON.

## Estrutura Principal

```text
src/
  p3at_simulation/
    launch/
      p3at_gazebo.launch.py
      p3at_praca.launch.py
      p3at_slam.launch.py
      p3at_teleop.launch.py
    meshes/
    rviz/
      p3at_slam.rviz
    urdf/
    worlds/
      praca_ao_ar_livre.sdf

  vision_yolov8/
    launch/
      yolo_detector.launch.py
    vision_yolov8/
      yolo_detector_node.py

docs/
  README.md
```

## Build

Na raiz do workspace:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Dependencias uteis para SLAM e RViz:

```bash
sudo apt update
sudo apt install ros-jazzy-slam-toolbox ros-jazzy-rviz2 ros-jazzy-nav2-map-server
```

Ambiente Python para YOLOv8:

```bash
source /opt/ros/jazzy/setup.bash
source /home/jonas/env_tcc/bin/activate
python3 -m pip install -r src/vision_yolov8/requirements.txt
colcon build --symlink-install --packages-select vision_yolov8
source install/setup.bash
```

## Executar A Simulacao

Cenario vazio:

```bash
ros2 launch p3at_simulation p3at_gazebo.launch.py
```

Cenario da praca ao ar livre:

```bash
ros2 launch p3at_simulation p3at_praca.launch.py
```

## Executar SLAM + RViz + Teclado

Launch completo para mapear a praca com LiDAR, visualizar no RViz e controlar
o robo pelo teclado:

```bash
ros2 launch p3at_simulation p3at_slam.launch.py
```

Para abrir sem teleop:

```bash
ros2 launch p3at_simulation p3at_slam.launch.py teleop:=false
```

Para abrir sem RViz:

```bash
ros2 launch p3at_simulation p3at_slam.launch.py rviz:=false
```

Controle por teclado em um terminal separado:

```bash
ros2 launch p3at_simulation p3at_teleop.launch.py
```

O controle por teclado usa um teleop proprio do pacote `p3at_simulation`, no
arquivo `p3at_simulation/keyboard_teleop.py`. Ele publica comandos
`geometry_msgs/Twist` no topico `/cmd_vel`.

Teclas:

```text
seta para cima    = frente
seta para baixo   = re
seta para esquerda = girar para esquerda
seta para direita  = girar para direita
soltar as setas    = parar
```

Salvar o mapa gerado pelo SLAM:

```bash
ros2 run nav2_map_server map_saver_cli -f mapa_praca
```

## Executar YOLOv8

Com o ambiente acima ativado e o Gazebo publicando a camera em
`/camera/image_raw`:

```bash
ros2 launch vision_yolov8 yolo_detector.launch.py
```

Com um modelo treinado proprio:

```bash
ros2 launch vision_yolov8 yolo_detector.launch.py model:=/caminho/para/best.pt
```

Saidas principais:

```text
/yolo/annotated_image
/yolo/detections
```

## Verificacao

```bash
colcon test
colcon test-result --verbose
```

## Documentacao

Veja [docs/README.md](docs/README.md) para detalhes de uso, topicos ROS,
launches, estrutura dos pacotes e proximos passos recomendados.
