# from flask import Flask, request, jsonify
# from geopy.distance import geodesic
# from concurrent.futures import ThreadPoolExecutor
# import requests
# import json
# from flask_cors import CORS 

# app = Flask(__name__)
# CORS(app, resources={
#     r"/*": {  # Allow all routes
#         "origins": ["http://localhost:3000"],  # Allow only your React app's origin
#         "methods": ["GET", "POST", "OPTIONS"],  # Allow these HTTP methods
#         "allow_headers": ["Content-Type", "Authorization"],  # Allow these headers
#         "supports_credentials": True  # Enable if you need to send cookies
#     }
# })


# # Function to fetch route data from OSRM
# def get_route_data(start_coords, end_coords):
#     url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}?overview=full&geometries=geojson"
#     response = requests.get(url)
#     if response.status_code == 200:
#         route_data = response.json()
#         if route_data["code"] == "Ok":
#             return route_data
#         else:
#             raise Exception("Error in OSRM route data response")
#     else:
#         raise Exception("Failed to fetch route data from OSRM")

# # Function to fetch traffic and weather data asynchronously
# def fetch_data(point, api_keys):
#     lat, lon = point[1], point[0]  # Reverse lat/lon order from GeoJSON
#     try:
#         # Traffic Data (TomTom API)
#         traffic_url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json?key={api_keys['tomtom']}&point={lat},{lon}"
#         traffic_response = requests.get(traffic_url)
#         traffic_speed = (
#             traffic_response.json()["flowSegmentData"]["currentSpeed"]
#             if traffic_response.status_code == 200
#             else 0
#         )

#         # Weather Data (AQICN API)
#         weather_url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={api_keys['aqicn']}"
#         weather_response = requests.get(weather_url)
#         aqi = (
#             weather_response.json()["data"]["aqi"]
#             if weather_response.status_code == 200
#             else 100  # Default AQI if unavailable
#         )

#         return {"traffic_speed": traffic_speed, "aqi": aqi}
#     except Exception as e:
#         print(f"Error fetching data for point {point}: {e}")
#         return {"traffic_speed": 0, "aqi": 100}

# # Function to calculate emissions based on distance
# def calculate_emissions(distance_km, fuel_efficiency, emission_factor):
#     fuel_used = (distance_km / 100) * fuel_efficiency  # Fuel consumed in liters
#     emissions = fuel_used * emission_factor  # Emissions in grams
#     return emissions

# # Function to calculate travel time based on traffic speed
# def calculate_travel_time(distance_km, traffic_speed_kmh):
#     # Time in hours: Distance / Speed
#     if traffic_speed_kmh > 0:
#         return distance_km / traffic_speed_kmh
#     else:
#         return float("inf")  # If no traffic speed data, return infinite time

# # Function to optimize route with reduced API calls
# @app.route('/optimize_route', methods=['POST'])
# def optimize_route():
#     data = request.get_json()
#     start_coords = tuple(data['start_coords'])
#     end_coords = tuple(data['end_coords'])
#     vehicle_data = data['vehicle_data']
#     api_keys = data['api_keys']

#     try:
#         # Fetch initial route data
#         route_data = get_route_data(start_coords, end_coords)
#         route_geometry = route_data["routes"][0]["geometry"]["coordinates"]
#         route_distance = route_data["routes"][0]["distance"] / 1000  # Convert to km

#         # Sample every 10th point to reduce API calls
#         sampled_points = route_geometry[::10]

#         # Fetch traffic and weather data for sampled points
#         with ThreadPoolExecutor() as executor:
#             results = list(
#                 executor.map(lambda point: fetch_data(point, api_keys), sampled_points)
#             )

#         # Calculate total score and check if rerouting is necessary
#         total_score = 0
#         total_travel_time = 0  # Initialize total travel time
#         reroute_needed = False  # Flag to indicate if rerouting is necessary

#         for i, result in enumerate(results):
#             traffic_speed = result["traffic_speed"]
#             # Estimate the distance between consecutive points
#             if i < len(route_geometry) - 1:
#                 distance_between_points = geodesic(route_geometry[i], route_geometry[i + 1]).km
#                 # Calculate the expected time for this segment based on traffic speed
#                 segment_time = calculate_travel_time(distance_between_points, traffic_speed)
#                 total_travel_time += segment_time

#             traffic_score = traffic_speed / 100  # Normalize traffic speed
#             weather_score = 1 / (result["aqi"] + 1)  # Inverse of AQI
#             total_score += traffic_score + weather_score

#             # If traffic speed is below a threshold, consider rerouting
#             if traffic_speed < 20:  # Example threshold for bad traffic (20 km/h)
#                 reroute_needed = True

#         # If rerouting is needed, recalculate the route by avoiding congested areas
#         if reroute_needed:
#             # Fetch a new route avoiding high-traffic areas (if OSRM supports this)
#             rerouted_route_data = get_route_data(start_coords, end_coords)  # You can use different params to avoid congested areas
#             rerouted_route_geometry = rerouted_route_data["routes"][0]["geometry"]["coordinates"]
#             rerouted_route_distance = rerouted_route_data["routes"][0]["distance"] / 1000  # Convert to km

#             # Update route geometry, distance, and recalculate the scores
#             route_geometry = rerouted_route_geometry
#             route_distance = rerouted_route_distance

#         # Calculate carbon emissions
#         total_emissions = calculate_emissions(
#             route_distance, vehicle_data["fuel_efficiency"], vehicle_data["emission_factor"]
#         )

#         return jsonify({
#             "route_geometry": route_geometry,
#             "route_distance": route_distance,
#             "total_score": total_score,
#             "total_emissions": total_emissions,
#             "estimated_travel_time": total_travel_time
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)})

# if __name__ == '__main__':
#    app.run(port=5000, debug=True)



from flask import Flask, request, jsonify
from geopy.distance import geodesic
from concurrent.futures import ThreadPoolExecutor
import requests
import json
from flask_cors import CORS
from statistics import mean
from datetime import datetime
import pytz
import math

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

def format_time(hours):
    """
    Convert time from hours to a readable format with hours and minutes
    """
    total_minutes = hours * 60
    hours_part = math.floor(total_minutes / 60)
    minutes_part = round(total_minutes % 60)
    
    return {
        "total_hours": round(hours, 2),
        "formatted_time": {
            "hours": hours_part,
            "minutes": minutes_part
        },
        "display_text": f"{hours_part}h {minutes_part}m"
    }

def get_route_data(start_coords, end_coords):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}?overview=full&geometries=geojson"
    response = requests.get(url)
    if response.status_code == 200:
        route_data = response.json()
        if route_data["code"] == "Ok":
            return route_data
        else:
            raise Exception("Error in OSRM route data response")
    else:
        raise Exception("Failed to fetch route data from OSRM")

def fetch_data(point, api_keys):
    lat, lon = point[1], point[0]
    try:
        # Traffic Data with more detailed information
        traffic_url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json?key={api_keys['tomtom']}&point={lat},{lon}"
        traffic_response = requests.get(traffic_url)
        
        if traffic_response.status_code == 200:
            traffic_data = traffic_response.json()["flowSegmentData"]
            traffic_speed = traffic_data.get("currentSpeed", 0)
            free_flow_speed = traffic_data.get("freeFlowSpeed", traffic_speed)
            confidence = traffic_data.get("confidence", 0.8)
        else:
            traffic_speed = 0
            free_flow_speed = 0
            confidence = 0.8

        # Weather Data with more parameters
        weather_url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={api_keys['aqicn']}"
        weather_response = requests.get(weather_url)
        
        if weather_response.status_code == 200:
            weather_data = weather_response.json()["data"]
            aqi = weather_data.get("aqi", 100)
            
            # Extract additional weather parameters if available
            iaqi = weather_data.get("iaqi", {})
            visibility = iaqi.get("h", {}).get("v", 100)  # humidity as visibility proxy
            precipitation = iaqi.get("p", {}).get("v", 0)  # precipitation
        else:
            aqi = 100
            visibility = 100
            precipitation = 0

        return {
            "traffic_speed": traffic_speed,
            "free_flow_speed": free_flow_speed,
            "confidence": confidence,
            "aqi": aqi,
            "visibility": visibility,
            "precipitation": precipitation
        }
    except Exception as e:
        print(f"Error fetching data for point {point}: {e}")
        return {
            "traffic_speed": 0,
            "free_flow_speed": 0,
            "confidence": 0.8,
            "aqi": 100,
            "visibility": 100,
            "precipitation": 0
        }

def calculate_segment_travel_time(distance_km, conditions):
    """
    Calculate travel time for a route segment considering multiple factors
    """
    # Base speed calculation
    if conditions["traffic_speed"] > 0:
        base_speed = conditions["traffic_speed"]
    else:
        base_speed = conditions["free_flow_speed"] if conditions["free_flow_speed"] > 0 else 50

    # Weather impact factors (0 to 1, where 1 means no impact)
    visibility_factor = max(0.3, min(1.0, conditions["visibility"] / 100))
    aqi_factor = max(0.5, min(1.0, 1 - (conditions["aqi"] / 300)))
    precipitation_factor = max(0.6, min(1.0, 1 - (conditions["precipitation"] / 100)))

    # Combined weather impact (geometric mean for more balanced influence)
    weather_impact = (visibility_factor * aqi_factor * precipitation_factor) ** (1/3)

    # Adjust speed based on weather conditions
    adjusted_speed = base_speed * weather_impact

    # Calculate time with confidence factor
    time_hours = (distance_km / adjusted_speed) * (1 + (1 - conditions["confidence"]) * 0.2)
    
    return time_hours

def calculate_emissions(distance_km, fuel_efficiency, emission_factor):
    """
    Calculate carbon emissions based on distance and vehicle characteristics
    
    Args:
        distance_km: Distance in kilometers
        fuel_efficiency: Fuel consumption in L/100km
        emission_factor: CO2 emissions in g/L of fuel
    
    Returns:
        emissions: Total CO2 emissions in grams
    """
    fuel_used = (distance_km / 100) * fuel_efficiency  # Fuel consumed in liters
    emissions = fuel_used * emission_factor  # Emissions in grams
    return emissions

def get_time_period():
    """
    Determine current time period for traffic patterns
    """
    current_time = datetime.now(pytz.UTC)
    hour = current_time.hour
    
    if 6 <= hour < 10:  # Morning rush
        return "morning_rush", 1.3
    elif 16 <= hour < 19:  # Evening rush
        return "evening_rush", 1.4
    elif 23 <= hour < 5:  # Night time
        return "night", 0.9
    else:  # Regular hours
        return "regular", 1.0

@app.route('/optimize_route', methods=['POST'])
def optimize_route():
    data = request.get_json()
    start_coords = tuple(data['start_coords'])
    end_coords = tuple(data['end_coords'])
    vehicle_data = data['vehicle_data']
    api_keys = data['api_keys']

    try:
        # Fetch initial route data
        route_data = get_route_data(start_coords, end_coords)
        route_geometry = route_data["routes"][0]["geometry"]["coordinates"]
        route_distance = route_data["routes"][0]["distance"] / 1000  # Convert to km

        # Adaptive sampling based on route length
        sampling_rate = max(5, min(20, int(len(route_geometry) / 10)))
        sampled_points = route_geometry[::sampling_rate]

        # Fetch traffic and weather data for sampled points
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(lambda point: fetch_data(point, api_keys), sampled_points))

        # Calculate total travel time with improved accuracy
        total_travel_time = 0
        segment_times = []
        reroute_needed = False

        # Get time period factor
        time_period, time_factor = get_time_period()

        for i in range(len(results)):
            if i < len(sampled_points) - 1:
                # Calculate distance between consecutive sampled points
                distance = geodesic(
                    sampled_points[i],
                    sampled_points[i + 1]
                ).km

                # Calculate segment travel time
                segment_time = calculate_segment_travel_time(distance, results[i])
                segment_times.append(segment_time)

                # Apply time period factor
                adjusted_segment_time = segment_time * time_factor
                total_travel_time += adjusted_segment_time

                # Check for severe traffic conditions
                if results[i]["traffic_speed"] < 20 or segment_time > distance / 20:
                    reroute_needed = True

        # Calculate statistical measures for anomaly detection
        if segment_times:
            avg_time = mean(segment_times)
            # Remove obvious anomalies (segments taking more than 2x average time)
            filtered_times = [t for t in segment_times if t < 2 * avg_time]
            total_travel_time = sum(filtered_times) * time_factor

        # Handle rerouting if needed
        if reroute_needed:
            alternative_route = get_route_data(start_coords, end_coords)
            alternative_geometry = alternative_route["routes"][0]["geometry"]["coordinates"]
            alternative_distance = alternative_route["routes"][0]["distance"] / 1000

            # Compare and choose better route
            if alternative_distance < route_distance * 1.2:  # Accept if not more than 20% longer
                route_geometry = alternative_geometry
                route_distance = alternative_distance

        # Calculate carbon emissions
        total_emissions = calculate_emissions(
            route_distance,
            vehicle_data["fuel_efficiency"],
            vehicle_data["emission_factor"]
        )

        # Format the travel time
        formatted_time = format_time(total_travel_time)

        return jsonify({
            "route_geometry": route_geometry,
            "route_distance": route_distance,
            "estimated_travel_time": formatted_time,
            "time_period": time_period,
            "confidence_level": mean(result["confidence"] for result in results),
            "weather_conditions": {
                "average_aqi": mean(result["aqi"] for result in results),
                "average_visibility": mean(result["visibility"] for result in results),
                "average_precipitation": mean(result["precipitation"] for result in results)
            },
            "total_emissions": total_emissions
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
   app.run(port=5000, debug=True)