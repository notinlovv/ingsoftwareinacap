from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app import auth, database, models, schemas

router = APIRouter(prefix="/registros", tags=["Registros de Avance"])


def _normalizar_utc(fecha: datetime) -> datetime:
    """Asegura que un objeto datetime tenga zona horaria UTC para comparaciones seguras."""
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def _serializar_registro(registro: models.RegistroAvance) -> dict:
    """Serializa un RegistroAvance a un diccionario compatible con columnas JSON de auditoría."""
    return {
        "id": registro.id,
        "linea_id": registro.linea_id,
        "usuario_id": registro.usuario_id,
        "metros_avanzados": registro.metros_avanzados,
        "fecha": registro.fecha.isoformat() if registro.fecha else None,
        "latitud": registro.latitud,
        "longitud": registro.longitud,
        "estado": registro.estado,
        "observacion": registro.observacion,
        "version_esquema": registro.version_esquema,
    }


@router.put("/{uuid}", response_model=schemas.RegistroAvanceResponse)
def sincronizar_registro(
    uuid: str,
    registro_in: schemas.RegistroAvanceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    """
    Crea o actualiza un registro de avance de manera idempotente.
    Valida fecha no futura en UTC, existencia de la línea, límite de metros totales
    y registra la trazabilidad completa en la tabla auditoria.
    """
    # 0. Validar coincidencia entre el UUID de la ruta y el del cuerpo
    if uuid != registro_in.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El UUID de la URL no coincide con el ID del cuerpo de la solicitud",
        )

    # a) Validar que la fecha del registro no sea futura (UTC)
    ahora_utc = models.utc_now()
    fecha_registro_utc = _normalizar_utc(registro_in.fecha)
    if fecha_registro_utc > ahora_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha del registro no puede ser futura (UTC)",
        )

    # b) Validar que la línea de fondeo exista
    linea = (
        db.query(models.LineaFondeo)
        .filter(models.LineaFondeo.id == registro_in.linea_id)
        .first()
    )
    if not linea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La línea de fondeo con ID {registro_in.linea_id} no existe",
        )

    # Operación idempotente: verificar si el registro ya existe
    registro_existente = (
        db.query(models.RegistroAvance).filter(models.RegistroAvance.id == uuid).first()
    )

    if registro_existente:
        # Validar conflicto de versión antes de aplicar cambios
        version_entrante = registro_in.version_esquema or 1
        version_actual = registro_existente.version_esquema or 1
        if version_entrante < version_actual:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "mensaje": "Versión desactualizada",
                    "version_servidor": version_actual,
                },
            )

    # c) Validar que la suma acumulada de metros no supere metros_totales de la línea
    metros_otros_registros = (
        db.query(func.coalesce(func.sum(models.RegistroAvance.metros_avanzados), 0.0))
        .filter(
            models.RegistroAvance.linea_id == registro_in.linea_id,
            models.RegistroAvance.id != uuid,
        )
        .scalar()
        or 0.0
    )
    nuevo_acumulado = float(metros_otros_registros) + float(
        registro_in.metros_avanzados
    )
    if nuevo_acumulado > float(linea.metros_totales):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"La suma acumulada de metros ({nuevo_acumulado:.2f} m) supera "
                f"los metros totales de la línea ({linea.metros_totales:.2f} m)"
            ),
        )

    # d) Actualizar o crear registro y guardar trazabilidad en auditoria
    if registro_existente:
        valores_antes = _serializar_registro(registro_existente)

        for key, value in registro_in.model_dump().items():
            setattr(registro_existente, key, value)
        registro_existente.estado = "sincronizado"
        registro_existente.sincronizado_en = ahora_utc

        db.flush()
        valores_despues = _serializar_registro(registro_existente)

        auditoria = models.Auditoria(
            entidad="registros_avance",
            entidad_id=uuid,
            usuario_id=current_user.id,
            accion="UPDATE",
            valores_antes=valores_antes,
            valores_despues=valores_despues,
            fecha=ahora_utc,
        )
        db.add(auditoria)
        db.commit()
        db.refresh(registro_existente)
        return registro_existente

    nuevo_registro = models.RegistroAvance(
        **registro_in.model_dump(),
        usuario_id=current_user.id,
        estado="sincronizado",
        creado_en=ahora_utc,
        sincronizado_en=ahora_utc,
    )
    db.add(nuevo_registro)
    db.flush()

    valores_despues = _serializar_registro(nuevo_registro)
    auditoria = models.Auditoria(
        entidad="registros_avance",
        entidad_id=uuid,
        usuario_id=current_user.id,
        accion="CREATE",
        valores_antes=None,
        valores_despues=valores_despues,
        fecha=ahora_utc,
    )
    db.add(auditoria)
    db.commit()
    db.refresh(nuevo_registro)
    return nuevo_registro


@router.get(
    "/",
    response_model=list[schemas.RegistroAvanceResponse],
    dependencies=[Depends(auth.get_current_user)],
)
def listar_registros(
    desde: datetime | None = Query(
        default=None,
        description="Filtrar registros creados/sincronizados desde este timestamp (ISO 8601 o Unix)",
    ),
    linea_id: int | None = Query(
        default=None,
        description="Filtrar registros por ID de línea de fondeo",
    ),
    db: Session = Depends(database.get_db),
):
    """Lista los registros de avance permitiendo filtrar por timestamp `desde` y por `linea_id`."""
    query = db.query(models.RegistroAvance)

    if linea_id is not None:
        query = query.filter(models.RegistroAvance.linea_id == linea_id)

    if desde is not None:
        desde_utc = _normalizar_utc(desde)
        desde_naive = desde_utc.replace(tzinfo=None)
        query = query.filter(
            or_(
                models.RegistroAvance.sincronizado_en >= desde_naive,
                models.RegistroAvance.fecha >= desde_naive,
            )
        )

    return query.order_by(models.RegistroAvance.fecha.desc()).all()