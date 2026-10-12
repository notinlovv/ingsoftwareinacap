import React, { useEffect, useState } from 'react';
import api from './api';

function Dashboard({ onLogout }) {
  const [registros, setRegistros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRegistros = async () => {
      try {
        const response = await api.get('/registros/');
        setRegistros(response.data);
      } catch (err) {
        setError('Error al obtener los registros. Es posible que el token haya expirado.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRegistros();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    onLogout();
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Panel de Control - Líneas de Fondeo</h1>
        <button onClick={handleLogout} style={{ padding: '8px 15px' }}>Cerrar Sesión</button>
      </header>

      {loading && <p>Cargando datos...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}

      {!loading && !error && (
        <div>
          <h2>Registros de Avance</h2>
          {registros.length === 0 ? (
            <p>No hay registros ingresados todavía.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f2f2f2' }}>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>Línea ID</th>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>Metros</th>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>Fecha</th>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>Estado</th>
                </tr>
              </thead>
              <tbody>
                {registros.map((registro) => (
                  <tr key={registro.id}>
                    <td style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'center' }}>{registro.linea_id}</td>
                    <td style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'center' }}>{registro.metros_avanzados}</td>
                    <td style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'center' }}>
                        {new Date(registro.fecha).toLocaleDateString()}
                    </td>
                    <td style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'center' }}>{registro.estado}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

export default Dashboard;