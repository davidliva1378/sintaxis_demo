"""CLI principal del Sistema PJN v6.

Interfaz de línea de comandos para interactuar con el sistema.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from infrastructure.config import get_settings
from infrastructure.di_container import get_container

console = Console()


def setup_logging() -> None:
    """Configura el logging del sistema."""
    import logging

    settings = get_settings()

    # Configurar formato
    logging.basicConfig(
        level=getattr(logging, settings.logging.level),
        format=settings.logging.format,
        datefmt=settings.logging.date_format,
    )

    # Logging a archivo si está habilitado
    if settings.logging.log_to_file:
        from logging.handlers import RotatingFileHandler

        log_file = settings.storage.base_path / settings.logging.log_file
        log_file.parent.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            log_file,
            maxBytes=settings.logging.max_bytes,
            backupCount=settings.logging.backup_count,
        )
        handler.setFormatter(
            logging.Formatter(
                settings.logging.format,
                datefmt=settings.logging.date_format,
            )
        )
        logging.getLogger().addHandler(handler)


@click.group()
@click.version_option(version="6.0.0", prog_name="Sistema PJN")
def cli():
    """Sistema de extracción y monitoreo del Portal Judicial Nacional (Argentina) - v6.

    Este sistema permite:

    \b
    1. Extraer lista completa de expedientes → JSON "base"
    2. Filtrar expedientes seleccionados → JSON "sistema"
    3. Crear workspaces para expedientes
    4. Monitorear cambios y mantener actualizado

    Arquitectura: Clean Architecture con Domain-Driven Design
    """
    setup_logging()


@cli.command()
@click.option(
    "--usuario",
    "-u",
    help="Usuario del PJN (default: variable de entorno PJN_USER)",
)
@click.option(
    "--password",
    "-p",
    help="Contraseña del PJN (default: variable de entorno PJN_PASSWORD)",
)
@click.option(
    "--headless/--no-headless",
    default=True,
    help="Ejecutar navegador sin interfaz gráfica",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Archivo JSON donde guardar los expedientes",
)
def extraer(
    usuario: str | None,
    password: str | None,
    headless: bool,
    output: Path | None,
):
    """Extrae la lista completa de expedientes del PJN.

    Este comando ejecuta el Paso 1 del workflow:
    Scraping del PJN → JSON "base" con todos los expedientes.

    Ejemplo:
        pjn extraer --output data/expedientes_base.json
    """
    from application.dtos import ExtraerExpedientesCommand

    console.print(
        Panel.fit(
            "[bold blue]Paso 1: Extracción de Expedientes[/bold blue]\n"
            "Extrayendo lista completa del Portal Judicial Nacional...",
            border_style="blue",
        )
    )

    # Determinar archivo de salida
    if output is None:
        settings = get_settings()
        output = settings.storage.base_path / settings.storage.json_base_file

    # Crear comando
    command = ExtraerExpedientesCommand(
        usuario=usuario,
        contrasena=password,
        headless=headless,
        guardar_en=output,
    )

    # Ejecutar use case
    container = get_container()
    use_case = container.extraer_expedientes_use_case()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Extrayendo expedientes...", total=None)

        try:
            result = asyncio.run(use_case.execute(command))
            progress.update(task, completed=True)

            if result.success:
                response = result.value
                console.print(
                    f"\n[bold green]✓ Extracción exitosa![/bold green]\n"
                    f"  • Expedientes extraídos: {response.total}\n"
                    f"  • Guardado en: {response.archivo_guardado}"
                )
            else:
                console.print(
                    f"\n[bold red]✗ Error en extracción:[/bold red]\n"
                    f"  {result.error}",
                    style="red",
                )
                sys.exit(1)

        except NotImplementedError:
            progress.update(task, completed=True)
            console.print(
                "\n[bold yellow]⚠ Scraping no implementado aún[/bold yellow]\n"
                "  El adapter de scraping requiere migración completa de Sistema_v5.\n"
                "  Usa archivos JSON existentes o implementa el scraper.\n"
                "  Ver: infrastructure/adapters/scraping/playwright_scraper_adapter.py",
                style="yellow",
            )
            sys.exit(1)
        except Exception as e:
            progress.update(task, completed=True)
            console.print(
                f"\n[bold red]✗ Error inesperado:[/bold red]\n  {e}",
                style="red",
            )
            sys.exit(1)


@cli.command()
@click.option(
    "--origen",
    "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Archivo JSON 'base' con todos los expedientes",
)
@click.option(
    "--destino",
    "-o",
    type=click.Path(path_type=Path),
    help="Archivo JSON 'sistema' donde guardar expedientes seleccionados",
)
@click.option(
    "--numeros",
    "-n",
    multiple=True,
    help="Números de expedientes a seleccionar (puede repetirse)",
)
@click.option(
    "--activos/--no-activos",
    default=False,
    help="Incluir automáticamente expedientes activos",
)
@click.option(
    "--dias",
    "-d",
    type=int,
    default=30,
    help="Días de actividad para considerar expediente activo",
)
def filtrar(
    origen: Path,
    destino: Path | None,
    numeros: tuple[str, ...],
    activos: bool,
    dias: int,
):
    """Filtra expedientes según selección del usuario.

    Este comando ejecuta el Paso 2 del workflow:
    JSON "base" → Filtrado → JSON "sistema" con expedientes seleccionados.

    Ejemplo:
        pjn filtrar -i base.json -o sistema.json -n "FPA-123-2024" -n "FPA-456-2024"
        pjn filtrar -i base.json --activos --dias 30
    """
    from application.dtos import FiltrarExpedientesCommand

    console.print(
        Panel.fit(
            "[bold green]Paso 2: Filtrado de Expedientes[/bold green]\n"
            "Seleccionando expedientes para el sistema...",
            border_style="green",
        )
    )

    # Determinar archivo de destino
    if destino is None:
        settings = get_settings()
        destino = settings.storage.base_path / settings.storage.json_sistema_file

    # Validar que hay algo para filtrar
    if not numeros and not activos:
        console.print(
            "[bold red]Error:[/bold red] Debe especificar números de expedientes "
            "(-n) o --activos",
            style="red",
        )
        sys.exit(1)

    # Crear comando
    command = FiltrarExpedientesCommand(
        numeros_seleccionados=list(numeros),
        origen=origen,
        destino=destino,
        incluir_activos=activos,
        dias_actividad=dias,
    )

    # Ejecutar use case
    container = get_container()
    use_case = container.filtrar_expedientes_use_case()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Filtrando expedientes...", total=None)

        try:
            result = asyncio.run(use_case.execute(command))
            progress.update(task, completed=True)

            if result.success:
                response = result.value
                console.print(
                    f"\n[bold green]✓ Filtrado exitoso![/bold green]\n"
                    f"  • Expedientes seleccionados: {response.total}\n"
                    f"  • Guardado en: {response.archivo_guardado}"
                )
            else:
                console.print(
                    f"\n[bold red]✗ Error en filtrado:[/bold red]\n"
                    f"  {result.error}",
                    style="red",
                )
                sys.exit(1)

        except Exception as e:
            progress.update(task, completed=True)
            console.print(
                f"\n[bold red]✗ Error inesperado:[/bold red]\n  {e}",
                style="red",
            )
            sys.exit(1)


@cli.command()
@click.option(
    "--sistema",
    "-s",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Archivo JSON 'sistema' con expedientes seleccionados",
)
@click.option(
    "--workspaces-dir",
    "-w",
    type=click.Path(path_type=Path),
    help="Directorio base donde crear los workspaces",
)
@click.option(
    "--extraer-actuaciones/--no-extraer-actuaciones",
    default=True,
    help="Extraer actuaciones automáticamente",
)
@click.option(
    "--descargar-archivos/--no-descargar-archivos",
    default=False,
    help="Descargar archivos adjuntos automáticamente",
)
def workspace(
    sistema: Path,
    workspaces_dir: Path | None,
    extraer_actuaciones: bool,
    descargar_archivos: bool,
):
    """Crea workspaces para expedientes seleccionados.

    Este comando ejecuta el Paso 3 del workflow:
    JSON "sistema" → Crear directorios → Workspaces con actuaciones.

    Ejemplo:
        pjn workspace -s sistema.json --extraer-actuaciones
    """
    from application.dtos import CrearWorkspacesCommand

    console.print(
        Panel.fit(
            "[bold cyan]Paso 3: Creación de Workspaces[/bold cyan]\n"
            "Creando estructura de directorios para expedientes...",
            border_style="cyan",
        )
    )

    # Determinar directorio de workspaces
    if workspaces_dir is None:
        settings = get_settings()
        workspaces_dir = settings.storage.base_path / settings.storage.workspaces_dir

    # Crear comando
    command = CrearWorkspacesCommand(
        json_sistema=sistema,
        base_path=workspaces_dir,
        extraer_actuaciones=extraer_actuaciones,
        descargar_archivos=descargar_archivos,
    )

    # Ejecutar use case
    container = get_container()
    use_case = container.crear_workspaces_use_case()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creando workspaces...", total=None)

        try:
            result = asyncio.run(use_case.execute(command))
            progress.update(task, completed=True)

            if result.success:
                response = result.value
                console.print(
                    f"\n[bold green]✓ Workspaces creados![/bold green]\n"
                    f"  • Exitosos: {response.total_creados}\n"
                    f"  • Fallidos: {response.total_fallidos}"
                )

                if response.errores:
                    console.print("\n[bold yellow]Errores:[/bold yellow]")
                    for numero, error in response.errores:
                        console.print(f"  • {numero}: {error}", style="yellow")
            else:
                console.print(
                    f"\n[bold red]✗ Error creando workspaces:[/bold red]\n"
                    f"  {result.error}",
                    style="red",
                )
                sys.exit(1)

        except NotImplementedError:
            progress.update(task, completed=True)
            console.print(
                "\n[bold yellow]⚠ Extracción de actuaciones no disponible[/bold yellow]\n"
                "  Workspaces creados pero sin actuaciones.\n"
                "  El scraper requiere implementación completa.",
                style="yellow",
            )
        except Exception as e:
            progress.update(task, completed=True)
            console.print(
                f"\n[bold red]✗ Error inesperado:[/bold red]\n  {e}",
                style="red",
            )
            sys.exit(1)


@cli.command()
@click.option(
    "--sistema",
    "-s",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Archivo JSON 'sistema' con expedientes a monitorear",
)
@click.option(
    "--workspaces-dir",
    "-w",
    type=click.Path(path_type=Path),
    help="Directorio base de workspaces",
)
@click.option(
    "--intervalo",
    "-i",
    type=int,
    default=0,
    help="Intervalo en segundos entre verificaciones (0 = una vez)",
)
@click.option(
    "--notificar/--no-notificar",
    default=True,
    help="Enviar notificaciones de cambios",
)
def monitorear(
    sistema: Path,
    workspaces_dir: Path | None,
    intervalo: int,
    notificar: bool,
):
    """Monitorea expedientes y mantiene el sistema actualizado.

    Este comando ejecuta el Paso 4 del workflow:
    Verificar cambios en el PJN → Actualizar workspaces → Notificar.

    Ejemplo:
        pjn monitorear -s sistema.json --intervalo 3600
    """
    from application.dtos import MonitorearExpedientesCommand

    console.print(
        Panel.fit(
            "[bold magenta]Paso 4: Monitoreo de Expedientes[/bold magenta]\n"
            "Monitoreando cambios en el Portal Judicial Nacional...",
            border_style="magenta",
        )
    )

    # Determinar directorio de workspaces
    if workspaces_dir is None:
        settings = get_settings()
        workspaces_dir = settings.storage.base_path / settings.storage.workspaces_dir

    # Crear comando
    command = MonitorearExpedientesCommand(
        json_sistema=sistema,
        base_path=workspaces_dir,
        intervalo_segundos=intervalo,
        notificar_cambios=notificar,
        descargar_nuevos_archivos=True,
    )

    # Ejecutar use case
    container = get_container()
    use_case = container.monitorear_expedientes_use_case()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Monitoreando expedientes...", total=None)

        try:
            result = asyncio.run(use_case.execute(command))
            progress.update(task, completed=True)

            if result.success:
                response = result.value
                console.print(
                    f"\n[bold green]✓ Monitoreo completado![/bold green]\n"
                    f"  • Expedientes verificados: {response.expedientes_verificados}\n"
                    f"  • Cambios detectados: {response.total_cambios}\n"
                    f"  • Notificaciones enviadas: {response.notificaciones_enviadas}"
                )

                if response.cambios_detectados:
                    console.print("\n[bold cyan]Cambios detectados:[/bold cyan]")
                    for cambio in response.cambios_detectados:
                        console.print(
                            f"  • {cambio.numero_expediente}: {cambio.descripcion}",
                            style="cyan",
                        )
            else:
                console.print(
                    f"\n[bold red]✗ Error en monitoreo:[/bold red]\n"
                    f"  {result.error}",
                    style="red",
                )
                sys.exit(1)

        except NotImplementedError:
            progress.update(task, completed=True)
            console.print(
                "\n[bold yellow]⚠ Monitoreo no disponible[/bold yellow]\n"
                "  El scraper requiere implementación completa.",
                style="yellow",
            )
        except Exception as e:
            progress.update(task, completed=True)
            console.print(
                f"\n[bold red]✗ Error inesperado:[/bold red]\n  {e}",
                style="red",
            )
            sys.exit(1)


@cli.command()
def info():
    """Muestra información del sistema."""
    from rich.table import Table

    settings = get_settings()

    # Crear tabla de configuración
    table = Table(title="Configuración del Sistema", show_header=True)
    table.add_column("Parámetro", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("Versión", "6.0.0")
    table.add_row("Entorno", settings.environment)
    table.add_row("Directorio base", str(settings.storage.base_path))
    table.add_row("JSON base", settings.storage.json_base_file)
    table.add_row("JSON sistema", settings.storage.json_sistema_file)
    table.add_row("Workspaces", settings.storage.workspaces_dir)
    table.add_row("Login URL", settings.auth.login_url)
    table.add_row("Nivel de log", settings.logging.level)

    console.print(table)

    # Información de arquitectura
    console.print(
        "\n[bold]Arquitectura:[/bold] Clean Architecture + DDD\n"
        "  • Domain Layer: 5 entidades + 4 utils\n"
        "  • Application Layer: 4 use cases + 7 ports\n"
        "  • Infrastructure Layer: Adapters + DI Container\n"
        "  • Presentation Layer: CLI + API REST + MCP"
    )


def main():
    """Punto de entrada principal."""
    cli()


if __name__ == "__main__":
    main()
