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
  - Ponte ROS 2 <-> Gazebo para comandos, odometria, laser, camera e TF.

- Pacote `vision_yolov8`
  - No ROS 2 inicial para executar YOLOv8 sobre imagens da camera.
  - Publicacao de imagem anotada.
  - Publicacao de deteccoes em JSON.

## Estrutura Principal

```text
src/
  p3at_simulation/
    launch/
      p3at_gazebo.launch.py
      p3at_praca.launch.py
    meshes/
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
colcon build
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

## Executar YOLOv8

Com o Gazebo publicando a camera em `/camera/image_raw`:

```bash
ros2 launch vision_yolov8 yolo_detector.launch.py
```

Com um modelo treinado proprio:

```bash
ros2 launch vision_yolov8 yolo_detector.launch.py model:=/caminho/para/best.pt
```

## Verificacao

```bash
colcon test
colcon test-result --verbose
```

## Documentacao

Veja [docs/README.md](docs/README.md) para detalhes de uso, topicos ROS,
launches, estrutura dos pacotes e proximos passos recomendados.
