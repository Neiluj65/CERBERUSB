"""
Détection des branchements/débranchements de clés USB via pyudev.

Ce module ne fait QUE de la détection : il ne monte pas les périphériques,
il ne lance pas de scan. Il notifie l'appelant (main.py) via des callbacks
quand une clé USB apparaît ou disparaît, avec les informations nécessaires
(device_node, système de fichiers, label, uuid...) pour que scanner.py
puisse ensuite la monter et l'analyser.

On ne retient que les partitions dont le bus est USB (ID_BUS=usb), pour
ignorer les disques internes et tout ce qui n'est pas une clé USB branchée
à chaud.
"""

import logging
from pathlib import Path

import pyudev

import config

logger = logging.getLogger("usb_monitor")


def _setup_logging():
    """Configure le logger : fichier si possible, sinon console uniquement."""
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(config.USB_LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as exc:
        logger.warning("Impossible d'écrire les logs dans %s (%s) — logs console uniquement",
                        config.LOG_DIR, exc)


_setup_logging()


class UsbDeviceInfo:
    """Informations extraites d'un périphérique USB détecté par udev."""

    def __init__(self, device_node, fs_type, fs_label, fs_uuid, serial):
        self.device_node = device_node    # ex: /dev/sda1
        self.fs_type = fs_type            # ex: vfat, ntfs, exfat...
        self.fs_label = fs_label          # label du volume, peut être None
        self.fs_uuid = fs_uuid            # UUID du volume, peut être None
        self.serial = serial              # numéro de série du périphérique USB

    def __repr__(self):
        return (f"UsbDeviceInfo(device_node={self.device_node!r}, "
                f"fs_type={self.fs_type!r}, fs_label={self.fs_label!r}, "
                f"serial={self.serial!r})")


class UsbMonitor:
    """
    Surveille les événements udev et notifie l'insertion/le retrait de clés USB.

    Usage :
        monitor = UsbMonitor(on_inserted=handle_insert, on_removed=handle_remove)
        monitor.start()
        ...
        monitor.stop()
    """

    def __init__(self, on_inserted, on_removed):
        """
        on_inserted(UsbDeviceInfo) : appelé quand une partition USB apparaît
        on_removed(device_node: str) : appelé quand une partition USB disparaît
        """
        self._on_inserted = on_inserted
        self._on_removed = on_removed

        self._context = pyudev.Context()
        self._monitor = pyudev.Monitor.from_netlink(self._context)
        self._monitor.filter_by(subsystem="block", device_type="partition")

        self._observer = pyudev.MonitorObserver(
            self._monitor, self._handle_event, name="usb-monitor-observer"
        )

    def start(self):
        """Démarre l'écoute des événements udev en arrière-plan."""
        logger.info("Démarrage de la surveillance USB")
        self._observer.start()

    def stop(self):
        """Arrête l'écoute des événements udev."""
        logger.info("Arrêt de la surveillance USB")
        self._observer.stop()

    def scan_present_devices(self):
        """
        Retourne la liste des clés USB déjà branchées au démarrage de la borne
        (utile pour rattraper un branchement fait avant le lancement du programme).
        """
        devices = []
        for device in self._context.list_devices(subsystem="block", DEVTYPE="partition"):
            if self._is_usb_partition(device):
                devices.append(self._to_device_info(device))
        return devices

    def _handle_event(self, action, device):
        if not self._is_usb_partition(device):
            return

        if action == "add":
            info = self._to_device_info(device)
            logger.info("Clé USB détectée : %s", info)
            self._on_inserted(info)
        elif action == "remove":
            device_node = device.device_node
            logger.info("Clé USB retirée : %s", device_node)
            self._on_removed(device_node)

    @staticmethod
    def _is_usb_partition(device):
        """Filtre les événements pour ne garder que les partitions sur bus USB."""
        if device.get("ID_BUS") != config.REQUIRED_ID_BUS:
            return False
        if not device.device_node:
            return False
        return True

    @staticmethod
    def _to_device_info(device):
        return UsbDeviceInfo(
            device_node=device.device_node,
            fs_type=device.get("ID_FS_TYPE"),
            fs_label=device.get("ID_FS_LABEL"),
            fs_uuid=device.get("ID_FS_UUID"),
            serial=device.get("ID_SERIAL_SHORT") or device.get("ID_SERIAL"),
        )


if __name__ == "__main__":
    # Test manuel : lance le monitor et affiche les événements en direct.
    # À exécuter sur le Raspberry Pi (pyudev nécessite un système Linux avec udev).
    import signal
    import sys

    def handle_insert(info):
        print(f"[INSERTION] {info}")

    def handle_remove(device_node):
        print(f"[RETRAIT] {device_node}")

    monitor = UsbMonitor(on_inserted=handle_insert, on_removed=handle_remove)

    print("Clés déjà branchées :", monitor.scan_present_devices())
    monitor.start()
    print("En attente d'événements USB (Ctrl+C pour quitter)...")

    def shutdown(signum, frame):
        monitor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.pause()
