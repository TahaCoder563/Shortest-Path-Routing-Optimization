# Shortest Path Routing Optimization 🚗🗺️

This project is a GUI-based route optimization system built with Python and Tkinter that compares:
* Traditional shortest-distance routing
* Machine Learning–optimized routing that estimates travel time based on road features.
  
It uses OpenStreetMap data, graph algorithms, and a Random Forest model to visualize optimized routes on an interactive map.

## Features
* GUI-based input for start and end locations
* Shortest path calculation using Dijkstra’s algorithm
* Machine Learning–based route optimization
* Road network extraction from OpenStreetMap
* Interactive route visualization using Folium
* Real-time progress indicator with multithreading

## Technologies Used
* Python
* Tkinter (GUI)
* OSMnx & NetworkX (road network & graph algorithms)
* Scikit-learn (Random Forest Regressor)
* NumPy
* Geopy (distance calculations)
* Folium (map visualization)

## Installation
### 1. Clone the repository
```bash
git clone https://github.com/TahaCoder563/Shortest-Path-Routing-Optimization.git
cd Shortest-Path-Routing-Optimization
```
### 2. Install dependencies
```bash
pip install -r requirements.txt
```
### 3. Run the Code
```bash
python main.py
```
