"""Router de autenticación.

Este módulo define los endpoints para autenticación y gestión de usuarios.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from infrastructure.persistence.database import Usuario, get_db
from infrastructure.security import (
    create_access_token,
    decode_access_token,
    decrypt_credentials,
    encrypt_credentials,
    get_password_hash,
    verify_password,
)
from presentation.api.rest.schemas import (
    PJNCredentialsResponse,
    PJNCredentialsUpdate,
    Token,
    UserRegister,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme para extraer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Dependencia para obtener el usuario actual
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> Usuario:
    """Obtiene el usuario actual desde el token JWT.

    Args:
        token: Token JWT del header Authorization
        db: Sesión de base de datos

    Returns:
        Usuario autenticado

    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(Usuario).filter(Usuario.username == username).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[Usuario, Depends(get_current_user)]
) -> Usuario:
    """Verifica que el usuario actual esté activo.

    Args:
        current_user: Usuario actual

    Returns:
        Usuario activo

    Raises:
        HTTPException: Si el usuario está inactivo
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)) -> Usuario:
    """Registra un nuevo usuario.

    Args:
        user_data: Datos del usuario a registrar
        db: Sesión de base de datos

    Returns:
        Usuario creado

    Raises:
        HTTPException: Si el username o email ya existe
    """
    # Verificar si el username ya existe
    if db.query(Usuario).filter(Usuario.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado",
        )

    # Verificar si el email ya existe
    if db.query(Usuario).filter(Usuario.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    # Crear nuevo usuario
    hashed_password = get_password_hash(user_data.password)
    new_user = Usuario(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> dict:
    """Autentica un usuario y devuelve un token JWT.

    Args:
        form_data: Datos de login (username y password)
        db: Sesión de base de datos

    Returns:
        Token JWT

    Raises:
        HTTPException: Si las credenciales son incorrectas
    """
    # Buscar usuario
    user = db.query(Usuario).filter(Usuario.username == form_data.username).first()

    # Verificar usuario y contraseña
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo",
        )

    # Crear token
    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
) -> Usuario:
    """Obtiene la información del usuario actual.

    Args:
        current_user: Usuario autenticado

    Returns:
        Información del usuario
    """
    return current_user


@router.put("/credentials", response_model=UserResponse)
def update_pjn_credentials(
    credentials: PJNCredentialsUpdate,
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> Usuario:
    """Actualiza las credenciales del PJN del usuario.

    Note:
        Las credenciales deben venir encriptadas desde el cliente.

    Args:
        credentials: Credenciales del PJN (ya encriptadas en el cliente)
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Usuario actualizado
    """
    # Las credenciales ya vienen encriptadas desde el cliente
    # Aquí solo necesitamos encriptarlas con Fernet para almacenamiento
    current_user.pjn_usuario_encrypted = credentials.pjn_usuario_encrypted
    current_user.pjn_password_encrypted = credentials.pjn_password_encrypted

    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/credentials", response_model=PJNCredentialsResponse)
def get_pjn_credentials(
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
) -> dict:
    """Obtiene las credenciales del PJN del usuario.

    Args:
        current_user: Usuario autenticado

    Returns:
        Credenciales del PJN (encriptadas)
    """
    has_credentials = bool(
        current_user.pjn_usuario_encrypted and current_user.pjn_password_encrypted
    )

    return {
        "has_credentials": has_credentials,
        "pjn_usuario_encrypted": current_user.pjn_usuario_encrypted,
        "pjn_password_encrypted": current_user.pjn_password_encrypted,
    }


@router.delete("/credentials", status_code=status.HTTP_200_OK)
def delete_pjn_credentials(
    current_user: Annotated[Usuario, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> dict:
    """Elimina las credenciales del PJN del usuario.

    Args:
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Mensaje de éxito
    """
    current_user.pjn_usuario_encrypted = None
    current_user.pjn_password_encrypted = None

    db.commit()

    return {"message": "Credenciales eliminadas exitosamente"}
