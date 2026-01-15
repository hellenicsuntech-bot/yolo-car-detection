# 🚀 Deployment Guide - YOLO Car Detection

This guide will help you deploy your YOLO Car Detection application to Render.com (free tier available).

## 📋 Prerequisites

1. A GitHub account (free)
2. A Render.com account (free tier available)
3. Your code pushed to a GitHub repository

## 🎯 Step-by-Step Deployment

### Step 1: Push Code to GitHub

1. **Initialize Git** (if not already done):
   ```bash
   cd "/Users/Abdullah/Downloads/yolo car detection"
   git init
   git add .
   git commit -m "Initial commit - YOLO Car Detection App"
   ```

2. **Create a GitHub Repository**:
   - Go to https://github.com/new
   - Create a new repository (e.g., `yolo-car-detection`)
   - **DO NOT** initialize with README, .gitignore, or license

3. **Push Your Code**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/yolo-car-detection.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy to Render

1. **Sign up/Login to Render**:
   - Go to https://render.com
   - Sign up with your GitHub account (free)

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your `yolo-car-detection` repository

3. **Configure Service**:
   - **Name**: `yolo-car-detection` (or any name you like)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: Leave empty (root)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

4. **Environment Variables** (optional):
   - Render automatically sets `PORT` environment variable
   - No additional variables needed for basic deployment

5. **Plan Selection**:
   - Choose **Free** plan (sufficient for testing)
   - Note: Free tier spins down after 15 minutes of inactivity

6. **Click "Create Web Service"**

### Step 3: Wait for Deployment

- Render will:
  1. Clone your repository
  2. Install dependencies (this may take 5-10 minutes)
  3. Download YOLO model files automatically
  4. Start your application

- **First deployment may take 10-15 minutes** (downloading PyTorch and YOLO models)

### Step 4: Access Your Live App

Once deployed, you'll get a URL like:
```
https://yolo-car-detection.onrender.com
```

**Your API endpoints will be:**
- Frontend: `https://yolo-car-detection.onrender.com/`
- API Docs: `https://yolo-car-detection.onrender.com/docs`
- Verify API: `https://yolo-car-detection.onrender.com/verify/car`

## 🔧 Troubleshooting

### Issue: Build Fails
- **Check logs** in Render dashboard
- Ensure `requirements.txt` is in root directory
- Verify Python version compatibility

### Issue: Model Not Found
- YOLO will automatically download models on first run
- This may take a few minutes on first deployment

### Issue: App Spins Down
- Free tier apps spin down after 15 min inactivity
- First request after spin-down takes ~30 seconds
- Consider upgrading to paid plan for always-on service

### Issue: Memory Limits
- Free tier has 512MB RAM limit
- If you hit limits, consider:
  - Using smaller YOLO model (yolo11n.pt is already smallest)
  - Optimizing image sizes before upload

## 📝 Updating Your App

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your update message"
   git push
   ```
3. Render automatically redeploys (takes 5-10 minutes)

## 🌐 Alternative Deployment Options

### Railway.app
- Similar to Render
- Free tier available
- Good for Python apps

### Fly.io
- Free tier with 3 VMs
- Good performance
- More complex setup

### PythonAnywhere
- Simple Python hosting
- Free tier available
- Good for beginners

## ✅ Post-Deployment Checklist

- [ ] Test frontend at your Render URL
- [ ] Test `/verify/car` API endpoint
- [ ] Check `/docs` for Swagger UI
- [ ] Update any hardcoded URLs in your code
- [ ] Share your live URL! 🎉

## 📞 Support

If you encounter issues:
1. Check Render logs in dashboard
2. Verify all files are committed to GitHub
3. Ensure `requirements.txt` includes all dependencies
4. Check that model files (`yolo11n.pt` or `yolov8n.pt`) are accessible

---

**Your app is now live! 🚀**
