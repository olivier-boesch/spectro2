from kivy.base import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import mainthread
from graph import SmoothLinePlot
from kivy.properties import ObjectProperty, ListProperty, NumericProperty
from popups import *


# ------ Popup window for wavelength bounds in spectrum part
class PopupWavelengthSpectrum(Popup):
    """wavelengths selection for spectrum"""
    start = NumericProperty(defaultvalue=330)
    end = NumericProperty(defaultvalue=900)

    def when_opened(self):
        """what to do to initialize view"""
        # get bounds of spectrometer and apply
        min, max = 300, 900
        self.ids['wlstart_sldr'].min = min
        self.ids['wlstart_sldr'].max = max
        self.ids['wlend_sldr'].min = min
        self.ids['wlend_sldr'].max = max
        # get current values and apply
        self.start, self.end = 300, 900
        self.ids['wlstart_sldr'].value = self.start
        self.ids['wlend_sldr'].value = self.end

    def on_ok(self):
        """if user validates, set to internal values and close popup"""
        self.start = self.ids['wlstart_sldr'].value
        self.end = self.ids['wlend_sldr'].value
        # sapp.set_wavelength_spectrum(start, end)
        self.dismiss()

    def on_cancel(self):
        """if user invalidates, just close"""
        self.dismiss()

    def on_reset(self):
        """reset values to bounds"""
        min, max = 300, 900
        self.ids['wlstart_sldr'].value = min
        self.ids['wlend_sldr'].value = max

    def value_changed(self, who_has_changed):
        """restict changes : max must be >= min"""
        if self.ids['wlend_sldr'].value < self.ids['wlstart_sldr'].value:
            if who_has_changed == 'start':
                self.ids['wlend_sldr'].value = self.ids['wlstart_sldr'].value
            if who_has_changed == 'end':
                self.ids['wlstart_sldr'].value = self.ids['wlend_sldr'].value


class SpectrumScreen(Screen):
    main_app = ObjectProperty()
    data = ListProperty()


class BoxSpectrum(BoxLayout):

    def set_wl(self):
        self.pop_wl = PopupWavelengthSpectrum(start=330, end=900)
        self.pop_wl.open()

    def perform_blank(self, main_app):
        print(self.pop_wl.start, self.pop_wl.end)
        main_app.popup_operation = PopupOperation()
        main_app.popup_operation.open()
        main_app.popup_operation.update("Mesure du blanc", "En cours...")
        main_app.popup_operation.close_after(5)

    def perform_spectrum(self, main_app):
        main_app.popup_operation = PopupOperation()
        main_app.popup_operation.open()
        main_app.popup_operation.update("Mesure du spectre", "En cours...")
        main_app.popup_operation.close_after(5)



Builder.load_string("""
#:import Graph graph.Graph

<SpectrumScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: 30
        BoxSpectrum:
            
<BoxSpectrum>
    id: box_spectrum
    orientation: 'vertical'
    Label:
        id: boxspectrum_title_lbl
        text: 'Mesure de Spectre'
        size_hint_y: None
        height: dp(30)
    BoxLayout:
        size_hint_y: None
        height: dp(100)
        Button:
            text: "longueur d'ondes"
            on_release: root.set_wl()
        Button:
            text: "Blanc"
            on_release: root.perform_blank(app)
        Button:
            text: "Mesure"
            on_release: root.perform_spectrum(app)
        Spinner:
            id: spectrum_export_spinner
            text: 'Exporter'
            values: ['Exporter en image png','Exporter les donn\u00e9es']
            on_text: app.save_spectrum(self.text)
    Label:
        id: boxspectrum_coordinates_lbl
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
        
<PopupWavelengthSpectrum>
    size_hint: 0.8, 0.5
    title: "Sélection de la plage de longueur d\'onde"
    auto_dismiss: False
    on_open: root.when_opened()
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'vertical'
            padding: dp(10), dp(10), dp(10), dp(50)
            Label:
                text: "longueur d\'onde de départ: %d nm"%(wlstart_sldr.value,)
            Slider:
                id: wlstart_sldr
                orientation: 'horizontal'
                step: 1
                on_value: root.value_changed('start')
            Label:
                text: "longueur d\'onde de fin: %  d nm"%(wlend_sldr.value,)
            Slider:
                id: wlend_sldr
                orientation: 'horizontal'
                step: 1
                on_value: root.value_changed('end')
        BoxLayout:
            padding: dp(10)
            spacing: dp(10)
            size_hint_y: None
            height: dp(100)
            orientation: 'horizontal'
            SpecButton:
                text: "Plage Complète"
                on_release: root.on_reset()
            SpecButton:
                text: 'Annuler'
                on_release: root.on_cancel()
            SpecButton:
                text: 'Valider'
                on_release: root.on_ok()
""")
