# Sheltr Application Startup Guide

## Quick Start (Recommended)

### Option 1: Using Batch File (Easiest)
Simply double-click `start_sheltr.bat` in the project root directory.

### Option 2: Using PowerShell Script
Right-click `start_sheltr.ps1` and select "Run with PowerShell"

## Manual Startup

If you prefer to start components separately:

### Backend (Python API)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python sheltr_backend.py
```

Backend will run on: **http://localhost:5000**

### Frontend (React Native/Expo)
```bash
cd SheltrFE
npm install
npx expo start
```

Follow the Expo CLI instructions to:
- Press `w` to open in web browser
- Scan QR code with Expo Go app on mobile device
- Press `a` for Android emulator
- Press `i` for iOS simulator

## Prerequisites

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Git** (optional) - [Download](https://git-scm.com/)

## Troubleshooting

### Backend Issues

**"Python not found"**
- Install Python from python.org
- Ensure Python is added to PATH during installation

**"Module not found" errors**
- Activate virtual environment: `.venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**"File not found" errors**
- Ensure you're in the `backend` directory
- Check that data files exist in `../data/` directory

### Frontend Issues

**"npm not found"**
- Install Node.js from nodejs.org
- Restart terminal after installation

**"Cannot connect to backend"**
- Ensure backend is running on http://localhost:5000
- Check `SheltrFE\app\(tabs)\map.tsx` line 47 for correct API URL
- For mobile device testing, change `localhost` to your computer's IP address

**Expo errors**
- Clear cache: `npx expo start -c`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`

## Project Structure

```
Sheltr - Complete/
├── backend/                 # Python Flask API
│   ├── sheltr_backend.py   # Main API server
│   ├── comprehensive_route_calculator.py
│   ├── inference_script.py
│   └── requirements.txt
├── SheltrFE/               # React Native frontend
│   ├── app/                # App screens
│   ├── components/         # Reusable components
│   └── package.json
├── data/                   # Road network data
│   ├── segments_safe_min_dedup.csv
│   ├── segments_safe_min_dedup.geojson
│   └── segments_graph.csv
├── models/                 # ML models
│   ├── rf_model_balanced.joblib
│   └── scaler.joblib
├── start_sheltr.bat       # Windows batch startup
└── start_sheltr.ps1       # PowerShell startup

```

## Features

- **Flood Risk Prediction**: ML-based flood risk assessment for road segments
- **Safe Routing**: Dijkstra's algorithm with flood risk weighting
- **Evacuation Centers**: POI-based evacuation center locations
- **Real-time Updates**: Live route calculation and safety scoring

## API Endpoints

- `GET /` - API information
- `GET /api/health` - Health check
- `GET /api/segments` - All road segments with safety data
- `POST /api/predict` - Predict flood risk for coordinates
- `POST /api/calculate-route` - Calculate optimal route
- `POST /api/nearest-safe-route` - Route to nearest safe point
- `GET /api/evacuation-centers` - Get evacuation centers
- `GET /api/flood-risk` - Get flood risk overlay data

## Configuration

### Backend Configuration
Edit `backend/sheltr_backend.py`:
- Port: Line 675 `app.run(host='0.0.0.0', port=5000)`
- Data paths: Lines 124-138

### Frontend Configuration
Edit `SheltrFE/app/(tabs)/map.tsx`:
- API URL: Line 47 `const API_BASE_URL = 'http://localhost:5000/api'`

## Development Notes

- Backend uses Flask with CORS enabled for cross-origin requests
- Frontend uses Expo Router for navigation
- Coordinate system: EPSG:32651 (UTM Zone 51N) for Philippines
- ML model: Random Forest classifier for flood risk prediction

## Support

For issues or questions:
1. Check this guide's Troubleshooting section
2. Review console output for error messages
3. Ensure all dependencies are installed correctly
