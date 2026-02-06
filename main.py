import threading
import time
import os
import sys

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.utils import platform
from kivy.clock import Clock

# Flask import
from web_server import app as flask_app

# Global state
server_thread = None
server_running = False

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.app = app
        self.daemon = True

    def run(self):
        # On Android, we need to make sure we are serving on 0.0.0.0
        # Port 5001 as usual
        flask_app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

class MainInterface(BoxLayout):
    def __init__(self, **kwargs):
        super(MainInterface, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10

        # Title
        self.add_widget(Label(text='Payload Persist Server', font_size='24sp', size_hint_y=0.1))

        # Status
        self.status_label = Label(text='Status: STOPPED', font_size='18sp', color=(1, 0, 0, 1), size_hint_y=0.1)
        self.add_widget(self.status_label)

        # IP Info
        self.ip_info = TextInput(text='Connect via Hotspot IP:5001', readonly=True, size_hint_y=0.15, multiline=True)
        self.add_widget(self.ip_info)

        # Log area (simulated)
        self.log_area = TextInput(text='Logs will appear here...', readonly=True, size_hint_y=0.5)
        self.add_widget(self.log_area)

        # Control Button
        self.toggle_btn = Button(text='START SERVER', size_hint_y=0.15, background_color=(0, 1, 0, 1))
        self.toggle_btn.bind(on_press=self.toggle_server)
        self.add_widget(self.toggle_btn)

        # Auto-start logic
        Clock.schedule_once(self.start_server, 1)

    def toggle_server(self, instance):
        # For now, we only support starting (Flask doesn't have a clean "stop" without complex logic)
        if not server_running:
            self.start_server(None)
    
    def start_server(self, dt):
        global server_running, server_thread
        
        if server_running:
            return

        self.log("Starting server thread...")
        
        # Acquire Wake Lock on Android
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.WAKE_LOCK, Permission.WRITE_EXTERNAL_STORAGE])
            
            # Simple wake lock
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            Context = autoclass('android.content.Context')
            PowerManager = autoclass('android.os.PowerManager')
            pm = activity.getSystemService(Context.POWER_SERVICE)
            self.wake_lock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, 'PayloadServerLock')
            self.wake_lock.acquire()
            self.log("Wake Lock acquired.")

        try:
            server_thread = ServerThread(flask_app)
            server_thread.start()
            server_running = True
            
            self.status_label.text = "Status: RUNNING"
            self.status_label.color = (0, 1, 0, 1) # Green
            self.toggle_btn.text = "SERVER RUNNING"
            self.toggle_btn.disabled = True # Cannot stop easily
            self.log("Server started on port 5001")
            
            # Try to guess IP (simplified)
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                self.ip_info.text = f"Connect to:\nhttp://{ip}:5001"
            except:
                self.ip_info.text = "Could not detect IP.\nCheck your Hotspot settings."

        except Exception as e:
            self.log(f"Error starting server: {str(e)}")

    def log(self, message):
        self.log_area.text += f"\n{message}"

class PayloadPersistApp(App):
    def build(self):
        return MainInterface()

if __name__ == '__main__':
    PayloadPersistApp().run()
