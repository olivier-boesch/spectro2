from lib_spectro.s250Prim_async import S250Prim

__version__ = "2.0"
from kivy.utils import platform
from kivy.config import Config
Config.set("graphics", "maxfps", "60")
Config.set("graphics", 'multisample', 16)

if platform in ['win', 'linux']:
    Config.set('kivy', 'desktop', 1)  # desktop app (not mobile)
    Config.set('graphics','window_state','maximized')

from kivy.app import App
from kivy.uix.popup import Popup
from kivy.logger import Logger, LOG_LEVELS
from kivy.clock import Clock, mainthread
from kivy.uix.screenmanager import ScreenManager, FadeTransition, Screen
from device_screen import DeviceScreen
from spectrum_screen import SpectrumScreen
from absorbance_screen import AbsorbanceScreen
from kinetics_screen import KineticsScreen
from popups import PopupMessage

Logger.setLevel(LOG_LEVELS['debug'])


# -------------- Main App
class SpectroApp(App):
    # ---- Data
    title = "Spectro" + " v" + __version__
    ports_update_event = None
    spectro = S250Prim()
    serial_port = None
    devicescreen = None
    spectrumscreen = None
    absorbancescreen = None
    kineticsscreen = None
    popup_operation = None

    # ---- popups helpers
    def show_message(self, title, message, timeout=2.):
        popup = PopupMessage()
        popup.open()
        popup.set_message(title, message)
        popup.close_after(timeout)

    # ---- Start, stop, pause & resume
    def on_start(self):
        self.spectro.activity_out_clbk = self.outcoming_data
        self.spectro.activity_in_clbk = self.incoming_data
        wid = self.root.ids["screen_manager"]
        self.devicescreen = DeviceScreen(name="device", main_app=self)
        self.spectrumscreen = SpectrumScreen(name="spectrum", main_app=self)
        self.absorbancescreen = AbsorbanceScreen(name="absorbance", main_app=self)
        self.kineticsscreen = KineticsScreen(name="kinetics", main_app=self)
        wid.add_widget(self.devicescreen)
        wid.add_widget(self.spectrumscreen)
        wid.add_widget(self.absorbancescreen)
        wid.add_widget(self.kineticsscreen)

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        pass

    # ---- led activity
    @mainthread
    def incoming_data(self):
        self.root.ids['led_in'].state = "on"

    @mainthread
    def outcoming_data(self):
        self.root.ids['led_out'].state = "on"


myapp = SpectroApp()
myapp.run()
