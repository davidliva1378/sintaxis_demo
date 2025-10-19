"""Script legado - redirige al nuevo configurador CLI."""

from __future__ import annotations

from textwrap import dedent


def main() -> None:
    """Informa la nueva ruta del configurador y finaliza."""

    mensaje = dedent(
        """
        El configurador gráfico ha sido reemplazado por el asistente CLI.

        Ejecuta la nueva herramienta con:

            python -m Sistema_v5.cli.configuracion wizard

        También puedes mostrar la configuración actual o actualizar campos puntuales:

            python -m Sistema_v5.cli.configuracion show
            python -m Sistema_v5.cli.configuracion set campo=valor

        Consulta --help para más opciones.
        """
    ).strip()

    print(mensaje)


if __name__ == "__main__":
    main()
