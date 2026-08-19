"""
Formatage sécurisé d'une clé USB infectée.

Ce module ne formate JAMAIS sans confirmation explicite de l'appelant
(le paramètre confirm=True doit être passé volontairement par l'UI, après
validation par l'utilisateur sur l'écran "infected"). Il revérifie aussi
que le périphérique est bien sur bus USB avant toute action destructive,
pour éviter qu'une erreur de device_node ne formate un disque interne.
"""

import logging
import subprocess

import pyudev

import config

logger = logging.getLogger("formatter")


class FormatError(Exception):
    """Levée quand le formatage ne peut pas être effectué en toute sécurité."""


def _assert_is_usb_device(device_node):
    """Sécurité : refuse de formater un device qui n'est pas identifié comme USB."""
    context = pyudev.Context()
    try:
        device = pyudev.Devices.from_device_file(context, device_node)
    except pyudev.DeviceNotFoundByFileError:
        raise FormatError(f"Périphérique introuvable : {device_node}")

    if device.get("ID_BUS") != config.REQUIRED_ID_BUS:
        raise FormatError(
            f"Refus de formater {device_node} : ce n'est pas un périphérique USB "
            f"(ID_BUS={device.get('ID_BUS')!r})"
        )


def _is_mounted(device_node):
    result = subprocess.run(["findmnt", "-n", device_node], capture_output=True, text=True)
    return result.returncode == 0


def _unmount(device_node):
    result = subprocess.run(["umount", device_node], capture_output=True, text=True)
    if result.returncode != 0:
        raise FormatError(f"Échec du démontage de {device_node} : {result.stderr.strip()}")
    logger.info("Clé démontée avant formatage : %s", device_node)


def format_device(device_node, confirm=False):
    """
    Formate la clé USB en FAT32 (vfat).

    confirm doit être explicitement True : ce paramètre matérialise la
    confirmation de l'utilisateur obtenue par l'UI (pas de formatage
    "silencieux" possible depuis ce module).
    """
    if not confirm:
        raise FormatError("Formatage refusé : confirmation utilisateur manquante")

    _assert_is_usb_device(device_node)

    if _is_mounted(device_node):
        _unmount(device_node)

    logger.info("Formatage de %s en cours...", device_node)
    result = subprocess.run(
        ["mkfs.vfat", "-F", "32", device_node],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        error_message = result.stderr.strip() or f"mkfs.vfat a retourné le code {result.returncode}"
        logger.error("Échec du formatage de %s : %s", device_node, error_message)
        raise FormatError(error_message)

    logger.info("Formatage réussi : %s", device_node)


if __name__ == "__main__":
    # Test manuel : à exécuter sur le Raspberry Pi avec une clé branchée.
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if len(sys.argv) != 2:
        print("Usage: sudo python3 formatter.py /dev/sdX1")
        sys.exit(1)

    device = sys.argv[1]
    answer = input(f"Confirmer le formatage DÉFINITIF de {device} ? (oui/non) ")
    format_device(device, confirm=(answer.strip().lower() == "oui"))
