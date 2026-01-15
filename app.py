import os
import json
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io
import uvicorn
from typing import Optional

app = FastAPI(title="YOLO Car Detection API", version="1.0.0")

# --- Allow Frontend Communication ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load Model ---
try:
    print("Loading YOLO11-Nano model...")
    model = YOLO("yolo11n.pt") 
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = YOLO("yolov8n.pt")

# Class ID 2 is Car
TARGET_CLASS_ID = [2] 

# Ensure directories exist
os.makedirs("temp_output", exist_ok=True)
os.makedirs("temp_input", exist_ok=True)
os.makedirs("results", exist_ok=True)  # New folder for JSON results

# Serve frontend static files
if os.path.exists("frontend"):
    # Mount static files (CSS, JS, images)
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
    
    # Serve main pages
    @app.get("/")
    async def read_root():
        return FileResponse("frontend/index.html")
    
    @app.get("/docs.html")
    async def read_docs():
        return FileResponse("frontend/docs.html")
    
    # Serve CSS and JS files directly
    @app.get("/style.css")
    async def get_style():
        return FileResponse("frontend/style.css", media_type="text/css")
    
    @app.get("/script.js")
    async def get_script():
        return FileResponse("frontend/script.js", media_type="application/javascript")

@app.post("/detect/image")
async def detect_in_image(file: UploadFile = File(...)):
    # 1. READ IMAGE
    try:
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        image = image.convert("RGB")
        
        # Create unique filename based on time to avoid overwriting
        timestamp = int(time.time())
        base_filename = file.filename.split('.')[0]
        temp_filename = f"temp_input/{base_filename}_{timestamp}.jpg"
        
        image.save(temp_filename, "JPEG")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image. Error: {e}")

    try:
        # 2. RUN INFERENCE
        results = model.predict(temp_filename, conf=0.25, classes=TARGET_CLASS_ID)
        
        detections = []
        img_width, img_height = image.size # Default size

        if results and len(results) > 0:
            result = results[0]
            img_height, img_width = result.orig_shape
            
            for box in result.boxes:
                detections.append({
                    "class_id": int(box.cls[0]),
                    "class_name": "car",
                    "confidence": round(float(box.conf[0]), 4),
                    "bbox": {
                        "x1": float(box.xyxy[0][0]),
                        "y1": float(box.xyxy[0][1]),
                        "x2": float(box.xyxy[0][2]),
                        "y2": float(box.xyxy[0][3])
                    }
                })

        # 3. SAVE TO JSON
        result_data = {
            "filename": file.filename,
            "timestamp": timestamp,
            "car_count": len(detections),
            "image_width": img_width,
            "image_height": img_height,
            "detections": detections
        }

        # Save JSON file: results/image_name_123456789.json
        json_filename = f"results/{base_filename}_{timestamp}.json"
        with open(json_filename, "w") as json_file:
            json.dump(result_data, json_file, indent=4)

        print(f"Saved results to: {json_filename}")

        return result_data

    finally:
        # Cleanup image file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.post("/track/video")
async def track_in_video(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(400, "Unsupported video format.")

    input_path = f"temp_input/{file.filename}"
    
    with open(input_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    try:
        model.track(
            source=input_path,
            save=True,
            project="temp_output",
            name="tracking",
            exist_ok=True,
            classes=TARGET_CLASS_ID, 
            conf=0.25,
            persist=True
        )

        output_dir = "temp_output/tracking"
        if not os.path.exists(output_dir):
             raise HTTPException(500, "Tracking folder missing.")

        files = os.listdir(output_dir)
        if not files:
            raise HTTPException(500, "No output file generated.")

        full_paths = [os.path.join(output_dir, f) for f in files]
        latest_file = max(full_paths, key=os.path.getmtime)

        return FileResponse(latest_file, media_type="video/mp4")

    except Exception as e:
        raise HTTPException(500, f"Tracking error: {str(e)}")

@app.post("/verify/car")
async def verify_car(
    file: UploadFile = File(...),
    confidence_threshold: Optional[float] = Form(0.5)
):
    """
    Verify if an image contains a car.
    
    - **file**: Image file to verify (required)
    - **confidence_threshold**: Minimum confidence required (0.0-1.0, default: 0.5)
    
    Returns:
    - **is_car**: Boolean indicating if car is detected
    - **status**: "approved" if confidence >= threshold, "failed" otherwise
    - **confidence**: Highest confidence score from detections (0.0-1.0)
    - **detections_count**: Number of car detections found
    - **message**: Human-readable status message
    """
    # Validate confidence threshold
    if not 0.0 <= confidence_threshold <= 1.0:
        raise HTTPException(
            status_code=400, 
            detail="confidence_threshold must be between 0.0 and 1.0"
        )
    
    # 1. READ IMAGE
    try:
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        image = image.convert("RGB")
        
        timestamp = int(time.time())
        base_filename = file.filename.split('.')[0]
        temp_filename = f"temp_input/{base_filename}_{timestamp}.jpg"
        image.save(temp_filename, "JPEG")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image. Error: {e}")

    try:
        # 2. RUN INFERENCE
        results = model.predict(temp_filename, conf=0.25, classes=TARGET_CLASS_ID)
        
        detections = []
        max_confidence = 0.0

        if results and len(results) > 0:
            result = results[0]
            
            for box in result.boxes:
                conf = float(box.conf[0])
                detections.append({
                    "confidence": round(conf, 4),
                    "bbox": {
                        "x1": float(box.xyxy[0][0]),
                        "y1": float(box.xyxy[0][1]),
                        "x2": float(box.xyxy[0][2]),
                        "y2": float(box.xyxy[0][3])
                    }
                })
                max_confidence = max(max_confidence, conf)

        # 3. DETERMINE STATUS
        is_car = len(detections) > 0
        approved = is_car and max_confidence >= confidence_threshold
        
        response = {
            "is_car": is_car,
            "status": "approved" if approved else "failed",
            "confidence": round(max_confidence, 4) if is_car else 0.0,
            "detections_count": len(detections),
            "confidence_threshold": confidence_threshold,
            "message": (
                f"Car detected with {max_confidence*100:.1f}% confidence. Status: {'APPROVED' if approved else 'FAILED'} (threshold: {confidence_threshold*100:.0f}%)"
                if is_car else
                "No car detected in the image."
            )
        }

        return response

    finally:
        # Cleanup image file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)