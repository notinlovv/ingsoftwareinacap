from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import auth, database, models, schemas

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _normalizar_utc(fecha: datetime) -> datetime:
    """Convierte un datetime naive o con zona horaria a UTC consciente de zona."""
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


@router.get(
    "/resumen",
    response_model=schemas.DashboardResumenResponse,
    dependencies=[Depends(auth.get_current_user)],
)
def obtener_resumen_dashboard(
    linea_id: int | None = Query(
        default=None,
        description="ID de la línea de fondeo a consultar (si se omite, usa la primera línea disponible)",
    ),
    db: Session = Depends(database.get_db),
):
    """
    Calcula las métricas de resumen del dashboard para una línea de fondeo:
    - Metros acumulados, metros restantes y porcentaje de avance.
    - Promedio diario de avance en los últimos 7 días.
    - Días estimados y fecha estimada de término.
    - Alerta de atraso si la fecha estimada supera `fecha_meta`.
    """
    if linea_id is not None:
        linea = (
            db.query(models.LineaFondeo)
            .filter(models.LineaFondeo.id == linea_id)
            .first()
        )
        if not linea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Línea de fondeo con ID {linea_id} no encontrada",
            )
    else:
        linea = (
            db.query(models.LineaFondeo).order_by(models.LineaFondeo.id.asc()).first()
        )
        if not linea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existen líneas de fondeo registradas",
            )

    metros_totales = float(linea.metros_totales)

    # 1. Calcular metros acumulados y porcentaje de avance
    metros_acumulados = float(
        db.query(func.coalesce(func.sum(models.RegistroAvance.metros_avanzados), 0.0))
        .filter(models.RegistroAvance.linea_id == linea.id)
        .scalar()
        or 0.0
    )
    metros_acumulados = round(metros_acumulados, 2)
    porcentaje_avance = (
        round((metros_acumulados / metros_totales) * 100.0, 2)
        if metros_totales > 0
        else 0.0
    )
    metros_restantes = round(max(0.0, metros_totales - metros_acumulados), 2)

    # 2. Calcular promedio diario de los últimos 7 días (UTC)
    ahora_utc = models.utc_now()
    hace_7_dias_naive = (ahora_utc - timedelta(days=7)).replace(tzinfo=None)

    metros_ultimos_7_dias = float(
        db.query(func.coalesce(func.sum(models.RegistroAvance.metros_avanzados), 0.0))
        .filter(
            models.RegistroAvance.linea_id == linea.id,
            models.RegistroAvance.fecha >= hace_7_dias_naive,
        )
        .scalar()
        or 0.0
    )
    promedio_diario_7d = round(metros_ultimos_7_dias / 7.0, 2)

    # 3. Calcular proyección de días restantes y fecha estimada de término
    dias_estimados_termino: float | None = None
    fecha_estimada_termino: datetime | None = None

    if metros_restantes <= 0:
        dias_estimados_termino = 0.0
        fecha_estimada_termino = ahora_utc
    elif promedio_diario_7d > 0:
        dias_exactos = metros_restantes / (metros_ultimos_7_dias / 7.0)
        dias_estimados_termino = round(dias_exactos, 2)
        fecha_estimada_termino = ahora_utc + timedelta(days=dias_exactos)

    # 4. Evaluar alerta de atraso respecto a fecha_meta
    alerta_atraso = False
    if linea.fecha_meta is not None:
        fecha_meta_utc = _normalizar_utc(linea.fecha_meta)
        if fecha_estimada_termino is not None:
            alerta_atraso = _normalizar_utc(fecha_estimada_termino) > fecha_meta_utc
        elif metros_restantes > 0:
            # Si no hay ritmo de avance reciente y existe una meta definida,
            # se alerta atraso al no poder cumplir la fecha meta proyectada
            alerta_atraso = True

    return schemas.DashboardResumenResponse(
        linea_id=linea.id,
        linea_nombre=linea.nombre,
        metros_totales=metros_totales,
        metros_acumulados=metros_acumulados,
        porcentaje_avance=porcentaje_avance,
        metros_restantes=metros_restantes,
        promedio_diario_ultimos_7_dias=promedio_diario_7d,
        dias_estimados_termino=dias_estimados_termino,
        fecha_estimada_termino=fecha_estimada_termino,
        estado=linea.estado,
        alerta_atraso=alerta_atraso,
    )