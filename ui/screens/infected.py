"""Écran affiché quand la clé USB est infectée, avec option de formatage."""

from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.screenmanager import Screen

KV = """
<InfectedScreen>:
    canvas.before:
        Color:
            rgba: 0.6, 0.1, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: "vertical"
        padding: 30
        spacing: 15

        Label:
            text: "Clé infectée !"
            font_size: "26sp"
            bold: True
            size_hint_y: 0.25

        Label:
            id: details_label
            text: root.details_text
            font_size: "14sp"
            size_hint_y: 0.35
            text_size: self.width, None

        Label:
            id: status_label
            text: root.status_text
            font_size: "14sp"
            size_hint_y: 0.15

        BoxLayout:
            size_hint_y: 0.25
            spacing: 20

            Button:
                text: "Formater la clé"
                font_size: "18sp"
                on_release: root.on_format_pressed()

            Button:
                text: "Retirer sans formater"
                font_size: "18sp"
                on_release: root.on_dismiss_pressed()
"""

Builder.load_string(KV)


class InfectedScreen(Screen):
    details_text = StringProperty("")
    status_text = StringProperty("")
    infected_files = ListProperty([])

    def set_infected_files(self, infected_files):
        self.infected_files = infected_files
        if infected_files:
            names = "\n".join(
                f"- {f['path']} ({f['signature']})" for f in infected_files[:5]
            )
            if len(infected_files) > 5:
                names += f"\n... et {len(infected_files) - 5} autre(s)"
        else:
            names = "Menace détectée."
        self.details_text = names
        self.status_text = ""

    def on_format_pressed(self):
        if self.manager and hasattr(self.manager, "app_controller"):
            self.manager.app_controller.request_format()

    def on_dismiss_pressed(self):
        self.status_text = ""
        self.manager.current = "idle"
