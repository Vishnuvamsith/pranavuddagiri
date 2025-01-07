import React from 'react';
import { MapContainer, TileLayer, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const RouteMap = ({ routeGeometry }) => {
  const center = routeGeometry.length > 0 ? routeGeometry[0] : [0, 0];
  const zoom = 13; // Adjust zoom level as per your need

  return (
    <MapContainer center={center} zoom={zoom} style={{ height: '400px', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      {routeGeometry.length > 0 && <Polyline positions={routeGeometry} color="blue" />}
    </MapContainer>
  );
};

export default RouteMap;
