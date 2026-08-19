"""Écran d'attente : aucune clé branchée."""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

KV = """
<IdleScreen>:
    canvas.before:
        Color:
            rgba: 0.13, 0.16, 0.22, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: "vertical"
        padding: 30
        spacing: 20

        Label:
            text: "Borne de décontamination USB"
            font_size: "22sp"
            bold: True
            size_hint_y: 0.3

        Label:
            text: "Branchez une clé USB pour lancer l'analyse"
            font_size: "18sp"
            size_hint_y: 0.7
"""

Builder.load_string(KV)


class IdleScreen(Screen):
    pass
