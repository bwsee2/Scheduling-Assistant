# 🚀 Quick Deployment Guide

## ✅ What's Ready

Your Smart Scheduling Assistant is now configured to run both **locally** and on **Render**!

### 📁 Files Created/Updated:
- ✅ `requirements.txt` - Python dependencies
- ✅ `render.yaml` - Render deployment configuration  
- ✅ `app.py` - Updated for environment detection
- ✅ `.gitignore` - Excludes sensitive files
- ✅ `README.md` - Comprehensive documentation
- ✅ `deploy.sh` - Local setup script

## 🏠 Local Development

### Quick Start:
```bash
# 1. Run the setup script
./deploy.sh

# 2. Start the app
python3 app.py

# 3. Open browser
# http://localhost:8080
```

### Manual Setup:
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run app
python3 app.py
```

## 🌍 Render Deployment

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Deploy on Render

1. **Go to [Render Dashboard](https://dashboard.render.com/)**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Configure:**
   - **Name**: `smart-scheduling-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### Step 3: Set Environment Variables
In Render dashboard, add these environment variables:
- `SECRET_KEY`: `your-secure-random-string-here`
- `FLASK_ENV`: `production`
- `RENDER`: `true`

### Step 4: Deploy!
Click "Create Web Service" and wait for deployment.

## 🔧 Google Calendar Setup

### For Local Development:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Add redirect URI: `http://localhost:8080/oauth2callback`
6. Download `client_secret.json` to project root

### For Render Deployment:
1. In Google Cloud Console, add redirect URI:
   `https://your-app-name.onrender.com/oauth2callback`
2. Update `client_secret.json` if needed

## 🎯 Your App URLs

- **Local**: `http://localhost:8080`
- **Render**: `https://your-app-name.onrender.com`

## 🚨 Important Notes

1. **Environment Detection**: App automatically detects if running on Render vs local
2. **OAuth Redirects**: Different URLs for local vs production
3. **Secret Key**: Change the default secret key in production
4. **HTTPS**: Render provides HTTPS automatically

## 🐛 Troubleshooting

### Local Issues:
- Check virtual environment is activated
- Verify `client_secret.json` exists
- Check port 8080 is available

### Render Issues:
- Check build logs in Render dashboard
- Verify environment variables are set
- Ensure `gunicorn` is in requirements.txt

## 📞 Need Help?

1. Check the full `README.md` for detailed instructions
2. Review Render build logs for deployment issues
3. Test locally first before deploying

---

**🎉 You're all set! Your app can now run both locally and on Render!**
