#!/bin/bash

# Smart Scheduling Assistant Deployment Script

echo "🚀 Smart Scheduling Assistant Deployment Script"
echo "================================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if client_secret.json exists
if [ ! -f "client_secret.json" ]; then
    echo "⚠️  Warning: client_secret.json not found!"
    echo "   Please download your Google OAuth credentials and place them in the project root."
    echo "   Visit: https://console.cloud.google.com/apis/credentials"
fi

# Set environment variables for local development
export FLASK_ENV=development
export SECRET_KEY="dev-secret-key-change-in-production"

echo "✅ Setup complete!"
echo ""
echo "🌐 To run locally:"
echo "   python3 app.py"
echo ""
echo "🌍 To deploy on Render:"
echo "   1. Push this code to GitHub"
echo "   2. Connect your repo to Render"
echo "   3. Set environment variables in Render dashboard"
echo "   4. Deploy!"
echo ""
echo "📖 See README.md for detailed instructions"
