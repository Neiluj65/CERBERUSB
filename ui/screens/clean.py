"""Écran affiché quand la clé USB est saine."""

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

KV = """
<CleanScreen>:
    canvas.before:
        Color:
            rgba: 0.1, 0.55, 0.25, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: "vertical"
        padding: 30
        spacing: 20

        Label:
            text: "Clé saine"
            font_size: "26sp"
            bold: True
            size_hint_y: 0.4

        Label:
            text: "Aucune menace détectée. Vous pouvez retirer la clé."
            font_size: "16sp"
            size_hint_y: 0.6
"""

Builder.load_string(KV)

AUTO_RETURN_DELAY_SECONDS = 6


class CleanScreen(Screen):
    def on_enter(self):
        self._return_event = Clock.schedule_once(self._go_idle, AUTO_RETURN_DELAY_SECONDS)

    def on_leave(self):
        if getattr(self, "_return_event", None):
            self._return_event.cancel()

    def _go_idle(self, dt):
        self.manager.current = "idle"
