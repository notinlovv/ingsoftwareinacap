import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { router } from 'expo-router';
import uuid from 'react-native-uuid';
import db from '../db/database'; // Importa la instancia de SQLite

export default function ExploreScreen() {
  const [lineaId, setLineaId] = useState('');
  const [metros, setMetros] = useState('');

  const guardarRegistroLocal = () => {
    if (!lineaId || !metros) {
      Alert.alert('Error', 'Por favor ingresa todos los campos');
      return;
    }

    const nuevoId = uuid.v4() as string;
    const fechaActual = new Date().toISOString();

    try {
      // Guardar en la tabla principal
      db.runSync(
        `INSERT INTO registros_avance (id, linea_id, metros_avanzados, fecha, estado, estado_sync) 
         VALUES (?, ?, ?, ?, 'pendiente', 'pendiente')`,
        [nuevoId, parseInt(lineaId), parseFloat(metros), fechaActual]
      );

      // Registrar la operación en el outbox para futura sincronización
      db.runSync(
        `INSERT INTO outbox (registro_id, operacion, fecha_creacion) VALUES (?, 'CREATE', ?)`,
        [nuevoId, fechaActual]
      );

      Alert.alert('Éxito', 'Registro guardado localmente');
      setLineaId('');
      setMetros('');
    } catch (error) {
      console.error("Error guardando el registro:", error);
      Alert.alert('Error', 'No se pudo guardar el registro localmente');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Nuevo Registro de Avance</Text>
      
      <Text style={styles.label}>ID de Línea Piloto:</Text>
      <TextInput
        style={styles.input}
        placeholder="Ej: 1"
        value={lineaId}
        onChangeText={setLineaId}
        keyboardType="numeric"
      />
      
      <Text style={styles.label}>Metros Avanzados:</Text>
      <TextInput
        style={styles.input}
        placeholder="Ej: 150.5"
        value={metros}
        onChangeText={setMetros}
        keyboardType="numeric"
      />
      
      <TouchableOpacity style={styles.button} onPress={guardarRegistroLocal}>
        <Text style={styles.buttonText}>Guardar (Offline)</Text>
      </TouchableOpacity>
      
      <TouchableOpacity style={[styles.button, styles.logoutButton]} onPress={() => router.replace('/')}>
        <Text style={styles.buttonText}>Cerrar Sesión</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
    paddingTop: 50,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    marginBottom: 5,
    color: '#555',
  },
  input: {
    backgroundColor: '#f9f9f9',
    padding: 15,
    borderRadius: 8,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  button: {
    backgroundColor: '#28a745',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  logoutButton: {
    backgroundColor: '#dc3545',
  },
  buttonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
});
