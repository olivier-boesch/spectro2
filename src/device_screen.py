from kivy.base import Builder
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock, mainthread
from kivy.base import platform
from kivy.logger import Logger
from kivy.properties import ObjectProperty

if platform in ['windows', 'linux']:
    from serial.tools import list_ports

    def get_serial_ports_list():
        ports = list_ports.comports()
        return [item.device for item in ports]

elif platform == 'android':
    from usb4a import usb

    def get_serial_ports_list():
        usb_device_list = usb.get_usb_device_list()
        return [device.getDeviceName() for device in usb_device_list]


class DeviceScreen(Screen):
    main_app = ObjectProperty()

    # ---- Serial ports & com
    def ports_update_state(self, on=False):
        if on:
            Logger.info("Serial: Turning on port update")
            self.update_serial_ports()
            self.ports_update_event = Clock.schedule_interval(lambda dt: self.update_serial_ports(), 1.0)
        else:
            Logger.info("Serial: Turning off port update")
            self.ports_update_event.cancel()

    def update_serial_ports(self):
        ports = get_serial_ports_list()
        Logger.info("Serial ports: found {:s}".format(str(ports)))
        self.update_serial_ports_ui(ports)

    def update_serial_ports_ui(self, ports_list):
        wid = self.ids["serial_port"]
        wid.values = ports_list
        # if no ports in list or text not in list -> display default text
        if not ports_list or wid.text not in ports_list:
            wid.text = wid.text_default
        # if only one port -> select it as default one
        if len(ports_list) == 1:
            wid.text = ports_list[0]

    def serial_port_ui_change(self, instance, text):
        if text != instance.text_default:
            self.main_app.serial_port = text
        else:
            self.main_app.serial_port = None
        Logger.info("Serial port: internal value changed to {:s}".format(str(self.main_app.serial_port)))

    def connect(self, button, state):
        if self.main_app.serial_port is not None:
            if state == "down":
                Logger.info("Serial port: Connecting to {:s}".format(self.main_app.serial_port))
                ret = self.main_app.spectro.connect(self.main_app.serial_port)
                self.set_ui_connect_state(True)
                if ret:
                    Logger.info("Device: Starting...")
                    self.main_app.spectro.start_device(clbk=self.connect_callback)
                else:
                    self.set_ui_connect_state(False)
            else:
                self.main_app.spectro.disconnect()
                self.set_ui_connect_state(False)
                Logger.info("Serial port: Disconnecting...")
        else:
            button.state = "normal"

    def set_ui_connect_state(self, state=False):
        if state:
            self.ports_update_state(False)
            self.main_app.root.ids['connect_label'].backgound_color = (0, 1, 0, 1)
            self.main_app.root.ids['connect_label'].text = "Connecté"
        else:
            self.ports_update_state(True)
            self.ids['connect_btn'].state = "normal"
            self.main_app.root.ids['connect_label'].backgound_color = (1, 0, 0, 1)
            self.main_app.root.ids['connect_label'].text = "Non Connecté"

    @mainthread
    def connect_callback(self, ret_val):
        Logger.info("Device: returned {!r}".format(ret_val))
        if ret_val is None or not ret_val:
            self.main_app.show_message("Connection Error", "Can't connect to device (really plugged ?)", 5.)
            self.set_ui_connect_state(False)
            self.main_app.spectro.disconnect()
        else:
            self.set_ui_connect_state(True)


Builder.load_string("""
<DeviceScreen>:
    id: device_screen
    on_pre_enter: self.ports_update_state(True)
    on_leave: self.ports_update_state(False)
    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 30
        Image:
            source: "images/device.png"
        Spinner:
            size_hint_y: None
            height: dp(100)
            id: serial_port
            text_default: "---"
            text: self.text_default
            on_text: device_screen.serial_port_ui_change(self, self.text)
        ToggleButton:
            id: connect_btn
            size_hint_y: None
            height: dp(100)
            text: "Connect"
            on_release: device_screen.connect(self, self.state)
        Label:
""")
