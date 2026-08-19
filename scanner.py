"""
Scan antivirus des clés USB via ClamAV.

Ce module monte le périphérique détecté par usb_monitor.py en lecture seule
et avec des options restrictives (noexec,nosuid,nodev), lance clamscan sur
le point de montage, puis démonte systématiquement la clé (y compris en cas
d'erreur), avant de retourner un résultat exploitable par l'UI.
"""

import logging
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum

import config

logger = logging.getLogger("scanner")


class ScanStatus(Enum):
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"


@dataclass
class ScanResult:
    status: ScanStatus
    infected_files: list = field(default_factory=list)
    error_message: str = None


class MountError(Exception):
    """Levée quand le montage ou le démontage de la clé échoue."""


def _mount_point_for(device_node):
    # ex: /dev/sda1 -> /media/borne/sda1
    name = device_node.rstrip("/").rsplit("/", 1)[-1]
    return config.MOUNT_BASE_DIR / name


def _mount(device_node, mount_point):
    mount_point.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["mount", "-o", config.MOUNT_OPTIONS, device_node, str(mount_point)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise MountError(f"Échec du montage de {device_node} : {result.stderr.strip()}")
    logger.info("Clé montée en lecture seule : %s -> %s", device_node, mount_point)


def _unmount(mount_point):
    result = subprocess.run(
        ["umount", str(mount_point)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        logger.warning("Échec du démontage de %s : %s", mount_point, result.stderr.strip())
    else:
        logger.info("Clé démontée : %s", mount_point)


_FOUND_LINE_RE = re.compile(r"^(?P<path>.+): (?P<signature>.+) FOUND$")


def _parse_clamscan_output(stdout):
    infected_files = []
    for line in stdout.splitlines():
        match = _FOUND_LINE_RE.match(line)
        if match:
            infected_files.append({
                "path": match.group("path"),
                "signature": match.group("signature"),
            })
    return infected_files


def _run_clamscan(mount_point):
    """
    Lance clamscan sur le point de montage.
    Codes retour clamscan : 0 = sain, 1 = virus détecté, 2 = erreur.
    """
    try:
        result = subprocess.run(
            [config.CLAMSCAN_BIN, "--recursive", "--infected", "--no-summary", str(mount_point)],
            capture_output=True, text=True,
            timeout=config.SCAN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise MountError(f"Le scan a dépassé le délai de {config.SCAN_TIMEOUT_SECONDS}s")
    except FileNotFoundError:
        raise MountError(f"Binaire clamscan introuvable ({config.CLAMSCAN_BIN})")

    return result


def scan_device(device_info):
    """
    Monte la clé USB décrite par device_info (UsbDeviceInfo), lance clamscan,
    démonte la clé, et retourne un ScanResult.
    """
    mount_point = _mount_point_for(device_info.device_node)

    try:
        _mount(device_info.device_node, mount_point)
    except MountError as exc:
        logger.error("Erreur de montage : %s", exc)
        return ScanResult(status=ScanStatus.ERROR, error_message=str(exc))

    try:
        result = _run_clamscan(mount_point)
    except MountError as exc:
        logger.error("Erreur de scan : %s", exc)
        return ScanResult(status=ScanStatus.ERROR, error_message=str(exc))
    finally:
        _unmount(mount_point)

    if result.returncode == 0:
        logger.info("Scan terminé, clé saine : %s", device_info.device_node)
        return ScanResult(status=ScanStatus.CLEAN)
    elif result.returncode == 1:
        infected_files = _parse_clamscan_output(result.stdout)
        logger.warning("Clé infectée détectée : %s (%d fichier(s))",
                        device_info.device_node, len(infected_files))
        return ScanResult(status=ScanStatus.INFECTED, infected_files=infected_files)
    else:
        error_message = result.stderr.strip() or f"clamscan a retourné le code {result.returncode}"
        logger.error("Erreur clamscan : %s", error_message)
        return ScanResult(status=ScanStatus.ERROR, error_message=error_message)


if __name__ == "__main__":
    # Test manuel : à exécuter sur le Raspberry Pi avec une clé branchée.
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if len(sys.argv) != 2:
        print("Usage: sudo python3 scanner.py /dev/sdX1")
        sys.exit(1)

    class _FakeDeviceInfo:
        device_node = sys.argv[1]

    scan_result = scan_device(_FakeDeviceInfo())
    print(scan_result)
