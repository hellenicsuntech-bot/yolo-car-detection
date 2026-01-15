import os
import json
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io
import uvicorn
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
    # Warm up the model with a dummy inference to avoid first-request delay
    print("Warming up model...")
    dummy_img = Image.new('RGB', (640, 640), color='black')
    model.predict(dummy_img, conf=0.25, classes=[2], verbose=False)
    print("Model loaded and warmed up successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = YOLO("yolov8n.pt")
    # Warm up fallback model too
    dummy_img = Image.new('RGB', (640, 640), color='black')
    model.predict(dummy_img, conf=0.25, classes=[2], verbose=False)

# Class ID 2 is Car
TARGET_CLASS_ID = [2]

# Thread pool for async inference
executor = ThreadPoolExecutor(max_workers=2)

# Image processing constants
MAX_IMAGE_SIZE = 1920  # Max width/height in pixels
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size 

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

def resize_image_if_needed(image: Image.Image, max_size: int = MAX_IMAGE_SIZE) -> Image.Image:
    """Resize image if it's too large, maintaining aspect ratio"""
    width, height = image.size
    if width <= max_size and height <= max_size:
        return image
    
    # Calculate new dimensions
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))
    
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

def run_inference(image: Image.Image):
    """Run YOLO inference in thread pool"""
    return model.predict(image, conf=0.25, classes=TARGET_CLASS_ID, imgsz=640, verbose=False)

@app.post("/detect/image")
async def detect_in_image(file: UploadFile = File(...)):
    start_time = time.time()
    
    # 1. READ AND VALIDATE IMAGE
    try:
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to start
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        image = image.convert("RGB")
        
        # Resize if too large (faster processing)
        original_size = image.size
        image = resize_image_if_needed(image)
        was_resized = image.size != original_size
        
        timestamp = int(time.time())
        base_filename = file.filename.split('.')[0] if file.filename else "image"
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image. Error: {str(e)}")

    try:
        # 2. RUN INFERENCE (async in thread pool to avoid blocking)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(executor, run_inference, image)
        
        detections = []
        img_width, img_height = image.size

        if results and len(results) > 0:
            result = results[0]
            # Use original dimensions if image was resized
            if was_resized:
                scale_x = original_size[0] / img_width
                scale_y = original_size[1] / img_height
                img_width, img_height = original_size
            else:
                scale_x = scale_y = 1.0
            
            for box in result.boxes:
                # Scale bbox back to original size if image was resized
                x1 = float(box.xyxy[0][0]) * scale_x
                y1 = float(box.xyxy[0][1]) * scale_y
                x2 = float(box.xyxy[0][2]) * scale_x
                y2 = float(box.xyxy[0][3]) * scale_y
                
                detections.append({
                    "class_id": int(box.cls[0]),
                    "class_name": "car",
                    "confidence": round(float(box.conf[0]), 4),
                    "bbox": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2
                    }
                })

        # 3. PREPARE RESPONSE
        processing_time = round(time.time() - start_time, 2)
        result_data = {
            "filename": file.filename,
            "timestamp": timestamp,
            "car_count": len(detections),
            "image_width": img_width,
            "image_height": img_height,
            "detections": detections,
            "processing_time_seconds": processing_time
        }

        # Save JSON file (optional, can be disabled for speed)
        json_filename = f"results/{base_filename}_{timestamp}.json"
        try:
            with open(json_filename, "w") as json_file:
                json.dump(result_data, json_file, indent=4)
        except:
            pass  # Don't fail if file write fails

        return result_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

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
    start_time = time.time()
    
    # Validate confidence threshold
    if not 0.0 <= confidence_threshold <= 1.0:
        raise HTTPException(
            status_code=400, 
            detail="confidence_threshold must be between 0.0 and 1.0"
        )
    
    # 1. READ AND VALIDATE IMAGE
    try:
        # Check file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        image = image.convert("RGB")
        
        # Resize if too large
        image = resize_image_if_needed(image)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image. Error: {str(e)}")

    try:
        # 2. RUN INFERENCE (async in thread pool)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(executor, run_inference, image)
        
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
        processing_time = round(time.time() - start_time, 2)
        
        response = {
            "is_car": is_car,
            "status": "approved" if approved else "failed",
            "confidence": round(max_confidence, 4) if is_car else 0.0,
            "detections_count": len(detections),
            "confidence_threshold": confidence_threshold,
            "processing_time_seconds": processing_time,
            "message": (
                f"Car detected with {max_confidence*100:.1f}% confidence. Status: {'APPROVED' if approved else 'FAILED'} (threshold: {confidence_threshold*100:.0f}%)"
                if is_car else
                "No car detected in the image."
            )
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint to prevent cold starts"""
    return JSONResponse({
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": int(time.time())
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=75)