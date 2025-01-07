import React, { useState } from 'react';
import RouteForm from './components/RouteForm';
import RouteMap from './components/RouteMap';

const App = () => {
  const [routeGeometry, setRouteGeometry] = useState([]);

  return (
    <div>
      <h1>Route Optimization</h1>
      <RouteForm setRouteGeometry={setRouteGeometry} />
      <RouteMap routeGeometry={routeGeometry} />
    </div>
  );
};

export default App;
