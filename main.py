"""
Orchestration globale de la borne USB.

Ce module fait le lien entre :
- usb_monitor.py (détection udev, tourne dans son propre thread observer)
- scanner.py (scan ClamAV, lancé dans un thread pour ne pas bloquer l'UI)
- formatter.py (formatage, lancé dans un thread pour la même raison)
- ui/app.py (Kivy, dont la boucle d'événements tourne sur le thread principal)

Tous les callbacks venant d'un autre thread (udev, scan, formatage) sont
renvoyés sur le thread principal via kivy.clock.Clock.schedule_once, seul
moyen sûr de manipuler les widgets Kivy depuis un thread externe.
"""

import logging
import threading

from kivy.clock import Clock

import config
import formatter
import scanner
from ui.app import BorneApp
from usb_monitor import UsbMonitor

logger = logging.getLogger("main")


def _setup_logging():
    logger.setLevel(logging.INFO)
    formatter_ = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter_)
    logger.addHandler(console_handler)

    try:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(config.SCAN_LOG_FILE)
        file_handler.setFormatter(formatter_)
        logger.addHandler(file_handler)
    except OSError as exc:
        logger.warning("Impossible d'écrire les logs dans %s (%s) — logs console uniquement",
                        config.LOG_DIR, exc)


class BorneController:
    """
    Contrôleur applicatif : reçoit les événements USB et les actions
    utilisateur de l'UI, pilote scanner.py / formatter.py, et met à jour
    l'UI en conséquence.
    """

    def __init__(self):
        self.app = BorneApp(app_controller=self)
        self.monitor = UsbMonitor(on_inserted=self._handle_inserted, on_removed=self._handle_removed)
        self.current_device = None  # UsbDeviceInfo de la clé actuellement traitée

    def run(self):
        self.monitor.start()
        for device_info in self.monitor.scan_present_devices():
            # Rattrape une clé déjà branchée au démarrage de la borne.
            self._handle_inserted(device_info)
        try:
            self.app.run()
        finally:
            self.monitor.stop()

    # --- Événements USB (appelés depuis le thread observer pyudev) ---

    def _handle_inserted(self, device_info):
        if self.current_device is not None:
            logger.info("Clé %s ignorée : une clé est déjà en cours de traitement",
                         device_info.device_node)
            return

        self.current_device = device_info
        Clock.schedule_once(lambda dt: self.app.show_scanning(device_info.device_node))
        threading.Thread(target=self._run_scan, args=(device_info,), daemon=True).start()

    def _handle_removed(self, device_node):
        if self.current_device is not None and self.current_device.device_node == device_node:
            logger.info("Clé retirée pendant le traitement : %s", device_node)
            self.current_device = None
            Clock.schedule_once(lambda dt: self.app.show_idle())

    # --- Scan (appelé depuis un thread de travail) ---

    def _run_scan(self, device_info):
        result = scanner.scan_device(device_info)

        if self.current_device is None or self.current_device.device_node != device_info.device_node:
            # La clé a été débranchée pendant le scan : on n'affiche rien.
            return

        if result.status == scanner.ScanStatus.CLEAN:
            Clock.schedule_once(lambda dt: self.app.show_clean())
            self.current_device = None
        elif result.status == scanner.ScanStatus.INFECTED:
            Clock.schedule_once(lambda dt: self.app.show_infected(result.infected_files))
        else:
            logger.error("Scan en erreur pour %s : %s", device_info.device_node, result.error_message)
            Clock.schedule_once(lambda dt: self.app.show_infected([]))
            Clock.schedule_once(lambda dt: self.app.set_infected_status(
                f"Erreur de scan : {result.error_message}"))
            self.current_device = None

    # --- Action utilisateur : demande de formatage (appelée depuis le thread UI) ---

    def request_format(self):
        if self.current_device is None:
            return

        device_info = self.current_device
        self.app.set_infected_status("Formatage en cours...")
        threading.Thread(target=self._run_format, args=(device_info,), daemon=True).start()

    def _run_format(self, device_info):
        try:
            formatter.format_device(device_info.device_node, confirm=True)
        except formatter.FormatError as exc:
            logger.error("Échec du formatage de %s : %s", device_info.device_node, exc)
            Clock.schedule_once(lambda dt: self.app.set_infected_status(f"Échec du formatage : {exc}"))
            return

        self.current_device = None
        Clock.schedule_once(lambda dt: self.app.show_idle())


if __name__ == "__main__":
    _setup_logging()
    BorneController().run()
