import React, { useState, useEffect } from "react";
import axios from "axios";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet-routing-machine";
import "leaflet/dist/leaflet.css";

// Separate Map Component that handles route display
const RouteMap = ({ routeData, startCoords, endCoords }) => {
  const MapContent = ({ routeData }) => {
    const map = useMap();

    useEffect(() => {
      if (routeData?.route_geometry) {
        const latLngs = routeData.route_geometry.map((coord) => 
          L.latLng(coord[1], coord[0])
        );

        map.eachLayer((layer) => {
          if (layer instanceof L.Polyline || layer instanceof L.Marker) {
            map.removeLayer(layer);
          }
        });

        const routeLine = L.polyline(latLngs, {
          color: 'blue',
          weight: 5,
          opacity: 0.7
        }).addTo(map);

        if (latLngs.length > 0) {
          L.marker(latLngs[0]).addTo(map).bindPopup("Start");
          L.marker(latLngs[latLngs.length - 1]).addTo(map).bindPopup("End");
        }

        if (latLngs.length > 0) {
          map.fitBounds(L.latLngBounds(latLngs));
        }

        // Updated popup content to match backend data
        if (routeData) {
          routeLine.bindPopup(`
            <b>Optimized Route:</b><br />
            Distance: ${routeData.route_distance.toFixed(2)} km<br />
            Travel Time: ${routeData.estimated_travel_time.display_text}<br />
            Period: ${routeData.time_period.replace('_', ' ')}<br />
            Emissions: ${routeData.total_emissions.toFixed(2)} g CO₂<br />
            Confidence: ${(routeData.confidence_level * 100).toFixed(1)}%
          `).openPopup();
        }
      }
    }, [map, routeData]);

    return null;
  };

  return (
    <MapContainer
      center={startCoords[0] !== 0 ? startCoords : [51.505, -0.09]}
      zoom={13}
      style={{ width: "100%", height: "500px" }}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <MapContent routeData={routeData} />
    </MapContainer>
  );
};

// Weather conditions component
const WeatherConditions = ({ conditions }) => {
  return (
    <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded">
      <div>
        <p className="text-gray-600">Air Quality (AQI)</p>
        <p className="font-medium">{conditions.average_aqi.toFixed(1)}</p>
      </div>
      <div>
        <p className="text-gray-600">Visibility</p>
        <p className="font-medium">{conditions.average_visibility.toFixed(1)}%</p>
      </div>
      <div>
        <p className="text-gray-600">Precipitation</p>
        <p className="font-medium">{conditions.average_precipitation.toFixed(1)}mm</p>
      </div>
    </div>
  );
};

// Main RouteForm Component
const RouteForm = () => {
  const [startCoords, setStartCoords] = useState([0, 0]);
  const [endCoords, setEndCoords] = useState([0, 0]);
  const [vehicleData] = useState({
    fuel_efficiency: 10,
    emission_factor: 2.31,
  });
  const [apiKeys] = useState({
    tomtom: "wg3UqAm3mXJt7AE07VQJHmIbiDbKiNix",
    aqicn: "b83a7f6c95d70f8671999d6b7c8d91e969e1bb3f",
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const requestData = {
      start_coords: startCoords,
      end_coords: endCoords,
      vehicle_data: vehicleData,
      api_keys: apiKeys,
    };

    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/optimize_route",
        requestData,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      setResult(response.data);
    } catch (error) {
      console.error("Error fetching optimized route:", error);
      setError("Failed to fetch optimized route. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCoordinateChange = (e, setter) => {
    const value = e.target.value;
    const coords = value.split(",").map((coord) => parseFloat(coord.trim()));
    if (coords.length === 2 && !coords.some(isNaN)) {
      setter(coords);
    } else {
      setError("Invalid coordinates format. Please use format: latitude,longitude");
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4">
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Coordinates
            </label>
            <input
              type="text"
              className="w-full p-2 border rounded"
              value={startCoords}
              onChange={(e) => handleCoordinateChange(e, setStartCoords)}
              placeholder="latitude,longitude (e.g., 51.5074,-0.1278)"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Coordinates
            </label>
            <input
              type="text"
              className="w-full p-2 border rounded"
              value={endCoords}
              onChange={(e) => handleCoordinateChange(e, setEndCoords)}
              placeholder="latitude,longitude (e.g., 48.8566,2.3522)"
            />
          </div>
        </div>
        <button
          type="submit"
          className={`mt-4 px-4 py-2 rounded text-white ${
            loading ? 'bg-blue-400' : 'bg-blue-500 hover:bg-blue-600'
          }`}
          disabled={loading}
        >
          {loading ? 'Optimizing...' : 'Optimize Route'}
        </button>
      </form>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <RouteMap 
        routeData={result} 
        startCoords={startCoords}
        endCoords={endCoords}
      />

      {result && (
        <>
          <div className="mt-4 p-4 bg-gray-50 rounded">
            <h3 className="font-semibold mb-2">Route Details</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-gray-600">Distance</p>
                <p className="font-medium">{result.route_distance.toFixed(2)} km</p>
              </div>
              <div>
                <p className="text-gray-600">Travel Time</p>
                <p className="font-medium">{result.estimated_travel_time.display_text}</p>
              </div>
              <div>
                <p className="text-gray-600">Time Period</p>
                <p className="font-medium">{result.time_period.replace('_', ' ')}</p>
              </div>
              <div>
                <p className="text-gray-600">Emissions</p>
                <p className="font-medium">{result.total_emissions.toFixed(2)} g CO₂</p>
              </div>
              <div>
                <p className="text-gray-600">Confidence</p>
                <p className="font-medium">
                  {(result.confidence_level * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>

          <div className="mt-4">
            <h3 className="font-semibold mb-2">Weather Conditions</h3>
            <WeatherConditions conditions={result.weather_conditions} />
          </div>
        </>
      )}
    </div>
  );
};

export default RouteForm;





