"""Configuration centralisée de la borne de décontamination USB."""

from pathlib import Path

# Répertoire où les clés USB seront montées (un sous-dossier par device, ex: /media/borne/sdb1)
MOUNT_BASE_DIR = Path("/media/borne")

# Options de montage en lecture seule, sécurisées (pas d'exécution, pas de setuid, pas de devices)
MOUNT_OPTIONS = "ro,noexec,nosuid,nodev"

# Fichiers de log
LOG_DIR = Path("/var/log/borne-usb")
USB_LOG_FILE = LOG_DIR / "usb_monitor.log"
SCAN_LOG_FILE = LOG_DIR / "scan.log"

# Uniquement les périphériques de bus USB, on ignore le reste (disques internes, etc.)
REQUIRED_ID_BUS = "usb"

# Scan antivirus (ClamAV)
CLAMSCAN_BIN = "clamscan"
SCAN_TIMEOUT_SECONDS = 600  # sécurité anti-blocage sur une clé volumineuse/corrompue
