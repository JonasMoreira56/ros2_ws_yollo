# vision_yolov8

Pacote ROS 2 Jazzy para rodar deteccao de objetos com Ultralytics YOLOv8 em
um no Python.

## Ambiente Jazzy

Use o mesmo ambiente Python para instalar as dependencias, compilar o pacote e
executar o launch:

```bash
source /opt/ros/jazzy/setup.bash
source /home/jonas/env_tcc/bin/activate
python3 -m pip install -r src/vision_yolov8/requirements.txt
colcon build --symlink-install --packages-select vision_yolov8
source install/setup.bash
```

## Executar

Com a camera publicada em `/camera/image_raw`:

```bash
ros2 launch vision_yolov8 yolo_detector.launch.py
```

Fluxo dos topicos:

```text
/camera/image_raw -> yolo_detector -> /yolo/annotated_image
                                  -> /yolo/detections
```

Com um modelo YOLOv8 treinado:

```bash
ros2 launch vision_yolov8 yolo_detector.launch.py \
  model:=/caminho/para/best.pt \
  confidence:=0.4
```

## Topicos

Entrada:

- `/camera/image_raw` (`sensor_msgs/Image`)

Saidas:

- `/yolo/annotated_image` (`sensor_msgs/Image`)
- `/yolo/detections` (`std_msgs/String` com JSON)

## Parametros

- `model`: nome ou caminho do modelo. Padrao: `yolov8n.pt`.
- `image_topic`: topico de imagem. Padrao: `/camera/image_raw`.
- `confidence`: limiar de confianca. Padrao: `0.25`.
- `iou`: limiar IoU para NMS. Padrao: `0.45`.
- `max_detections`: maximo de deteccoes por imagem. Padrao: `100`.
- `device`: dispositivo de inferencia. Exemplos: `cpu`, `0`, `cuda`.
- `annotated_topic`: topico da imagem anotada.
- `detections_topic`: topico das deteccoes em JSON.
- `publish_annotated`: publica ou nao a imagem anotada. Padrao: `true`.
- `use_sim_time`: usa `/clock` da simulacao. Padrao: `true`.
