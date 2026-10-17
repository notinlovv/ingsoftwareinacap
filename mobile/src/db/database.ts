import * as SQLite from 'expo-sqlite';

// Abre o crea la base de datos local
const db = SQLite.openDatabaseSync('fondeo_local.db');

export const initDB = () => {
  db.execSync(`
    PRAGMA journal_mode = WAL;
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS registros_avance (
      id TEXT PRIMARY KEY,
      linea_id INTEGER NOT NULL,
      metros_avanzados REAL NOT NULL,
      fecha TEXT NOT NULL,
      latitud REAL,
      longitud REAL,
      estado TEXT DEFAULT 'pendiente',
      observacion TEXT,
      estado_sync TEXT DEFAULT 'pendiente' -- pendiente, sincronizado, conflicto
    );

    CREATE TABLE IF NOT EXISTS outbox (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      registro_id TEXT NOT NULL,
      operacion TEXT NOT NULL, -- 'CREATE', 'UPDATE'
      fecha_creacion TEXT NOT NULL,
      FOREIGN KEY (registro_id) REFERENCES registros_avance (id)
    );
  `);
  console.log("Base de datos local SQLite inicializada");
};

export default db;