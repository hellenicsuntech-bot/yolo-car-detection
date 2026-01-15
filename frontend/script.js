// Auto-detect API URL - use relative URL when deployed, localhost when developing
const API_URL = window.location.origin;
let currentDetections = null; // Store detections to redraw on resize

function switchTab(tab) {
    document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(`${tab}-section`).classList.add('active');
    event.target.classList.add('active');
}

// --- Image Detection Logic ---
async function uploadImage() {
    const input = document.getElementById('imageInput');
    const statusText = document.getElementById('imageStatus');
    const imgEl = document.getElementById('uploadedImage');
    const canvas = document.getElementById('detectionCanvas');
    const ctx = canvas.getContext('2d');

    if (!input.files[0]) return alert("Please select an image");

    // 1. Reset UI
    statusText.innerText = "Processing...";
    ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear previous boxes
    currentDetections = null; // Clear stored data

    // 2. Load Image & Display
    const file = input.files[0];
    imgEl.src = URL.createObjectURL(file);
    document.getElementById('imageResultContainer').style.display = 'block';

    const formData = new FormData();
    formData.append("file", file);

    try {
        // 3. Call API with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
        
        const response = await fetch(`${API_URL}/detect/image`, {
            method: "POST",
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        if (!response.ok) throw new Error(`Server Error: ${response.statusText}`);

        const data = await response.json();
        
        // 4. Save data and Draw
        currentDetections = data; 
        
        // Wait for image to load before drawing boxes
        if (imgEl.complete && imgEl.naturalHeight !== 0) {
            drawBoxes();
        } else {
            imgEl.onload = () => drawBoxes();
        }

        // UPDATED: 'data.detections' instead of 'data.cars'
        statusText.innerText = `Detected ${data.detections.length} cars.`;

    } catch (error) {
        console.error(error);
        if (error.name === 'AbortError') {
            alert("Request timed out. The server may be processing. Please try again.");
            statusText.innerText = "Request timed out. Please try again.";
        } else {
            alert("Error: " + error.message);
            statusText.innerText = "Error occurred.";
        }
    }
}

function drawBoxes() {
    // UPDATED: Check for 'detections'
    if (!currentDetections || !currentDetections.detections) return;

    const canvas = document.getElementById('detectionCanvas');
    const img = document.getElementById('uploadedImage');
    const data = currentDetections;

    // Safety: Ensure image has dimensions
    if (img.clientWidth === 0 || img.clientHeight === 0) {
        requestAnimationFrame(drawBoxes);
        return;
    }

    // 1. Match Canvas to Image Size
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    const ctx = canvas.getContext('2d');
    
    // 2. Calculate Scale
    const scaleX = canvas.width / data.image_width;
    const scaleY = canvas.height / data.image_height;

    // 3. Style
    ctx.strokeStyle = "#00FF00";
    ctx.lineWidth = 3;
    ctx.font = "bold 16px Arial";
    ctx.fillStyle = "#00FF00";

    // 4. Draw
    // UPDATED: Iterate over 'detections'
    data.detections.forEach(car => {
        // UPDATED: bbox is now an object {x1, y1, x2, y2}, not a list
        const x1 = car.bbox.x1;
        const y1 = car.bbox.y1;
        const x2 = car.bbox.x2;
        const y2 = car.bbox.y2;

        // Scale coordinates
        const rectX = x1 * scaleX;
        const rectY = y1 * scaleY;
        const rectW = (x2 - x1) * scaleX;
        const rectH = (y2 - y1) * scaleY;

        ctx.strokeRect(rectX, rectY, rectW, rectH);
        
        // Label Background
        const text = `Car ${Math.round(car.confidence * 100)}%`;
        const textWidth = ctx.measureText(text).width;
        
        ctx.fillStyle = "rgba(0, 255, 0, 0.2)";
        ctx.fillRect(rectX, rectY, rectW, rectH);
        
        ctx.fillStyle = "#00FF00";
        ctx.fillRect(rectX, rectY - 20, textWidth + 10, 20);
        
        ctx.fillStyle = "black";
        ctx.fillText(text, rectX + 5, rectY - 5);
    });
}

// --- Video Tracking Logic ---
async function uploadVideo() {
    const input = document.getElementById('videoInput');
    if (!input.files[0]) return alert("Please select a video");

    const formData = new FormData();
    formData.append("file", input.files[0]);

    document.getElementById('videoLoading').style.display = 'block';
    document.getElementById('videoResultContainer').style.display = 'none';

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout for video
        
        const response = await fetch(`${API_URL}/track/video`, {
            method: "POST",
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        if (!response.ok) throw new Error("Video processing failed");

        const blob = await response.blob();
        const videoUrl = URL.createObjectURL(blob);
        
        const videoEl = document.getElementById('processedVideo');
        videoEl.src = videoUrl;
        
        document.getElementById('videoLoading').style.display = 'none';
        document.getElementById('videoResultContainer').style.display = 'block';
    } catch (error) {
        console.error(error);
        if (error.name === 'AbortError') {
            alert("Video processing timed out. Please try with a shorter video.");
        } else {
            alert("Error processing video: " + error.message);
        }
        document.getElementById('videoLoading').style.display = 'none';
    }
}

// Resize listener
window.addEventListener('resize', () => {
    drawBoxes();
});