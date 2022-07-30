from kivy.base import Builder
from kivy.uix.screenmanager import Screen
from kivy.clock import mainthread
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty


class KineticsScreen(Screen):
    main_app = ObjectProperty()


class BoxKinetics(BoxLayout):
    def ask_wl(self):
        p = PopupWavelengthKinetics()
        p.open()


# ------ Popup window for wavelength bounds in spectrum part
class PopupWavelengthKinetics(Popup):
    """wavelengths selection for spectrum"""
    wavelength = NumericProperty(defaultvalue=300)

    def when_opened(self):
        """what to do to initialize view"""
        # get bounds of spectrometer and apply
        min, max = 300, 900
        self.ids['wl_sldr'].min = min
        self.ids['wl_sldr'].max = max
        # get current values and apply
        self.ids['wl_sldr'].value = self.wavelength

    def on_ok(self):
        """if user validates, set to internal values and close popup"""
        self.wavelength = self.ids['wl_sldr'].value
        self.dismiss()

    def on_cancel(self):
        """if user invalidates, just close"""
        self.dismiss()


Builder.load_string("""
<KineticsScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: 30
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
            on_release: root.ask_wl()
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
        xlabel: "temps(s)"
        ylabel: "Absorbance"
        x_ticks_minor: 1
        x_ticks_major: 4
        y_ticks_minor: 4
        y_ticks_major: 0.2
        y_grid_label: True
        x_grid_label: True
        y_grid: True
        x_grid: True
        ymin: 0
        ymax: 2
        xmin: 0
        xmax: 20
        
<PopupWavelengthKinetics>
    size_hint: 0.8, 0.3
    title: "Sélection de la longueur d\'onde"
    auto_dismiss: False
    on_open: root.when_opened()
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'vertical'
            padding: dp(10), dp(10), dp(10), dp(50)
            Label:
                text: "longueur d\'onde %d nm"%(wl_sldr.value,)
            Slider:
                id: wl_sldr
                orientation: 'horizontal'
                step: 1
        BoxLayout:
            padding: dp(10)
            spacing: dp(10)
            size_hint_y: None
            height: dp(100)
            orientation: 'horizontal'
            SpecButton:
                text: 'Annuler'
                on_release: root.on_cancel()
            SpecButton:
                text: 'Valider'
                on_release: root.on_ok()
""")
