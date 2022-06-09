from kivy.base import Builder
from kivy.uix.popup import Popup
from kivy.clock import Clock


# ------- Popup for message notification
class PopupMessage(Popup):
    """PopupMessage : display a message box"""

    def when_opened(self):
        pass

    def set_message(self, title, text):
        """set_message: set title and text"""
        self.title = title
        self.ids['message_content_lbl'].text = text

    def get_message(self):
        """get_message: get title and text"""
        return self.title, self.ids['message_content_lbl'].text

    def close_after(self, dt=1.):
        """close popup automaticaly after a short time (us 1s)"""
        Clock.schedule_once(lambda t: self.dismiss(), dt)


# ------- Popup for operation running (no dismiss)
class PopupOperation(Popup):
    """display a popup while an operation occures"""

    def when_opened(self):
        pass

    def update(self, title, text):
        """set title and text"""
        self.ids['message_operation_lbl'].text = text
        self.title = title

    def close_after(self, dt=2.):
        """close popup automaticaly after a short time (us 1s)"""
        Clock.schedule_once(lambda t: self.dismiss(), dt)


Builder.load_string("""

<PopupMessage>
    size_hint: None,None
    size: dp(400), dp(130)
    pos_hint: {'top': 0.95, 'right':0.98}
    auto_dismiss: True
    on_open: root.when_opened()
    BoxLayout:
        orientation: 'vertical'
        Label:
            id: message_content_lbl

<PopupOperation>
    size_hint: None,None
    size: dp(500), dp(200)
    pos_hint: {'center_x': 0.5, 'center_y':0.5}
    auto_dismiss: False
    on_open: root.when_opened()
    Label:
        id: message_operation_lbl

""")