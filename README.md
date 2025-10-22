## Sheltr

End-to-end flood-aware routing prototype with a React Native frontend and a Python backend.

### Project structure

```
Sheltr FE/
├── SheltrFE/              (frontend - Expo React Native)
├── backend/               (Python API & ML)
├── docs/                  (documentation)
├── data/                  (sample/small data files)
├── models/                (ML models)
└── README.md              (this file)
```

### Backend (Python)

- Entry point: `backend/sheltr_backend.py`
- Models: `models/rf_model_balanced.joblib`, `models/scaler.joblib`
- Data: `data/segments_safe_min_dedup.csv`, `data/segments_graph.csv`, `data/segments_safe_min_dedup.geojson`

Run locally:

```bash
cd backend
python -m venv .venv && . .venv/Scripts/Activate.ps1
pip install -r requirements.txt
python sheltr_backend.py
```

API will run on `http://localhost:5000`.

Optional: provide POIs/evacuation centers by placing a safepoints file in project root or setting `SAFEPOINTS_PATH` to one of: `safepoints.gpkg`, `safepoints.shp`, `safepoints.geojson`, or `safepoints.csv` (CSV must include latitude/longitude columns).

### Frontend (Expo)

The Expo app lives in `SheltrFE`.

Basic dev run:

```bash
cd SheltrFE
npm install
npx expo start --tunnel
```

Configure the app to call the backend at `http://localhost:5000` (or your LAN IP on device).

### Notes

- The repository includes only small sample data sufficient to boot and demo routing.
- For full-quality datasets (large rasters, full geodatabases), keep them outside the repo and point the backend via environment variables or local paths.


