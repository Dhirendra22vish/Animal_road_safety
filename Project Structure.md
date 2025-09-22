ai-animal-road-safety/
│
├── backend/                     # Python backend (Streamlit or FastAPI/Flask)
│   ├── app.py                   # Main backend app
│   ├── requirements.txt         # Python dependencies
│   ├── data/                    # Datasets
│   │   ├── animal_zones.csv
│   │   ├── incidents.csv
│   │   └── routes.json
│   └── utils/                   # Python helper modules
│       ├── map_utils.py
│       ├── simulation.py
│       ├── audio_utils.py
│       └── __init__.py
│
├── frontend/                    # React frontend (UI)
│   ├── public/                  # Static files (favicon, index.html)
│   ├── src/                     # React components & pages
│   │   ├── App.jsx              # Main React app
│   │   ├── index.js             # Entry point
│   │   ├── components/          # Reusable components
│   │   │   ├── Navbar.jsx
│   │   │   ├── MapView.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── Alerts.jsx
│   │   ├── assets/              # Images/icons
│   │   │   └── logo.png
│   │   └── styles/              # CSS
│   │       └── style.css
│   ├── package.json             # Frontend dependencies
│   └── vite.config.js           # (if using Vite)
│
└── README.md
