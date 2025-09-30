# AI Animal Road Safety System

A Streamlit-based web application that helps drivers identify potential animal crossing zones and provides safety recommendations for their routes.

## Features

- 🗺️ Interactive map showing animal zones and routes
- ⚠️ Real-time risk assessment for selected routes
- 🦌 Species-specific safety recommendations
- 📊 Route statistics and risk metrics
- 🚗 Multiple pre-configured routes with risk levels

## Project Structure

```
ai-animal-road-safety/
├── backend/
│   ├── app.py                # Streamlit main application
│   ├── requirements.txt      # Python dependencies
│   ├── data/
│   │   ├── animal_zones.csv  # Animal crossing zone data
│   │   └── routes.csv        # Route information
│   └── utils/
│       └── distance_calc.py  # Distance calculation utilities
├── README.md
└── .gitignore
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-animal-road-safety
```

2. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

## Usage

1. Navigate to the backend directory:
```bash
cd backend
```

2. Run the Streamlit application:
```bash
streamlit run app.py
```

3. Open your browser and navigate to `http://localhost:8501`

## Features Overview

### Interactive Map
- View animal crossing zones with different risk levels
- See route start and end points
- Zoom and pan to explore different areas

### Route Selection
- Choose from pre-configured routes
- View route distance, estimated time, and risk level
- Get real-time safety recommendations

### Safety Recommendations
- Species-specific advice (deer, moose, bear, elk)
- Risk-based speed recommendations
- Activity period warnings

### Data Structure

#### Animal Zones (animal_zones.csv)
- `zone_name`: Name of the animal crossing zone
- `latitude`, `longitude`: Geographic coordinates
- `species`: Type of animal (deer, moose, bear, etc.)
- `risk_level`: Risk assessment (low, medium, high)
- `activity_period`: When animals are most active
- `radius_meters`: Zone radius in meters
- `description`: Additional information

#### Routes (routes.csv)
- `route_name`: Name of the route
- `start_location`, `end_location`: Route endpoints
- `start_lat`, `start_lon`, `end_lat`, `end_lon`: Coordinates
- `distance_km`: Route distance in kilometers
- `estimated_time`: Estimated travel time
- `risk_level`: Overall route risk assessment
- `description`: Route description

## Customization

### Adding New Animal Zones
Edit `backend/data/animal_zones.csv` to add new animal crossing zones with the required columns.

### Adding New Routes
Edit `backend/data/routes.csv` to add new routes with start/end coordinates and risk assessments.

### Modifying Risk Calculations
Update the risk calculation logic in `backend/utils/distance_calc.py` to adjust how risk scores are computed.

## Dependencies

- **Streamlit**: Web application framework
- **Folium**: Interactive map creation
- **Pandas**: Data manipulation
- **Geopy**: Geographic distance calculations
- **NumPy**: Numerical computations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Future Enhancements

- Real-time traffic data integration
- Weather-based risk adjustments
- Mobile app development
- Machine learning for predictive risk assessment
- Integration with GPS navigation systems
