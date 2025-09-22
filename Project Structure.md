ai-animal-road-safety/
│
├── app.py                   # Main Streamlit app (Python logic, UI, routing)
│
├── requirements.txt         # Dependencies (Streamlit, Folium, Pandas, etc.)
│
├── static/                  # Static files (CSS, JS, Images, Sounds)
│   ├── style.css            # Custom CSS styles
│   ├── script.js            # Optional JavaScript for alerts/animations
│   ├── alert.mp3            # Alert sound file
│   └── logo.png             # Project logo/icon
│
├── data/                    # Data files (zones, incidents, etc.)
│   ├── animal_zones.csv     # Wildlife zones dataset
│   ├── incidents.csv        # Incident history dataset
│   └── routes.json          # Preset routes data (optional)
│
├── utils/                   # Helper Python scripts (modular code)
│   ├── map_utils.py         # Functions for map rendering
│   ├── simulation.py        # Functions for route simulation & alerts
│   ├── audio_utils.py       # Functions for playing alert sounds
│   └── __init__.py
│
└── README.md                # Project description & setup guide
