from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import database, models, schemas, auth

router = APIRouter(prefix="/registros", tags=["Registros de Avance"])

@router.put("/{uuid}", response_model=schemas.RegistroAvanceResponse)
def sincronizar_registro(
    uuid: str,
    registro_in: schemas.RegistroAvanceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    # Validar que el UUID de la URL coincida con el del cuerpo
    if uuid != registro_in.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UUID mismatch")

    # Operación Idempotente: Buscar si el registro ya existe
    registro_existente = db.query(models.RegistroAvance).filter(models.RegistroAvance.id == uuid).first()
    
    if registro_existente:
        # Lógica básica de resolución de conflictos por versión
        if registro_in.version_esquema < registro_existente.version_esquema:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"mensaje": "Versión desactualizada", "version_servidor": registro_existente.version_esquema}
            )
        # Actualizar campos
        for key, value in registro_in.model_dump().items():
            setattr(registro_existente, key, value)
        registro_existente.estado = "sincronizado"
        registro_existente.sincronizado_en = models.utc_now()
        db.commit()
        db.refresh(registro_existente)
        return registro_existente

    # Crear nuevo registro si no existe
    nuevo_registro = models.RegistroAvance(
        **registro_in.model_dump(),
        usuario_id=current_user.id,
        estado="sincronizado",
        sincronizado_en=models.utc_now()
    )
    db.add(nuevo_registro)
    db.commit()
    db.refresh(nuevo_registro)
    return nuevo_registro

@router.get("/", response_model=list[schemas.RegistroAvanceResponse])
def listar_registros(db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    return db.query(models.RegistroAvance).all()