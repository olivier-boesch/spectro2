from kivy.base import Builder
from kivy.uix.screenmanager import Screen
from kivy.clock import mainthread
from kivy.properties import ObjectProperty


class AbsorbanceScreen(Screen):
    main_app = ObjectProperty()


Builder.load_string("""
<AbsorbanceScreen>:
    BoxLayout:
        orientation: "vertical"
        Label:
            text: "abs"
""")
