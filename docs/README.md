# Documentacao Do Projeto

Este documento descreve o estado atual do workspace, como executar os
cenarios, quais topicos sao usados e onde continuar o desenvolvimento.

## Requisitos

O projeto foi trabalhado em um ambiente ROS 2 com Gazebo Sim. No ambiente atual,
os pacotes usados incluem:

- `rclpy`
- `robot_state_publisher`
- `ros_gz_sim`
- `ros_gz_bridge`
- `ros_gz_interfaces`
- `xacro`
- `geometry_msgs`
- `nav_msgs`
- `sensor_msgs`
- `tf2_msgs`
- `std_msgs`
- `cv_bridge`
- `ultralytics`
- `opencv-python` ou OpenCV equivalente

## Pacote `p3at_simulation`

Responsavel pela descricao e execucao da simulacao do Pioneer 3-AT.

Arquivos principais:

- `launch/p3at_gazebo.launch.py`: launch principal da simulacao.
- `launch/p3at_praca.launch.py`: launch para abrir o cenario de praca.
- `urdf/p3at.xacro`: descricao principal do robo.
- `urdf/p3at.gazebo`: plugins e sensores do Gazebo.
- `worlds/praca_ao_ar_livre.sdf`: mundo da praca ao ar livre.
- `meshes/`: malhas usadas pelo robo e sensores.

### Launch Principal

```bash
ros2 launch p3at_simulation p3at_gazebo.launch.py
```

Argumentos importantes:

- `world`: mundo SDF ou recurso Gazebo que sera carregado.
- `spawn_z`: altura inicial do robo no Gazebo.

Exemplo:

```bash
ros2 launch p3at_simulation p3at_gazebo.launch.py \
  world:=$(ros2 pkg prefix p3at_simulation)/share/p3at_simulation/worlds/praca_ao_ar_livre.sdf \
  spawn_z:=0.14
```

### Launch Da Praca

```bash
ros2 launch p3at_simulation p3at_praca.launch.py
```

Este launch carrega `praca_ao_ar_livre.sdf` e usa `spawn_z:=0.14` para colocar
o robo acima do piso/caminho do cenario.

### Cenario Da Praca

O mundo `praca_ao_ar_livre.sdf` contem:

- piso base;
- areas de gramado;
- caminhos centrais;
- fonte central;
- bancos;
- arvores;
- postes;
- iluminacao tipo sol.

O cenario foi feito com primitivas SDF simples para manter o projeto leve e
facil de versionar.

## Ponte ROS 2 <-> Gazebo

O launch principal inicia `ros_gz_bridge` para os seguintes topicos:

```text
/cmd_vel
/odom
/scan
/camera/image_raw
/tf
```

Uso esperado:

- publicar comandos de velocidade em `/cmd_vel`;
- ler odometria em `/odom`;
- ler laser em `/scan`;
- ler imagem da camera em `/camera/image_raw`;
- acompanhar transformacoes em `/tf`.

## Pacote `vision_yolov8`

Responsavel pela base inicial de visao computacional.

Arquivos principais:

- `vision_yolov8/yolo_detector_node.py`: no ROS 2 de deteccao.
- `launch/yolo_detector.launch.py`: launch do detector.

### Executar O Detector

```bash
ros2 launch vision_yolov8 yolo_detector.launch.py
```

Parametros:

- `model`: caminho ou nome do modelo YOLOv8. Padrao: `yolov8n.pt`.
- `image_topic`: topico de entrada. Padrao: `/camera/image_raw`.
- `confidence`: limiar de confianca. Padrao: `0.25`.
- `device`: dispositivo de inferencia. Exemplo: `cpu`, `0`, `cuda`.

Exemplo com modelo treinado:

```bash
ros2 launch vision_yolov8 yolo_detector.launch.py \
  model:=/caminho/para/best.pt \
  confidence:=0.4
```

### Saidas Do Detector

```text
/yolo/annotated_image
/yolo/detections
```

- `/yolo/annotated_image`: imagem com caixas desenhadas.
- `/yolo/detections`: mensagem `std_msgs/String` contendo uma lista JSON de
  deteccoes.

Formato aproximado de cada deteccao:

```json
{
  "class_id": 0,
  "class_name": "person",
  "confidence": 0.87,
  "bbox_xyxy": [10.0, 25.0, 120.0, 210.0]
}
```

## Fluxo Recomendado De Uso

1. Compilar o workspace:

   ```bash
   colcon build
   source install/setup.bash
   ```

2. Abrir a praca:

   ```bash
   ros2 launch p3at_simulation p3at_praca.launch.py
   ```

3. Em outro terminal, carregar o ambiente:

   ```bash
   cd /home/jonas/ros2_ws
   source install/setup.bash
   ```

4. Rodar o detector YOLOv8:

   ```bash
   ros2 launch vision_yolov8 yolo_detector.launch.py
   ```

## Testes

```bash
colcon test
colcon test-result --verbose
```

## Observacoes

- Os diretorios `build/`, `install/` e `log/` sao gerados pelo `colcon` e nao
  devem ser versionados.
- Arquivos `Zone.Identifier` tambem nao devem ser versionados.
- O diretorio `worlds/` e instalado automaticamente pelo `setup.py` do pacote
  `p3at_simulation`.
- O no YOLOv8 tem conversao manual de imagem como alternativa caso `cv_bridge`
  apresente problema no ambiente.

## Proximos Passos Possiveis

- Adicionar README especifico em cada pacote ROS.
- Criar um mundo com obstaculos dinamicos ou pedestres.
- Publicar deteccoes em `vision_msgs`, se esse pacote for adotado.
- Criar testes de launch para validar argumentos e caminhos instalados.
- Adicionar um arquivo de dependencias ou instrucoes de instalacao do ambiente.
