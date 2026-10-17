import { Stack } from 'expo-router';
import { useEffect } from 'react';
import { initDB } from '../db/database';

export default function RootLayout() {
  useEffect(() => {
    // Inicializar las tablas locales SQLite al arrancar la aplicación
    try {
      initDB();
    } catch (error) {
      console.error("Error inicializando la BD local:", error);
    }
  }, []);

  return (
    <Stack>
      <Stack.Screen 
        name="index" 
        options={{ 
          title: 'Inicio',
          headerShown: false // Oculta la barra superior para que el Login se vea limpio
        }} 
      />
      <Stack.Screen 
        name="explore" 
        options={{ 
          title: 'Captura en Terreno',
          headerBackVisible: false, // Evitar que botón "volver atrás" tire el login
          gestureEnabled: false // Evita que en iOS/Android deslicen para volver al login
        }} 
      />
    </Stack>
  );
}