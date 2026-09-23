# AI-Based Smart Parking Detection and Management System Using Computer Vision

SmartPark AI is a final-year CSE (AI/ML) project that analyzes a parking-lot image or video using a real Ultralytics YOLO model. It detects vehicles, compares each detection with administrator-drawn parking regions, and reports which spaces are occupied or available. Results, processed media, and analytics are stored locally in SQLite.

## Problem statement and solution

Drivers waste time and fuel searching manually for empty parking. This application uses computer vision to detect vehicles and maps them to preconfigured parking-space polygons. It provides an annotated result, dashboard, history, parking layout, and analytics rather than relying on manual counting.

## Features

- Real YOLO vehicle detection for `car`, `motorcycle`, `bus`, and `truck` (configurable).
- Secure image upload: JPG, JPEG, PNG, WEBP.
- Streaming video upload: MP4, AVI, MOV, MKV (when OpenCV can decode it).
- Administrator reference-image uploader and click-to-draw polygon parking-space editor.
- Deterministic occupancy using vehicle-bounding-box / parking-polygon intersection area.
- Annotated output image or MP4 with detections, space labels, and computed metrics.
- Frame-derived initial, final, minimum, maximum, and average video occupancy.
- SQLite-backed history, dashboard, parking layout, analytics, and JSON APIs.
- Automated unit/API tests for calculation, overlap, empty layout, validation, and persistence.

## Architecture

```text
Image / video → YOLO vehicle detections → configured parking polygons
              → overlap calculation → occupancy statistics
              → annotated output + SQLite → dashboard / history / analytics
```

## Requirements

- Python 3.11 or newer (Python 3.12 tested as compatible).
- Internet access on the first analysis so Ultralytics can download `yolo11n.pt`, unless the model has already been downloaded or `MODEL_PATH` points to a local model.
- Sufficient disk space for Python/PyTorch dependencies and processed media.

## Install on Windows

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell prevents activation, use `Set-ExecutionPolicy -Scope Process Bypass` for that terminal, or run `.\.venv\Scripts\python.exe` in each command instead. The project does not require credentials or a `.env` file for local use.

## Run

```powershell
.\.venv\Scripts\python.exe app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

The default model is `models/yolo11n.pt`. The first actual inference invokes the supported Ultralytics download mechanism. To use a local or custom model, set `MODEL_PATH` before starting:

```powershell
$env:MODEL_PATH = "models\best.pt"
.\.venv\Scripts\python.exe app.py
```

## Workflow

1. Open **Admin** and upload a real parking-lot reference image.
2. Give the configuration a name; it becomes the active layout.
3. Click **Add space**, enter an ID such as `P001`, and click the parking-space corners. Click **Finish polygon** and repeat. The editor converts display clicks back to original-image coordinates before saving.
4. Save the layout. Use **Activate** to switch between saved configurations.
5. On Home, upload an image or video from the same camera angle/layout.
6. View the annotated result, individual space statuses, and history/dashboard data.

## How occupancy works

For every configured parking-space polygon, SmartPark AI calculates the area shared by that polygon and each YOLO vehicle bounding box. The largest fraction is used:

```text
overlap = intersection_area(parking polygon, vehicle bounding box) / parking polygon area
```

The space is **OCCUPIED** when this value is at least `OCCUPANCY_THRESHOLD` (default `0.30`); otherwise it is **AVAILABLE**. This is more robust than checking whether only the bounding-box centre lies in a region. The final percentage is:

```text
occupied spaces / total configured spaces × 100
```

No occupancy values are hardcoded. A layout with no spaces produces a clear error rather than a misleading result.

## Video processing

Video is read sequentially—never loaded all at once. YOLO runs on every frame by default (`VIDEO_FRAME_SKIP=1`) and the annotated frames are written to an output MP4. `VIDEO_FRAME_SKIP` can be increased for performance; summary statistics are calculated only from the frames that were actually inferred. The database stores final space status plus initial, final, min, max, and mean occupancy from the processed frames.

## Configuration

Copy `.env.example` values into environment variables when needed:

| Variable | Default | Purpose |
|---|---:|---|
| `MODEL_PATH` | `yolo11n.pt` | Pretrained or custom Ultralytics weight path |
| `CONFIDENCE_THRESHOLD` | `0.35` | Minimum YOLO detection confidence |
| `IOU_THRESHOLD` | `0.45` | YOLO duplicate-box suppression setting |
| `OCCUPANCY_THRESHOLD` | `0.30` | Fraction of parking region covered before occupied |
| `VIDEO_FRAME_SKIP` | `1` | Analyze every Nth frame |
| `VIDEO_MAX_WIDTH` | `1280` | Resize wide videos for practical processing |
| `VEHICLE_CLASSES` | `car,motorcycle,bus,truck` | COCO classes used for occupancy |

## Database and important files

| Path | Purpose |
|---|---|
| `app.py` | Application factory, blueprint registration, database initialization |
| `config.py` | Central configuration and folders |
| `services/detector.py` | Lazy, real Ultralytics YOLO inference |
| `services/parking_analyzer.py` | Polygon clipping, overlap, and statistics |
| `services/image_processor.py` | Annotated image processing |
| `services/video_processor.py` | Sequential annotated video processing |
| `routes/` | Pages, uploads, admin editor, JSON APIs |
| `database_models/analysis.py` | Analyses, configurations, and spaces tables |
| `templates/admin.html` + `static/js/parking.js` | Coordinate-correct visual layout editor |
| `database/parking.db` | Created automatically at first app start |

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The suite checks file extension validation, overlap/occupancy calculation, zero-space handling, database insertion, and API responses. Use a valid real parking image/video for an end-to-end YOLO check.

## AI model and academic evaluation

The initial system uses pretrained COCO inference; it does **not** claim custom-model accuracy, precision, recall, F1, or mAP. These metrics must be measured from a labelled held-out dataset before reporting them in a project report.

To use a custom model later: collect representative parking-camera images, annotate vehicles in YOLO format, split train/validation/test sets, write `data.yaml`, train/evaluate with Ultralytics, inspect actual precision/recall/F1/mAP, then point `MODEL_PATH` at the resulting `best.pt`.

## Limitations

- The reference layout and analyzed media must have the same camera viewpoint.
- Occlusion, poor lighting, distant vehicles, and inaccurate polygons affect results.
- Pretrained COCO vehicle detection may underperform for unusual camera angles; a domain-specific model can improve it.
- Long videos are processed synchronously in this local demonstration version and may take time.

## Future scope

Live CCTV ingestion, background job/progress queues, number-plate recognition, reservations, mobile notifications, multi-floor layouts, IoT sensor fusion, cloud deployment, navigation, and payment integration are natural next steps.

## Viva explanation

“The administrator first draws each parking bay on a reference image. When an image or video is uploaded, YOLO detects only vehicle classes. For every vehicle and parking polygon, the program calculates how much of the parking area is intersected by the vehicle’s bounding box. If it reaches the configured threshold, the bay is occupied. The backend computes totals and saves the real result in SQLite. For videos it repeats the process frame-by-frame and calculates statistics from those analyzed frames.”
