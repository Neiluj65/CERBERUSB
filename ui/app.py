"""
Application Kivy plein écran (mode kiosque) pour la borne USB.

Ce module ne contient AUCUNE logique métier (pas de scan, pas de montage,
pas de formatage) : il expose uniquement les écrans et des méthodes pour
naviguer entre eux. L'orchestration (main.py) pilote l'UI via ces méthodes
et reçoit les actions utilisateur (bouton "Formater") via app_controller.
"""

from kivy.app import App
from kivy.config import Config
from kivy.uix.screenmanager import NoTransition, ScreenManager

from ui.screens.clean import CleanScreen
from ui.screens.idle import IdleScreen
from ui.screens.infected import InfectedScreen
from ui.screens.scanning import ScanningScreen

# Mode kiosque : plein écran, pas de bordure de fenêtre.
Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "borderless", "1")
Config.set("kivy", "keyboard_mode", "system")


class BorneScreenManager(ScreenManager):
    """ScreenManager avec une référence vers le contrôleur applicatif (main.py),
    pour que les écrans puissent déclencher des actions (ex: formatage)."""
    app_controller = None


class BorneApp(App):
    def __init__(self, app_controller=None, **kwargs):
        super().__init__(**kwargs)
        self.app_controller = app_controller

    def build(self):
        sm = BorneScreenManager(transition=NoTransition())
        sm.app_controller = self.app_controller

        sm.add_widget(IdleScreen(name="idle"))
        sm.add_widget(ScanningScreen(name="scanning"))
        sm.add_widget(CleanScreen(name="clean"))
        sm.add_widget(InfectedScreen(name="infected"))

        sm.current = "idle"
        self.screen_manager = sm
        return sm

    def show_idle(self):
        self.screen_manager.current = "idle"

    def show_scanning(self, device_node):
        screen = self.screen_manager.get_screen("scanning")
        screen.set_device(device_node)
        self.screen_manager.current = "scanning"

    def show_clean(self):
        self.screen_manager.current = "clean"

    def show_infected(self, infected_files):
        screen = self.screen_manager.get_screen("infected")
        screen.set_infected_files(infected_files)
        self.screen_manager.current = "infected"

    def set_infected_status(self, text):
        screen = self.screen_manager.get_screen("infected")
        screen.status_text = text
