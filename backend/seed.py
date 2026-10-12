from app.database import SessionLocal
from app.models import Usuario, LineaFondeo
from app.auth import get_password_hash

db = SessionLocal()

def poblar_bd():
    print("Revisando base de datos...")
    
    # Crear usuario de prueba si no existe
    usuario = db.query(Usuario).filter(Usuario.email == "supervisor@fondeo.cl").first()
    if not usuario:
        usuario = Usuario(
            nombre="Supervisor Piloto",
            email="supervisor@fondeo.cl",
            hash_password=get_password_hash("admin123"),
            rol="supervisor"
        )
        db.add(usuario)
        print("Usuario supervisor creado: supervisor@fondeo.cl / admin123")

    # Crear línea de fondeo piloto si no existe
    linea = db.query(LineaFondeo).filter(LineaFondeo.nombre == "Línea Piloto 1").first()
    if not linea:
        linea = LineaFondeo(
            nombre="Línea Piloto 1",
            metros_totales=1500.0
        )
        db.add(linea)
        print("Línea de fondeo piloto creada.")

    db.commit()
    db.close()
    print("Proceso finalizado.")

if __name__ == "__main__":
    poblar_bd()