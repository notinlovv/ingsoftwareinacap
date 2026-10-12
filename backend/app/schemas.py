from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

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

class LineaFondeoResponse(LineaFondeoBase):
    id: int

    class Config:
        from_attributes = True

# --- Esquemas de Registro de Avance ---
class RegistroAvanceBase(BaseModel):
    linea_id: int
    metros_avanzados: float = Field(..., ge=0, description="Los metros no pueden ser negativos")
    fecha: datetime
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    estado: str = "pendiente"
    observacion: Optional[str] = None

class RegistroAvanceCreate(RegistroAvanceBase):
    # El ID (UUID) es requerido aquí porque se genera en la app móvil offline
    id: str = Field(..., min_length=36, max_length=36)
    version_esquema: Optional[int] = 1

class RegistroAvanceResponse(RegistroAvanceBase):
    id: str
    usuario_id: int
    creado_en: datetime
    sincronizado_en: datetime
    version_esquema: int

    class Config:
        from_attributes = True

# --- Esquemas de Archivo ---
class ArchivoResponse(BaseModel):
    id: int
    registro_id: str
    ruta: str
    tipo: str
    tamano: int

    class Config:
        from_attributes = True