# YOLO model

The default `MODEL_PATH` is `models/yolo11n.pt`. Ultralytics downloads this pretrained COCO model automatically the first time it is used, subject to network access. It detects the configured COCO vehicle classes: car, motorcycle, bus, and truck.

For a custom parking model, train it with Ultralytics and set `MODEL_PATH` to its `.pt` file (or place it in this folder). Do not commit model weights to Git.
