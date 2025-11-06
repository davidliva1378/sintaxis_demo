#!/usr/bin/env python
"""Script para inicializar la base de datos del sistema multi-usuario.

Este script crea todas las tablas necesarias en la base de datos y opcionalmente
puede crear un usuario administrador inicial.

Usage:
    python scripts/init_db.py
    python scripts/init_db.py --admin-username admin --admin-email admin@example.com --admin-password password123
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.config import get_settings
from infrastructure.persistence.database import Base, Usuario, engine
from infrastructure.security import generate_fernet_key, get_password_hash


def init_db(create_admin: bool = False, admin_data: dict | None = None, interactive: bool = True) -> None:
    """Inicializa la base de datos.

    Args:
        create_admin: Si True, crea un usuario administrador
        admin_data: Datos del administrador (username, email, password)
        interactive: Si True, pide confirmación al usuario
    """
    settings = get_settings()

    print("=" * 60)
    print("INICIALIZACION DE BASE DE DATOS - Sistema PJN v6")
    print("=" * 60)
    print()

    # Mostrar información de configuración
    print(f"Base de datos: {engine.url}")
    print(f"Storage path: {settings.storage.base_path}")
    print()

    # Verificar si existe clave de encriptación
    if not settings.encryption.fernet_key:
        print("WARNING: No se encontro clave de encriptacion (ENCRYPTION_FERNET_KEY)")
        print("Se generara una nueva clave automaticamente.")
        new_key = generate_fernet_key()
        print()
        print("Por favor, guarde esta clave en su archivo .env:")
        print(f"ENCRYPTION_FERNET_KEY={new_key}")
        print()
        print("IMPORTANTE: Sin esta clave, no podra desencriptar las credenciales PJN")
        print("existentes si reinicia el servidor.")
        print()
        if interactive:
            input("Presione Enter para continuar...")
        print()

    # Crear todas las tablas
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tablas creadas exitosamente")
    print()

    # Crear usuario administrador si se especificó
    if create_admin and admin_data:
        from sqlalchemy.orm import Session

        from infrastructure.persistence.database import SessionLocal

        print("Creando usuario administrador...")

        db: Session = SessionLocal()
        try:
            # Verificar si ya existe un usuario con ese username o email
            existing_user = (
                db.query(Usuario)
                .filter(
                    (Usuario.username == admin_data["username"])
                    | (Usuario.email == admin_data["email"])
                )
                .first()
            )

            if existing_user:
                print(f"WARNING: Ya existe un usuario con username '{admin_data['username']}' o email '{admin_data['email']}'")
                print("No se creo el usuario administrador.")
            else:
                # Crear usuario
                admin_user = Usuario(
                    username=admin_data["username"],
                    email=admin_data["email"],
                    hashed_password=get_password_hash(admin_data["password"]),
                    is_active=True,
                    is_superuser=True,
                )
                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)

                print(f"[OK] Usuario administrador creado:")
                print(f"  Username: {admin_user.username}")
                print(f"  Email: {admin_user.email}")
                print(f"  ID: {admin_user.id}")
        finally:
            db.close()

    print()
    print("=" * 60)
    print("[OK] Inicializacion completada exitosamente")
    print("=" * 60)


def main() -> None:
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(
        description="Inicializa la base de datos del Sistema PJN v6"
    )

    parser.add_argument(
        "--admin-username",
        type=str,
        help="Nombre de usuario del administrador",
    )
    parser.add_argument(
        "--admin-email",
        type=str,
        help="Email del administrador",
    )
    parser.add_argument(
        "--admin-password",
        type=str,
        help="Contraseña del administrador",
    )

    args = parser.parse_args()

    # Verificar si se proporcionaron todos los datos del admin
    create_admin = False
    admin_data = None

    if args.admin_username or args.admin_email or args.admin_password:
        if not (args.admin_username and args.admin_email and args.admin_password):
            print("ERROR: Debe proporcionar --admin-username, --admin-email y --admin-password juntos")
            sys.exit(1)

        create_admin = True
        admin_data = {
            "username": args.admin_username,
            "email": args.admin_email,
            "password": args.admin_password,
        }

    # Ejecutar inicialización
    try:
        # Si se proveen datos de admin, no ser interactivo
        interactive = not create_admin
        init_db(create_admin=create_admin, admin_data=admin_data, interactive=interactive)
    except Exception as e:
        print(f"[ERROR] Error durante la inicializacion: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
