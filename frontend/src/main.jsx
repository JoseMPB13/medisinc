import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

/**
 * Punto de entrada principal de la aplicación React.
 * Renderiza el componente raíz App dentro del elemento HTML 'root'.
 */
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
