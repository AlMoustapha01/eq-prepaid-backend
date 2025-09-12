"""Module de logging amélioré pour l'application."""

import logging
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Literal

from asgi_correlation_id import CorrelationIdFilter

try:
    from core.settings import settings
except ImportError:
    settings = None


class LogLevel(Enum):
    """Niveaux de log supportés."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogLevelColor(Enum):
    """Mapping des niveaux de log vers les codes ANSI pour la colorisation."""

    DEBUG = "\033[94m"  # Bleu
    INFO = "\033[92m"  # Vert
    WARNING = "\033[93m"  # Jaune
    ERROR = "\033[91m"  # Rouge
    CRITICAL = "\033[91m\033[1m"  # Rouge + Gras
    RESET = "\033[0m"  # Reset


class ColoredConsoleFormatter(logging.Formatter):
    """
    Formateur de logging avec colorisation pour la console.

    Ce formateur permet la colorisation de l'en-tête des logs et le formatage
    du contenu des messages, facilitant la distinction des logs selon leur importance.

    Attributes:
        default_fmt: Formateur pour la partie message du log sans couleur.
        header_fmt: Formateur pour l'en-tête du log avec timestamps, nom du logger, etc.

    """

    def __init__(
        self,
        *,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: bool = True,
    ):
        """
        Initialise le formateur avec les options de format.

        Args:
            fmt: Format string pour les logs.
            datefmt: Format string pour les dates.
            style: Style de formatage.
            use_colors: Active/désactive la colorisation.

        """
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.use_colors = use_colors and self._supports_color()

        # Formats de base
        self.default_fmt = logging.Formatter("%(message)s", datefmt=datefmt)
        self.header_fmt = logging.Formatter(
            "%(asctime)s - [%(correlation_id)s] - %(name)s - %(funcName)s - %(levelname)s",
            datefmt=datefmt,
        )

    def _supports_color(self) -> bool:
        """Vérifie si le terminal supporte les couleurs."""
        return (
            hasattr(sys.stdout, "isatty")
            and sys.stdout.isatty()
            and os.getenv("TERM") != "dumb"
            and os.getenv("NO_COLOR") is None
        )

    def format(self, record: logging.LogRecord) -> str:
        """
        Formate l'enregistrement de log avec colorisation.

        Args:
            record: L'enregistrement de log à formater.

        Returns:
            L'enregistrement formaté avec en-tête colorisé.

        """
        header = self.header_fmt.format(record)
        message = self.default_fmt.format(record)

        if self.use_colors and record.levelname in LogLevelColor.__members__:
            color = LogLevelColor[record.levelname].value
            reset = LogLevelColor.RESET.value
            header = f"{color}{header}{reset}"

        return f"{header} - {message}"


class LoggerConfig:
    """Configuration centralisée pour le logging."""

    def __init__(self):
        """Initialise la configuration avec des valeurs par défaut."""
        self.log_level = self._get_log_level()
        self.log_file_path = self._get_log_file_path()
        self.max_file_size = self._get_max_file_size()
        self.backup_count = int(os.getenv("LOG_BACKUP_COUNT", "10"))
        self.retention_days = int(os.getenv("LOG_RETENTION_DAYS", "7"))
        self.use_rotation_by_time = os.getenv("LOG_ROTATE_BY_TIME", "false").lower() == "true"
        self.correlation_id_length = int(os.getenv("CORRELATION_ID_LENGTH", "32"))

    def _get_log_level(self) -> int:
        """Détermine le niveau de log à utiliser."""
        if settings and hasattr(settings, "app") and hasattr(settings.app, "debug"):
            return logging.DEBUG if settings.app.debug else logging.INFO

        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        return getattr(logging, level_str, logging.INFO)

    def _get_log_file_path(self) -> Path:
        """Détermine le chemin du fichier de log."""
        log_file_path_env = os.getenv("APP_LOG_FILE_PATH", "logs/app.log")
        return Path(log_file_path_env).resolve()

    def _get_max_file_size(self) -> int:
        """Calcule la taille maximale du fichier de log."""
        # Taille par défaut : 100MB
        default_size = 100 * 1024 * 1024

        try:
            # 15% de l'espace disque ou 4GB, le plus petit
            disk_usage = shutil.disk_usage(self.log_file_path.parent)
            calculated_size = min(
                0.15 * disk_usage.total,
                4 * 1024 * 1024 * 1024,
            )
            return int(calculated_size)
        except (OSError, AttributeError):
            return default_size


class LoggerManager:
    """Gestionnaire centralisé pour la configuration du logging."""

    def __init__(self, config: LoggerConfig | None = None):
        """
        Initialise le gestionnaire avec la configuration.

        Args:
            config: Configuration du logging. Si None, utilise la configuration par défaut.

        """
        self.config = config or LoggerConfig()
        self._is_configured = False

    def setup_logging(self) -> None:
        """Configure le système de logging de l'application."""
        if self._is_configured:
            logging.getLogger(__name__).debug("Logging already configured, skipping setup")
            return

        try:
            self._setup_log_directory()
            self._configure_root_logger()
            self._suppress_noisy_loggers()
            self._is_configured = True

            logger = logging.getLogger(__name__)
            logger.info("Logging system configured successfully")

        except Exception as e:
            # Fallback vers la configuration basique
            logging.basicConfig(
                level=self.config.log_level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            logging.getLogger(__name__).error("Failed to setup advanced logging: %s", e)

    def _setup_log_directory(self) -> None:
        """Crée le répertoire de logs s'il n'existe pas."""
        try:
            if not self.config.log_file_path.parent.exists():
                self.config.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.config.log_file_path.exists():
                self.config.log_file_path.touch()
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Cannot create log directory: {e}") from e

    def _configure_root_logger(self) -> None:
        """Configure le logger racine avec les handlers appropriés."""
        root_logger = logging.getLogger()

        # Nettoie les handlers existants
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        root_logger.setLevel(self.config.log_level)

        # Ajoute les handlers
        root_logger.addHandler(self._create_console_handler())
        root_logger.addHandler(self._create_file_handler())

    def _create_console_handler(self) -> logging.StreamHandler:
        """Crée le handler pour la sortie console."""
        console_handler = logging.StreamHandler()
        console_formatter = ColoredConsoleFormatter(
            "%(asctime)s - [%(correlation_id)s] - %(name)s - %(funcName)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(
            CorrelationIdFilter(uuid_length=self.config.correlation_id_length)
        )
        return console_handler

    def _create_file_handler(self) -> logging.Handler:
        """Crée le handler pour l'écriture en fichier."""
        if self.config.use_rotation_by_time:
            # Rotation par temps (quotidienne)
            file_handler = TimedRotatingFileHandler(
                str(self.config.log_file_path),
                when="midnight",
                interval=1,
                backupCount=self.config.backup_count,
                encoding="utf-8",
            )
        else:
            # Rotation par taille
            file_handler = RotatingFileHandler(
                str(self.config.log_file_path),
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
                encoding="utf-8",
            )

        file_formatter = logging.Formatter(
            "%(asctime)s - [%(correlation_id)s] - %(name)s - %(funcName)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(CorrelationIdFilter(uuid_length=self.config.correlation_id_length))
        return file_handler

    def _suppress_noisy_loggers(self) -> None:
        """Supprime les logs verbeux de certaines librairies."""
        noisy_loggers = [
            "pytds",
            "urllib3.connectionpool",
            "asyncio",
            "sqlalchemy.engine",
        ]

        for logger_name in noisy_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)


def _validate_log_directory(log_directory: Path, retention_days: int) -> None:
    """Valide les paramètres pour le nettoyage des logs."""
    if retention_days < 0:
        raise ValueError("retention_days must be non-negative")
    if not log_directory.exists():
        raise OSError("Log directory does not exist: %s", log_directory)
    if not log_directory.is_dir():
        raise OSError("Path is not a directory: %s", log_directory)


def _delete_log_file(log_file: Path, threshold: datetime) -> tuple[bool, str | None]:
    """Supprime un fichier de log si plus ancien que le seuil."""
    try:
        file_time = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
        if file_time < threshold:
            log_file.unlink()
            return True, None
    except (OSError, PermissionError) as e:
        return False, str(e)
    return False, None


def cleanup_old_logs(log_directory: Path, retention_days: int = 7) -> int:
    """
    Supprime les fichiers de log plus anciens que le nombre de jours spécifié.
    """
    logger = logging.getLogger(__name__)
    _validate_log_directory(log_directory, retention_days)

    threshold = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted_count = 0
    errors: list[str] = []

    for log_file in log_directory.glob("*.log*"):
        deleted, err = _delete_log_file(log_file, threshold)
        if deleted:
            deleted_count += 1
            logger.debug("Deleted old log file: %s", log_file)
        elif err:
            errors.append(f"Failed to delete {log_file}: {err}")
            logger.warning("Failed to delete %s: %s", log_file, err)

    if errors:
        logger.warning("Log cleanup completed with %d errors", len(errors))
    else:
        logger.info("Log cleanup completed successfully. Deleted %d files", deleted_count)

    return deleted_count


def cleanup_temp_log_dir(temp_dir: Path) -> None:
    """
    Supprime un répertoire temporaire utilisé pour les fichiers de log.

    Args:
        temp_dir: Le répertoire temporaire à supprimer.

    Raises:
        OSError: Si la suppression échoue.

    """
    logger = logging.getLogger(__name__)

    if not temp_dir.exists():
        logger.debug("Temporary directory does not exist: %s", temp_dir)
        return

    try:
        temp_dir.rmdir()  # Ne réussit que si le répertoire est vide
        logger.info("Removed temporary log directory: %s", temp_dir)
    except OSError as e:
        logger.error("Failed to remove temporary directory %s: %s", temp_dir, e)
        raise


# Instance globale du gestionnaire de logging
_logger_manager: LoggerManager = LoggerManager()


def setup_logging(config: LoggerConfig | None = None) -> None:
    """
    Point d'entrée principal pour configurer le logging.

    Args:
        config: Configuration personnalisée. Si None, utilise la configuration par défaut.

    """
    if config:
        _logger_manager = LoggerManager(config)
    _logger_manager.setup_logging()


def get_logger(name: str) -> logging.Logger:
    """
    Obtient un logger configuré pour le module spécifié.

    Args:
        name: Nom du module (généralement __name__).

    Returns:
        Logger configuré.

    """
    return logging.getLogger(name)


if __name__ == "__main__":
    # Test de la configuration
    setup_logging()

    logger = get_logger(__name__)
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    # Test du nettoyage des logs
    log_dir = Path("logs")
    if log_dir.exists():
        deleted_count = cleanup_old_logs(log_dir, retention_days=7)
        logger.info("Cleanup completed, deleted %d files", deleted_count)
