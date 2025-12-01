"""
Gestor de certificados SSL para MCP SSE Server.

Proporciona:
- Generación de certificados auto-firmados
- Verificación de expiración
- Renovación automática antes del vencimiento
- Soporte para certificados personalizados
"""

import logging
import ipaddress
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class CertificateManager:
    """
    Gestiona certificados SSL para el servidor MCP.

    Por defecto genera certificados auto-firmados persistentes en config/ssl/.
    Soporta certificados personalizados proporcionados por el usuario.

    Uso:
        manager = CertificateManager()

        # Obtener o crear certificados
        cert_path, key_path = manager.get_or_create()

        # Verificar estado
        info = manager.get_info()
        print(f"Expira: {info['expires']}")

        # Forzar renovación
        cert_path, key_path = manager.renew()
    """

    DEFAULT_CERT_DIR = Path("config/ssl")
    CERT_VALIDITY_DAYS = 365
    RENEWAL_THRESHOLD_DAYS = 30

    def __init__(
        self,
        cert_dir: Optional[Path] = None,
        cert_file: str = "cert.pem",
        key_file: str = "key.pem"
    ):
        """
        Inicializa el gestor de certificados.

        Args:
            cert_dir: Directorio donde guardar certificados (default: config/ssl)
            cert_file: Nombre del archivo de certificado
            key_file: Nombre del archivo de clave privada
        """
        self.cert_dir = cert_dir or self.DEFAULT_CERT_DIR
        self.cert_path = self.cert_dir / cert_file
        self.key_path = self.cert_dir / key_file

        # Configuración del certificado
        self.country = "AR"
        self.state = "Buenos Aires"
        self.locality = "CABA"
        self.organization = "Sintaxis MCP"
        self.common_name = "localhost"
        self.alt_names = ["localhost", "*.local"]
        self.alt_ips = ["127.0.0.1"]

    def get_or_create(self) -> Tuple[str, str]:
        """
        Obtiene certificados existentes o crea nuevos si es necesario.

        Crea nuevos certificados si:
        - No existen
        - Están próximos a expirar (< 30 días)
        - Están expirados

        Returns:
            Tupla (ruta_certificado, ruta_clave)
        """
        if self._needs_renewal():
            self._generate()

        return str(self.cert_path), str(self.key_path)

    def renew(self) -> Tuple[str, str]:
        """
        Fuerza la renovación del certificado.

        Returns:
            Tupla (ruta_certificado, ruta_clave)
        """
        logger.info("Forzando renovación de certificado SSL")
        self._generate()
        return str(self.cert_path), str(self.key_path)

    def exists(self) -> bool:
        """Verifica si los certificados existen."""
        return self.cert_path.exists() and self.key_path.exists()

    def get_info(self) -> dict:
        """
        Obtiene información del certificado actual.

        Returns:
            Dict con subject, issuer, expires, days_remaining, needs_renewal
        """
        if not self.exists():
            return {
                "exists": False,
                "path": str(self.cert_path),
                "key_path": str(self.key_path)
            }

        try:
            from cryptography import x509

            with open(self.cert_path, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read())

            now = datetime.now(timezone.utc)
            expires = cert.not_valid_after_utc if hasattr(cert, 'not_valid_after_utc') else cert.not_valid_after.replace(tzinfo=timezone.utc)
            days_remaining = (expires - now).days

            return {
                "exists": True,
                "path": str(self.cert_path),
                "key_path": str(self.key_path),
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "serial_number": cert.serial_number,
                "not_valid_before": cert.not_valid_before_utc.isoformat() if hasattr(cert, 'not_valid_before_utc') else cert.not_valid_before.isoformat(),
                "expires": expires.isoformat(),
                "days_remaining": days_remaining,
                "needs_renewal": days_remaining < self.RENEWAL_THRESHOLD_DAYS,
                "is_expired": days_remaining < 0,
                "validity_days": self.CERT_VALIDITY_DAYS,
                "renewal_threshold_days": self.RENEWAL_THRESHOLD_DAYS
            }

        except ImportError:
            return {
                "exists": True,
                "path": str(self.cert_path),
                "key_path": str(self.key_path),
                "error": "cryptography no instalado, no se puede leer info"
            }
        except Exception as e:
            return {
                "exists": True,
                "path": str(self.cert_path),
                "key_path": str(self.key_path),
                "error": str(e)
            }

    def _needs_renewal(self) -> bool:
        """Verifica si el certificado necesita renovación."""
        if not self.exists():
            logger.info("Certificados no encontrados, se crearán nuevos")
            return True

        info = self.get_info()

        if info.get("error"):
            logger.warning(f"Error leyendo certificado: {info['error']}")
            return True

        if info.get("is_expired"):
            logger.warning("Certificado expirado, se renovará")
            return True

        if info.get("needs_renewal"):
            days = info.get("days_remaining", 0)
            logger.info(f"Certificado próximo a expirar ({days} días), se renovará")
            return True

        return False

    def _generate(self) -> None:
        """Genera nuevo par de certificado/clave."""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.asymmetric import rsa

            logger.info(f"Generando certificado SSL en {self.cert_dir}")

            # Generar clave privada RSA 2048
            key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            # Construir subject/issuer
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, self.country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state),
                x509.NameAttribute(NameOID.LOCALITY_NAME, self.locality),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.organization),
                x509.NameAttribute(NameOID.COMMON_NAME, self.common_name),
            ])

            # Subject Alternative Names
            san_list = [x509.DNSName(name) for name in self.alt_names]
            san_list.extend([
                x509.IPAddress(ipaddress.IPv4Address(ip))
                for ip in self.alt_ips
            ])

            # Construir certificado
            now = datetime.now(timezone.utc)
            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + timedelta(days=self.CERT_VALIDITY_DAYS))
                .add_extension(
                    x509.SubjectAlternativeName(san_list),
                    critical=False,
                )
                .add_extension(
                    x509.BasicConstraints(ca=False, path_length=None),
                    critical=True,
                )
                .sign(key, hashes.SHA256(), default_backend())
            )

            # Crear directorio si no existe
            self.cert_dir.mkdir(parents=True, exist_ok=True)

            # Guardar clave privada
            with open(self.key_path, "wb") as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            # Guardar certificado
            with open(self.cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            # Permisos restrictivos para la clave
            self.key_path.chmod(0o600)
            self.cert_path.chmod(0o644)

            logger.info(f"Certificado SSL generado (válido por {self.CERT_VALIDITY_DAYS} días)")

        except ImportError:
            raise RuntimeError(
                "Para HTTPS necesitas instalar cryptography: pip install cryptography"
            )

    def delete(self) -> bool:
        """
        Elimina los certificados existentes.

        Returns:
            True si se eliminaron, False si no existían
        """
        deleted = False

        if self.cert_path.exists():
            self.cert_path.unlink()
            deleted = True

        if self.key_path.exists():
            self.key_path.unlink()
            deleted = True

        if deleted:
            logger.info("Certificados SSL eliminados")

        return deleted


# Instancia global para uso directo
_manager: Optional[CertificateManager] = None


def get_certificate_manager() -> CertificateManager:
    """Obtiene instancia singleton del gestor de certificados."""
    global _manager
    if _manager is None:
        _manager = CertificateManager()
    return _manager
