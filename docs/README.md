# Documentacao Do Projeto

Este documento descreve o estado atual do workspace, como executar os
cenarios, quais topicos sao usados e onde continuar o desenvolvimento.

## Requisitos

O projeto foi trabalhado em um ambiente ROS 2 Jazzy com Gazebo Sim. No ambiente
atual, os pacotes usados incluem:

- `rclpy`
- `robot_state_publisher`
- `ros_gz_sim`
- `ros_gz_bridge`
- `ros_gz_interfaces`
- `rosgraph_msgs`
- `rviz2`
- `slam_toolbox`
- `teleop_twist_keyboard`
- `xacro`
- `geometry_msgs`
- `nav_msgs`
- `sensor_msgs`
- `tf2_msgs`
- `std_msgs`
- `cv_bridge`
- `ultralytics`
- `python3-opencv` ou `opencv-python`
- `nav2_map_server`, caso queira salvar mapas com `map_saver_cli`

Instalacao dos pacotes ROS 2 mais importantes:

```bash
sudo apt update
sudo apt install ros-jazzy-slam-toolbox ros-jazzy-rviz2 ros-jazzy-nav2-map-server ros-jazzy-teleop-twist-keyboard
```

Ambiente Python recomendado para YOLOv8 no Jazzy:

```bash
source /opt/ros/jazzy/setup.bash
source /home/jonas/env_tcc/bin/activate
python3 -m pip install -r src/vision_yolov8/requirements.txt
colcon build --symlink-install --packages-select vision_yolov8
source install/setup.bash
```

## Pacote `p3at_simulation`

Responsavel pela descricao e execucao da simulacao do Pioneer 3-AT.

Arquivos principais:

- `launch/p3at_gazebo.launch.py`: launch principal da simulacao.
- `launch/p3at_praca.launch.py`: launch para abrir o cenario de praca.
- `launch/p3at_slam.launch.py`: launch completo com praca, SLAM Toolbox,
  RViz e teleop por teclado.
- `launch/p3at_twist_keyboard.launch.py`: controle manual usando o pacote
  `teleop_twist_keyboard`.
- `launch/p3at_teleop.launch.py`: controle manual proprio por setas.
- `p3at_simulation/keyboard_teleop.py`: no ROS 2 proprio que publica `Twist`
  em `/cmd_vel` a partir das setas.
- `rviz/p3at_slam.rviz`: configuracao RViz para mapa, laser, TF, odometria e
  modelo do robo.
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
- `spawn_x`: posicao X inicial do robo.
- `spawn_y`: posicao Y inicial do robo.
- `spawn_z`: altura inicial do robo no Gazebo.
- `spawn_yaw`: orientacao inicial do robo.
- `use_sim_time`: usa o tempo da simulacao.

Exemplo:

```bash
ros2 launch p3at_simulation p3at_gazebo.launch.py \
  world:=$(ros2 pkg prefix p3at_simulation)/share/p3at_simulation/worlds/praca_ao_ar_livre.sdf \
  spawn_x:=-8.5 \
  spawn_y:=0.0 \
  spawn_z:=0.0
```

### Launch Da Praca

```bash
ros2 launch p3at_simulation p3at_praca.launch.py
```

Este launch carrega `praca_ao_ar_livre.sdf` e coloca o robo na posicao inicial
configurada:

```text
x = -1.5
y = 2.0
z = 0.0
yaw = 0.0
```

### Launch SLAM + RViz + Teclado

```bash
ros2 launch p3at_simulation p3at_slam.launch.py
```

Este launch inicia:

- Gazebo com a praca;
- robo P3-AT no ponto inicial;
- SLAM Toolbox em modo `online_async`;
- RViz com `rviz/p3at_slam.rviz`;
- teleop por teclado publicando em `/cmd_vel`.

Argumentos:

- `use_sim_time`: padrao `true`.
- `rviz`: padrao `true`. Use `rviz:=false` para nao abrir RViz.
- `teleop`: padrao `true`. Use `teleop:=false` para nao iniciar o teclado.
- `rviz_config`: caminho para um arquivo `.rviz` alternativo.

Exemplos:

```bash
ros2 launch p3at_simulation p3at_slam.launch.py rviz:=false
ros2 launch p3at_simulation p3at_slam.launch.py teleop:=false
```

### Teleop Separado

Opcao recomendada para testar com o pacote `teleop_twist_keyboard`:

```bash
ros2 launch p3at_simulation p3at_twist_keyboard.launch.py
```

Ele publica `geometry_msgs/Twist` em `/cmd_vel`.

Argumentos:

- `speed`: velocidade linear inicial. Padrao `0.35`.
- `turn`: velocidade angular inicial. Padrao `0.75`.

Teclas principais:

```text
i = frente
, = re
j/l = girar esquerda/direita
k = parar
q/z = aumenta/diminui velocidade
```

Opcao propria por setas:

```bash
ros2 launch p3at_simulation p3at_teleop.launch.py
```

Se as setas nao forem capturadas corretamente pelo `launch`, execute o no
diretamente no terminal:

```bash
ros2 run p3at_simulation keyboard_teleop
```

O teleop proprio e implementado em `p3at_simulation/keyboard_teleop.py`. Ele
le somente as teclas de seta e publica comandos `geometry_msgs/Twist` no
topico `/cmd_vel`.

Argumentos do teleop proprio:

- `speed`: velocidade linear inicial. Padrao `0.35`.
- `turn`: velocidade angular inicial. Padrao `0.75`.
- `repeat_rate`: taxa de publicacao de `/cmd_vel`. Padrao `10.0`.
- `pulse_duration`: duracao do pulso de velocidade a cada clique. Padrao
  `0.25`.

Teclas do teleop proprio:

```text
seta para cima     = frente
seta para baixo    = re
seta para esquerda = girar para esquerda
seta para direita  = girar para direita
cada clique        = envia um pulso de velocidade e para
```

### Cenario Da Praca

O mundo `praca_ao_ar_livre.sdf` contem:

- piso base;
- areas de gramado;
- caminhos centrais;
- fonte central;
- bancos;
- arvores;
- postes;
- objetos de teste, como bicicleta, lixeira, mochila, caixa, cone e placa;
- ponto inicial azul e ponto final verde para testes de navegacao;
- iluminacao tipo sol.

O cenario foi feito com primitivas SDF simples para manter o projeto leve e
facil de versionar.

## Ponte ROS 2 <-> Gazebo

O launch principal inicia `ros_gz_bridge` para os seguintes topicos:

```text
/cmd_vel
/clock
/odom
/scan
/camera/image_raw
/tf
```

Uso esperado:

- publicar comandos de velocidade em `/cmd_vel`;
- sincronizar nos com o tempo da simulacao em `/clock`;
- ler odometria em `/odom`;
- ler laser em `/scan`;
- ler imagem da camera em `/camera/image_raw`;
- acompanhar transformacoes em `/tf`.

## Pacote `vision_yolov8`

Responsavel pela deteccao de objetos com Ultralytics YOLOv8 em um no Python
ROS 2 Jazzy.

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
- `iou`: limiar IoU da etapa de NMS. Padrao: `0.45`.
- `max_detections`: maximo de deteccoes por imagem. Padrao: `100`.
- `device`: dispositivo de inferencia. Exemplo: `cpu`, `0`, `cuda`.
- `annotated_topic`: topico da imagem anotada. Padrao:
  `/yolo/annotated_image`.
- `detections_topic`: topico das deteccoes em JSON. Padrao:
  `/yolo/detections`.
- `publish_annotated`: publica a imagem anotada. Padrao: `true`.
- `use_sim_time`: usa o clock da simulacao. Padrao: `true`.

Exemplo com modelo treinado:

```bash
ros2 launch vision_yolov8 yolo_detector.launch.py \
  model:=/caminho/para/best.pt \
  confidence:=0.4
```

Topicos publicados:

```text
/yolo/annotated_image
/yolo/detections
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
   cd /home/jonas/ros2_ws
   source /opt/ros/jazzy/setup.bash
   colcon build --symlink-install
   source install/setup.bash
   ```

2. Abrir a praca com SLAM, RViz e teleop proprio por setas:

   ```bash
   ros2 launch p3at_simulation p3at_slam.launch.py
   ```

3. Para testar com `teleop_twist_keyboard`, abra o SLAM sem teleop e rode o
   teleop em outro terminal:

   ```bash
   ros2 launch p3at_simulation p3at_slam.launch.py teleop:=false
   ros2 launch p3at_simulation p3at_twist_keyboard.launch.py
   ```

4. Usar o teclado no terminal do teleop para mover o robo e gerar o mapa.

5. Salvar o mapa:

   ```bash
   ros2 run nav2_map_server map_saver_cli -f mapa_praca
   ```

6. Opcionalmente, rodar somente a praca sem SLAM:

   ```bash
   ros2 launch p3at_simulation p3at_praca.launch.py
   ```

7. Em outro terminal, carregar o ambiente:

   ```bash
   cd /home/jonas/ros2_ws
   source install/setup.bash
   ```

7. Rodar o detector YOLOv8:

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
