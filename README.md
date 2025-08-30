# Smart Scheduling Assistant

A Flask-based web application that helps you find available time slots in your Google Calendar using natural language queries.

## Features

- 🔗 **Google Calendar Integration**: Connect multiple calendars and view all events
- 🗣️ **Natural Language Search**: Ask questions like "find me time tomorrow" or "next monday availability"
- 📅 **Multi-Calendar Support**: View events from all connected calendars
- 🎨 **Clean Interface**: Modern, responsive design with calendar legend
- ⚡ **Fast Performance**: Optimized event fetching and caching

## Local Development Setup

### Prerequisites

- Python 3.9 or higher
- Google Cloud Console project with Calendar API enabled
- OAuth 2.0 credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd smart-scheduling-backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Google OAuth credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials
   - Download the `client_secret.json` file
   - Place it in the project root directory

5. **Set environment variables (optional)**
   ```bash
   export SECRET_KEY="your-secret-key-here"
   export FLASK_ENV="development"
   ```

6. **Run the application**
   ```bash
   python3 app.py
   ```

7. **Access the application**
   - Open your browser and go to `http://localhost:8080`
   - Click "Connect Google Calendar" to authenticate
   - Start searching for available time slots!

## Render Deployment

### Automatic Deployment

1. **Connect your GitHub repository to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" and select "Web Service"
   - Connect your GitHub account and select this repository

2. **Configure the service**
   - **Name**: `smart-scheduling-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

3. **Set environment variables in Render**
   - `SECRET_KEY`: A secure random string for Flask sessions
   - `FLASK_ENV`: `production`
   - `RENDER`: `true`

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### Manual Deployment

If you prefer to use the `render.yaml` file:

1. **Push your code to GitHub**
2. **Create a new Web Service in Render**
3. **Select "Deploy from render.yaml"**
4. **Render will use the configuration from `render.yaml`**

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | No | `your_secret_key` |
| `FLASK_ENV` | Flask environment (development/production) | No | `development` |
| `RENDER` | Set to `true` when running on Render | No | `false` |
| `PORT` | Port number (set by Render automatically) | No | `8080` |

## Google Calendar Setup

1. **Create a Google Cloud Project**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project

2. **Enable Google Calendar API**
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - Local: `http://localhost:8080/oauth2callback`
     - Render: `https://your-app-name.onrender.com/oauth2callback`

4. **Download credentials**
   - Download the JSON file
   - Rename to `client_secret.json`
   - Place in project root

## Usage Examples

### Natural Language Queries

- "find me some time tomorrow"
- "next monday availability"
- "free time this week"
- "available slots next week"
- "when am I free on friday"

### Features

- **Calendar Navigation**: Use arrow buttons to navigate between months
- **Multi-Calendar View**: See events from all connected calendars with color coding
- **Real-time Search**: Get instant results for available time slots
- **Responsive Design**: Works on desktop and mobile devices

## Project Structure

```
smart-scheduling-backend/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment configuration
├── client_secret.json    # Google OAuth credentials (not in repo)
├── static/
│   └── css/
│       └── style.css     # Application styles
├── templates/
│   ├── index.html        # Main application interface
│   └── landing.html      # Landing page for unauthenticated users
└── README.md             # This file
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Make sure you're in the virtual environment
   - Run `pip install -r requirements.txt`

2. **OAuth errors**
   - Verify `client_secret.json` is in the project root
   - Check redirect URIs in Google Cloud Console
   - Ensure Calendar API is enabled

3. **No events showing**
   - Make sure you're authenticated with Google
   - Check that you have events in your calendar
   - Verify calendar permissions

4. **Render deployment issues**
   - Check build logs in Render dashboard
   - Verify environment variables are set
   - Ensure `gunicorn` is in requirements.txt

### Local Development Tips

- Use `export FLASK_ENV=development` for debug mode
- Check browser console for JavaScript errors
- Use browser developer tools to inspect network requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
