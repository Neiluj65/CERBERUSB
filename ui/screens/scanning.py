"""Écran affiché pendant le scan antivirus de la clé."""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

KV = """
<ScanningScreen>:
    canvas.before:
        Color:
            rgba: 0.15, 0.35, 0.55, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: "vertical"
        padding: 30
        spacing: 20

        Label:
            text: "Analyse antivirus en cours..."
            font_size: "22sp"
            bold: True
            size_hint_y: 0.4

        Label:
            id: device_label
            text: ""
            font_size: "16sp"
            size_hint_y: 0.2

        Label:
            text: "Ne débranchez pas la clé"
            font_size: "16sp"
            size_hint_y: 0.4
"""

Builder.load_string(KV)


class ScanningScreen(Screen):
    def set_device(self, device_node):
        self.ids.device_label.text = device_node
