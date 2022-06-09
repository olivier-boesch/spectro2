from kivy.base import Builder
from kivy.uix.screenmanager import Screen
from kivy.clock import mainthread
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout


class KineticsScreen(Screen):
    main_app = ObjectProperty()


class BoxKinetics(BoxLayout):
    pass


Builder.load_string("""
<KineticsScreen>:
    BoxLayout:
        orientation: "vertical"
        BoxKinetics:

<BoxKinetics>
    id: box_kinetics
    orientation: 'vertical'
    Label:
        id: boxkinetics_title_lbl
        text: 'Cinétique Chimique'
        size_hint_y: None
        height: dp(30)
    BoxLayout:
        size_hint_y: None
        height: dp(100)
        Button:
            text: "longueur d'ondes"
        Button:
            text: "Blanc"
        Button:
            text: "Mesure"
        Spinner:
            id: spectrum_export_spinner
            text: 'Exporter'
            values: ['Exporter en image png','Exporter les donn\u00e9es']
            on_text: app.save_spectrum(self.text)
    Label:
        id: boxkinetics_coordinates_lbl
        text: "0,0"
        size_hint_y: None
        height: dp(30)
    Graph:
        id: graph_widget
        xlabel: "longueur d\'onde (nm)"
        ylabel: "Absorbance"
        x_ticks_minor: 5
        x_ticks_major: 50
        y_ticks_minor: 4
        y_ticks_major: 0.2
        y_grid_label: True
        x_grid_label: True
        y_grid: True
        x_grid: True
        ymin: 0
        ymax: 2
        xmin: 330
        xmax: 900
""")
