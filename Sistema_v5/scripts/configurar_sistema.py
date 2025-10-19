"""Script legado - redirige al nuevo configurador CLI."""

from __future__ import annotations

from textwrap import dedent


def main() -> None:
    """Informa la nueva ruta del configurador y finaliza."""

    mensaje = dedent(
        """
        El configurador se centralizó en el paquete Sistema_v5/configuracion/.

        Opciones disponibles:

            python -m Sistema_v5.cli.configuracion wizard   # Asistente por terminal
            python -m Sistema_v5.cli.configuracion show     # Ver configuración
            python -m Sistema_v5.cli.configuracion set ...  # Actualizar campos
            python -m Sistema_v5.configuracion.gui.config_form  # Interfaz gráfica

        Consulta --help en la CLI para ver todos los subcomandos.
        """
    ).strip()

    print(mensaje)


if __name__ == "__main__":
    main()
