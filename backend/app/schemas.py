from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Esquemas de Usuario ---
class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr
    rol: str = Field(default="supervisor")
    activo: bool = True

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioResponse(UsuarioBase):
    id: int

    class Config:
        from_attributes = True

# --- Esquemas de Autenticación ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    rol: Optional[str] = None

# --- Esquemas de Línea de Fondeo ---
class LineaFondeoBase(BaseModel):
    nombre: str
    metros_totales: float
    fecha_inicio: datetime
    fecha_meta: Optional[datetime] = None
    estado: str = "activa"

class LineaFondeoCreate(LineaFondeoBase):
    pass


class LineaFondeoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    metros_totales: float | None = Field(default=None, gt=0)
    fecha_inicio: datetime | None = None
    fecha_meta: datetime | None = None
    estado: str | None = None


class LineaFondeoResponse(LineaFondeoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# --- Esquemas de Archivo Adjunto ---
class ArchivoBase(BaseModel):
    ruta: str
    tipo: str | None = None
    tamano: int | None = Field(
        default=None, ge=0, description="Tamaño del archivo en bytes"
    )


class ArchivoCreate(ArchivoBase):
    registro_id: str = Field(..., min_length=36, max_length=36)


class ArchivoResponse(ArchivoBase):
    id: int
    registro_id: str

    model_config = ConfigDict(from_attributes=True)


# --- Esquemas de Registro de Avance ---
class RegistroAvanceBase(BaseModel):
    linea_id: int
    metros_avanzados: float = Field(
        ..., ge=0, description="Los metros no pueden ser negativos"
    )
    fecha: datetime
    latitud: float | None = None
    longitud: float | None = None
    estado: str = "pendiente"
    observacion: str | None = None


class RegistroAvanceCreate(RegistroAvanceBase):
    # El ID (UUID) es requerido porque se genera en la app móvil offline
    id: str = Field(..., min_length=36, max_length=36)
    version_esquema: int | None = 1


class RegistroAvanceResponse(RegistroAvanceBase):
    id: str
    usuario_id: int
    creado_en: datetime
    sincronizado_en: datetime
    version_esquema: int
    archivos: list[ArchivoResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


# --- Esquemas de Auditoría ---
class AuditoriaResponse(BaseModel):
    id: int
    entidad: str
    entidad_id: str
    usuario_id: int | None = None
    accion: str
    valores_antes: dict[str, Any] | None = None
    valores_despues: dict[str, Any] | None = None
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Esquemas de Dashboard ---
class DashboardResumenResponse(BaseModel):
    linea_id: int
    linea_nombre: str
    metros_totales: float
    metros_acumulados: float
    porcentaje_avance: float
    metros_restantes: float
    promedio_diario_ultimos_7_dias: float
    dias_estimados_termino: float | None = None
    fecha_estimada_termino: datetime | None = None
    estado: str
    alerta_atraso: bool

    model_config = ConfigDict(from_attributes=True)