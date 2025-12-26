import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import webbrowser
import osmnx as ox
import networkx as nx
import geopy.distance
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
import folium

def compute_routes_thread():
    try:
        start_node = start_entry.get()
        end_node = end_entry.get()
        if not start_node or not end_node:
            messagebox.showerror("Error", "Please enter both start and end locations!")
            return
        status_label.config(text="⏳ Processing...")
        
        progress.start()
        
        start_geo = ox.geocode(start_node)
        end_geo = ox.geocode(end_node)
        
        user_start = (start_geo[0], start_geo[1])
        user_end = (end_geo[0], end_geo[1])
        
        dist_between = geopy.distance.distance(user_start, user_end).km
        
        radius_needed = (dist_between * 1000) * 1.5
        
        graph = ox.graph_from_point(user_start, dist=radius_needed, network_type="drive")
        source_node = ox.distance.nearest_nodes(graph, start_geo[1], start_geo[0])
        destination_node = ox.distance.nearest_nodes(graph, end_geo[1], end_geo[0])
        
        shortest_path = nx.shortest_path(graph, source_node, destination_node, weight="length")
        shortest_distance = nx.shortest_path_length(graph, source_node, destination_node, weight="length")
        
        edges_gdf = ox.graph_to_gdfs(graph, nodes=False, edges=True)
        edges_gdf["maxspeed"] = edges_gdf["maxspeed"].astype(str).str.extract(r"(\d+)").astype(float)
        edges_gdf["maxspeed"] = edges_gdf["maxspeed"].fillna(40).clip(5, 120)
        edges_gdf["length_m"] = edges_gdf["length"].clip(1, 10000)
        edges_gdf["highway"] = edges_gdf["highway"].fillna("unclassified").astype(str)
        
        df = edges_gdf[["length_m", "highway", "maxspeed"]].dropna()
        encoder = OneHotEncoder(handle_unknown="ignore")
        highway_encoded = encoder.fit_transform(df[["highway"]]).toarray()
        X = np.hstack([df[["length_m", "maxspeed"]].values, highway_encoded])
        base_time = df["length_m"] / (df["maxspeed"] * (1000 / 3600))
        delay = np.random.uniform(5, 25, len(df))
        y = (base_time + delay) / 60
        model = RandomForestRegressor(n_estimators=10)
        model.fit(X, y)
        df_valid = df.reset_index(drop=True)
        for idx, row in df_valid.iterrows():
            edge_index = edges_gdf[
                (edges_gdf["length_m"] == row["length_m"]) &
                (edges_gdf["maxspeed"] == row["maxspeed"]) &
                (edges_gdf["highway"] == row["highway"])
            ].index[0]
            u, v, k = edge_index
            feat = np.hstack([row[["length_m", "maxspeed"]].values, highway_encoded[idx]])
            graph[u][v][k]["ml_weight"] = model.predict([feat])[0]
        ml_path = nx.shortest_path(graph, source_node, destination_node, weight="ml_weight")
        optimized_time = nx.shortest_path_length(graph, source_node, destination_node, weight="ml_weight")
        distance_label.config(text=f"Shortest Distance: {shortest_distance:.2f} meters")
        ml_label.config(text=f"ML Optimized Time: {optimized_time:.2f} minutes")
        m = folium.Map(location=user_start, zoom_start=14)
        folium.Marker(location=user_start, tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(location=user_end, tooltip="End", icon=folium.Icon(color="red")).add_to(m)
        shortest_coords = [(graph.nodes[n]["y"], graph.nodes[n]["x"]) for n in shortest_path]
        folium.PolyLine(shortest_coords, color="blue", weight=4, tooltip="Shortest Path").add_to(m)
        ml_coords = [(graph.nodes[n]["y"], graph.nodes[n]["x"]) for n in ml_path]
        folium.PolyLine(ml_coords, color="orange", weight=4, tooltip="ML Optimized Path").add_to(m)
        global map_path
        map_path = os.path.abspath("route_map.html")
        m.save(map_path)
        status_label.config(text="✔ Completed – Click 'Open Map in Browser'")
    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_label.config(text="❌ Error")
    finally:
        progress.stop()

def compute_routes():
    threading.Thread(target=compute_routes_thread).start()

def open_map_browser():
    if os.path.exists("route_map.html"):
        webbrowser.open("file://" + map_path)
    else:
        messagebox.showerror("Error", "Map not generated yet!")

root = tk.Tk()
root.title("Shortest Path Routing Optimization")
root.geometry("400x500")
root.configure(bg="#1e1e1e")

frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(fill="both", expand=True, padx=20, pady=20)

tk.Label(frame, text="Shortest Path Routing Optimization", font=("Segoe UI", 18, "bold"),
         bg="#1e1e1e", fg="white").pack(pady=10)

input_frame = tk.Frame(frame, bg="#1e1e1e")
input_frame.pack(pady=10, fill="x")

tk.Label(input_frame, text="Start Location:", bg="#1e1e1e", fg="white").grid(row=0, column=0, padx=5, pady=5, sticky="e")
start_entry = ttk.Entry(input_frame, width=30)
start_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(input_frame, text="End Location:", bg="#1e1e1e", fg="white").grid(row=1, column=0, padx=5, pady=5, sticky="e")
end_entry = ttk.Entry(input_frame, width=30)
end_entry.grid(row=1, column=1, padx=5, pady=5)

compute_btn = tk.Button(frame, text="Compute Routes", command=compute_routes,
                        bg="#4a90e2", fg="white", font=("Segoe UI", 12, "bold"),
                        relief="flat", padx=10, pady=5)
compute_btn.pack(pady=10)

open_map_btn = tk.Button(frame, text="Open Map in Browser", command=open_map_browser,
                         bg="#27ae60", fg="white", font=("Segoe UI", 12, "bold"),
                         relief="flat", padx=10, pady=5)
open_map_btn.pack(pady=10)

distance_label = tk.Label(frame, text="Shortest Distance: ",
                          bg="#1e1e1e", fg="#b4e1ff", font=("Segoe UI", 11))
distance_label.pack(pady=5)

ml_label = tk.Label(frame, text="ML Optimized Time: ",
                    bg="#1e1e1e", fg="#b4e1ff", font=("Segoe UI", 11))
ml_label.pack(pady=5)

progress = ttk.Progressbar(frame, mode="indeterminate")
progress.pack(pady=10)

status_label = tk.Label(frame, text="Ready", bg="#1e1e1e", fg="white")
status_label.pack()

root.mainloop()
