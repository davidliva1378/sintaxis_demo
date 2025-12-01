#!/usr/bin/env python3
"""
CLI para gestión de tokens MCP.

Permite generar, listar, revocar y eliminar tokens
para acceso remoto al servidor MCP SSE.

Uso:
    python mcp_token_cli.py generate --name "claude-desktop"
    python mcp_token_cli.py generate --name "chatgpt" --expires 30
    python mcp_token_cli.py list
    python mcp_token_cli.py info <token_id>
    python mcp_token_cli.py revoke <token_id>
    python mcp_token_cli.py delete <token_id>
    python mcp_token_cli.py cleanup
    python mcp_token_cli.py stats
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sintaxis_mcp.auth import TokenManager


def format_date(iso_date: str | None) -> str:
    """Formatea fecha ISO a formato legible."""
    if not iso_date:
        return "Nunca"
    try:
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_date


def cmd_generate(args, manager: TokenManager):
    """Genera un nuevo token."""
    print(f"\n🔑 Generando token para: {args.name}")

    expires = args.expires if args.expires else None
    permissions = args.permissions.split(",") if args.permissions else None

    token_plaintext, token = manager.generate_token(
        name=args.name,
        expires_in_days=expires,
        permissions=permissions
    )

    print("\n" + "=" * 60)
    print("✅ TOKEN GENERADO EXITOSAMENTE")
    print("=" * 60)
    print(f"\n📋 Token ID: {token.token_id}")
    print(f"📛 Nombre: {token.name}")
    print(f"📅 Creado: {format_date(token.created_at)}")
    print(f"⏰ Expira: {format_date(token.expires_at)}")
    print(f"🔐 Permisos: {', '.join(token.permissions)}")
    print("\n" + "-" * 60)
    print("⚠️  IMPORTANTE: Guarda este token de forma segura.")
    print("   No podrás verlo de nuevo.")
    print("-" * 60)
    print(f"\n🔑 TOKEN: {token_plaintext}\n")

    print("\n📝 Uso en Claude Code/Desktop (claude_desktop_config.json):")
    print("""
{
  "mcpServers": {
    "sintaxis-actuaciones": {
      "url": "http://localhost:8001/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer """ + token_plaintext + """"
      }
    }
  }
}
""")


def cmd_list(args, manager: TokenManager):
    """Lista todos los tokens."""
    tokens = manager.list_tokens(include_inactive=args.all)

    if not tokens:
        print("\n📭 No hay tokens registrados")
        return

    print(f"\n📋 Tokens ({len(tokens)}):")
    print("-" * 80)
    print(f"{'ID':<18} {'Nombre':<20} {'Estado':<10} {'Último uso':<18} {'Expira':<18}")
    print("-" * 80)

    for token in tokens:
        status = "✅ Activo" if token.is_valid() else "❌ Inactivo"
        if token.is_expired():
            status = "⏰ Expirado"

        print(
            f"{token.token_id:<18} "
            f"{token.name:<20} "
            f"{status:<10} "
            f"{format_date(token.last_used):<18} "
            f"{format_date(token.expires_at):<18}"
        )

    print("-" * 80)


def cmd_info(args, manager: TokenManager):
    """Muestra información detallada de un token."""
    token = manager.get_token_info(args.token_id)

    if not token:
        print(f"\n❌ Token no encontrado: {args.token_id}")
        return

    print(f"\n📋 Información del Token")
    print("=" * 40)
    print(f"ID:          {token.token_id}")
    print(f"Nombre:      {token.name}")
    print(f"Estado:      {'Activo' if token.is_active else 'Revocado'}")
    print(f"Expirado:    {'Sí' if token.is_expired() else 'No'}")
    print(f"Válido:      {'Sí' if token.is_valid() else 'No'}")
    print(f"Creado:      {format_date(token.created_at)}")
    print(f"Expira:      {format_date(token.expires_at)}")
    print(f"Último uso:  {format_date(token.last_used)}")
    print(f"Permisos:    {', '.join(token.permissions)}")
    print("=" * 40)


def cmd_revoke(args, manager: TokenManager):
    """Revoca un token."""
    if manager.revoke_token(args.token_id):
        print(f"\n✅ Token revocado: {args.token_id}")
    else:
        print(f"\n❌ Token no encontrado: {args.token_id}")


def cmd_delete(args, manager: TokenManager):
    """Elimina un token permanentemente."""
    if args.force:
        confirmed = True
    else:
        response = input(f"¿Eliminar token {args.token_id} permanentemente? [y/N]: ")
        confirmed = response.lower() in ("y", "yes", "s", "si")

    if confirmed:
        if manager.delete_token(args.token_id):
            print(f"\n✅ Token eliminado: {args.token_id}")
        else:
            print(f"\n❌ Token no encontrado: {args.token_id}")
    else:
        print("\n❌ Operación cancelada")


def cmd_cleanup(args, manager: TokenManager):
    """Elimina tokens expirados."""
    count = manager.cleanup_expired()
    print(f"\n🧹 Eliminados {count} tokens expirados")


def cmd_stats(args, manager: TokenManager):
    """Muestra estadísticas de tokens."""
    stats = manager.get_stats()

    print("\n📊 Estadísticas de Tokens")
    print("=" * 40)
    print(f"Total:       {stats['total']}")
    print(f"Activos:     {stats['active']}")
    print(f"Inactivos:   {stats['inactive']}")
    print(f"Expirados:   {stats['expired']}")
    print(f"Almacenado:  {stats['storage_path']}")
    print("=" * 40)


def main():
    parser = argparse.ArgumentParser(
        description="CLI para gestión de tokens MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--storage",
        help="Ruta al archivo de tokens (default: ~/.sintaxis_mcp/tokens.json)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generar nuevo token")
    gen_parser.add_argument("--name", "-n", required=True, help="Nombre del token")
    gen_parser.add_argument("--expires", "-e", type=int, help="Días hasta expiración")
    gen_parser.add_argument("--permissions", "-p", help="Permisos (separados por coma)")

    # list
    list_parser = subparsers.add_parser("list", help="Listar tokens")
    list_parser.add_argument("--all", "-a", action="store_true", help="Incluir inactivos")

    # info
    info_parser = subparsers.add_parser("info", help="Información de un token")
    info_parser.add_argument("token_id", help="ID del token")

    # revoke
    revoke_parser = subparsers.add_parser("revoke", help="Revocar un token")
    revoke_parser.add_argument("token_id", help="ID del token")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Eliminar un token")
    delete_parser.add_argument("token_id", help="ID del token")
    delete_parser.add_argument("--force", "-f", action="store_true", help="Sin confirmación")

    # cleanup
    subparsers.add_parser("cleanup", help="Eliminar tokens expirados")

    # stats
    subparsers.add_parser("stats", help="Mostrar estadísticas")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Inicializar manager
    storage_path = Path(args.storage) if args.storage else None
    manager = TokenManager(storage_path)

    # Ejecutar comando
    commands = {
        "generate": cmd_generate,
        "list": cmd_list,
        "info": cmd_info,
        "revoke": cmd_revoke,
        "delete": cmd_delete,
        "cleanup": cmd_cleanup,
        "stats": cmd_stats,
    }

    if args.command in commands:
        commands[args.command](args, manager)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
