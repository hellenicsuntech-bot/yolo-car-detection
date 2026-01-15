# 🚗 YOLO Car Detection & Verification API

A powerful car detection and verification system using YOLO11, built with FastAPI. Detect cars in images, track them in videos, and verify car presence with customizable confidence thresholds.

## ✨ Features

- **Image Detection**: Detect cars in images with bounding boxes and confidence scores
- **Video Tracking**: Track cars across video frames
- **Car Verification API**: Simple API to verify if an image contains a car (approved/failed based on confidence threshold)
- **Interactive Frontend**: Beautiful web interface for testing
- **Developer Documentation**: Complete API documentation with code examples

## 🚀 Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   cd "yolo car detection"
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the server**:
   ```bash
   python app.py
   ```

3. **Access the app**:
   - Frontend: Open `frontend/index.html` in your browser
   - API Docs: http://127.0.0.1:8000/docs
   - API Base: http://127.0.0.1:8000

## 📡 API Endpoints

### 1. Verify Car (New!)
**POST** `/verify/car`

Verify if an image contains a car with customizable confidence threshold.

**Request:**
- `file`: Image file (multipart/form-data)
- `confidence_threshold`: Optional float (0.0-1.0, default: 0.5)

**Response:**
```json
{
  "is_car": true,
  "status": "approved",
  "confidence": 0.8542,
  "detections_count": 2,
  "confidence_threshold": 0.5,
  "message": "Car detected with 85.4% confidence. Status: APPROVED (threshold: 50%)"
}
```

### 2. Detect Cars in Image
**POST** `/detect/image`

Detect all cars in an image with bounding boxes.

### 3. Track Cars in Video
**POST** `/track/video`

Track cars across video frames.

## 📚 Documentation

- **Interactive API Docs**: Visit `/docs` for Swagger UI
- **Developer Guide**: See `frontend/docs.html` for complete API documentation with code examples

## 🌐 Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for step-by-step deployment instructions to Render.com or other platforms.

**Quick Deploy to Render:**
1. Push code to GitHub
2. Connect repository to Render.com
3. Deploy! (Free tier available)

## 🛠️ Tech Stack

- **Backend**: FastAPI, Uvicorn
- **ML Model**: YOLO11 (Ultralytics)
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Image Processing**: PIL/Pillow, OpenCV

## 📝 Requirements

- Python 3.8+
- See `requirements.txt` for all dependencies

## 🎯 Use Cases

- Vehicle verification systems
- Parking lot monitoring
- Traffic analysis
- Car rental verification
- Insurance claim processing

## 📄 License

This project is open source and available for use.

---

**Made with ❤️ using YOLO11 and FastAPI**
