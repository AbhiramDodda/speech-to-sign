import os
import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.videoplayer import VideoPlayer
from kivy.clock import Clock
import sounddevice as sd
import numpy as np
import wave
import threading
import platform
import subprocess
from datetime import datetime
from functools import partial
from speech_to_text import main_text


class Database:
    def __init__(self):
        self.db_path = "user_database.db"
        self.initialize_db()

    def initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mobile TEXT UNIQUE,
                password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def user_exists(self, mobile):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE mobile = ?", (mobile,))
        user = cursor.fetchone()
        
        conn.close()
        return user is not None
        
    def validate_login(self, mobile, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE mobile = ? AND password = ?", 
                      (mobile, password))
        user = cursor.fetchone()
        
        conn.close()
        return user is not None
        
    def register_user(self, mobile, password):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO users (mobile, password) VALUES (?, ?)",
                          (mobile, password))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return False

# Login Screen
class LoginScreen(Screen):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        title = Label(text='Audio Video App Login', font_size=24, size_hint_y=0.2)

        form = GridLayout(cols=2, spacing=10, size_hint_y=0.4)
        
        form.add_widget(Label(text='Mobile Number:'))
        self.mobile_input = TextInput(multiline=False, input_type='number', input_filter='int')
        form.add_widget(self.mobile_input)
        
        form.add_widget(Label(text='Password:'))
        self.password_input = TextInput(multiline=False, password=True)
        form.add_widget(self.password_input)

        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        
        self.login_btn = Button(text='Login')
        self.login_btn.bind(on_press=self.verify_login)
        
        self.register_btn = Button(text='Register')
        self.register_btn.bind(on_press=self.go_to_register)
        
        buttons_layout.add_widget(self.login_btn)
        buttons_layout.add_widget(self.register_btn)

        self.error_label = Label(text='', color=(1, 0, 0, 1), size_hint_y=0.2)

        layout.add_widget(title)
        layout.add_widget(form)
        layout.add_widget(buttons_layout)
        layout.add_widget(self.error_label)
        
        self.add_widget(layout)
    
    def verify_login(self, instance):
        mobile = self.mobile_input.text.strip()
        password = self.password_input.text.strip()
        
        if not mobile or not password:
            self.error_label.text = "Please enter both mobile number and password"
            return
            
        if not mobile.isdigit():
            self.error_label.text = "Mobile number should contain only digits"
            return
            
        if self.db.validate_login(mobile, password):
            self.manager.transition.direction = 'left'
            self.manager.current = 'home'
            self.mobile_input.text = ''
            self.password_input.text = ''
            self.error_label.text = ''
        elif self.db.user_exists(mobile):
            self.error_label.text = "Invalid password"
        else:
            self.error_label.text = "User not found. Please register."
    
    def go_to_register(self, instance):
        register_screen = self.manager.get_screen('register')
        register_screen.mobile_input.text = self.mobile_input.text
        
        self.manager.transition.direction = 'left'
        self.manager.current = 'register'
        self.error_label.text = ''

# Registration Screen
class RegisterScreen(Screen):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        title = Label(text='Register New Account', font_size=24, size_hint_y=0.2)

        form = GridLayout(cols=2, spacing=10, size_hint_y=0.5)
        
        form.add_widget(Label(text='Mobile Number:'))
        self.mobile_input = TextInput(multiline=False, input_type='number', input_filter='int')
        form.add_widget(self.mobile_input)
        
        form.add_widget(Label(text='Password:'))
        self.password_input = TextInput(multiline=False, password=True)
        form.add_widget(self.password_input)
        
        form.add_widget(Label(text='Confirm Password:'))
        self.confirm_password_input = TextInput(multiline=False, password=True)
        form.add_widget(self.confirm_password_input)

        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        
        self.register_btn = Button(text='Register')
        self.register_btn.bind(on_press=self.process_registration)
        
        self.back_btn = Button(text='Back to Login')
        self.back_btn.bind(on_press=self.go_back_to_login)
        
        buttons_layout.add_widget(self.register_btn)
        buttons_layout.add_widget(self.back_btn)

        self.error_label = Label(text='', color=(1, 0, 0, 1), size_hint_y=0.2)

        layout.add_widget(title)
        layout.add_widget(form)
        layout.add_widget(buttons_layout)
        layout.add_widget(self.error_label)
        
        self.add_widget(layout)
    
    def process_registration(self, instance):
        mobile = self.mobile_input.text.strip()
        password = self.password_input.text.strip()
        confirm_password = self.confirm_password_input.text.strip()

        if not mobile or not password or not confirm_password:
            self.error_label.text = "Please fill in all fields"
            return
            
        if not mobile.isdigit():
            self.error_label.text = "Mobile number should contain only digits"
            return
            
        if len(mobile) < 10:
            self.error_label.text = "Mobile number should be at least 10 digits"
            return
            
        if password != confirm_password:
            self.error_label.text = "Passwords don't match"
            return
            
        if len(password) < 6:
            self.error_label.text = "Password should be at least 6 characters"
            return

        if self.db.user_exists(mobile):
            self.error_label.text = "Mobile number already registered"
            return

        if self.db.register_user(mobile, password):
            self.error_label.text = ''
            self.manager.transition.direction = 'left'
            self.manager.current = 'home'

            self.mobile_input.text = ''
            self.password_input.text = ''
            self.confirm_password_input.text = ''
        else:
            self.error_label.text = "Registration failed. Please try again."
    
    def go_back_to_login(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'login'
        self.error_label.text = ''

class AudioVideoInterface(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10
        self.speech_to_video_function = main_text
        self.top_section = BoxLayout(
            orientation='vertical',
            size_hint_y=0.3,
            spacing=10
        )
        self.status_label = Label(
            text='Ready to record',
            size_hint_y=0.3
        )

        self.record_btn = Button(
            text='Start Recording',
            size_hint_y=0.3
        )
        self.record_btn.bind(on_press=self.toggle_recording)

        self.top_section.add_widget(self.status_label)
        self.top_section.add_widget(self.record_btn)
        self.video_player = VideoPlayer(
            size_hint_y=0.7,
            state='stop',
            options={'allow_stretch': True}
        )

        self.add_widget(self.top_section)
        self.add_widget(self.video_player)

        self.is_recording = False
        self.frames = []
        self.sample_rate = 44100
        self.video_path = None

        self.recordings_dir = "recordings"
        if not os.path.exists(self.recordings_dir):
            os.makedirs(self.recordings_dir)

    def toggle_recording(self, instance):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.is_recording = True
        self.frames = []  
        self.record_btn.text = 'Stop Recording'
        self.status_label.text = 'Recording...'
        threading.Thread(target=self.record_audio).start()
    
    def stop_recording(self):
        self.is_recording = False
        self.record_btn.text = 'Start Recording'
        self.status_label.text = 'Processing...'
        threading.Thread(target=self.save_and_process_audio).start()
    
    def record_audio(self):
        def callback(indata, frames, time, status):
            if self.is_recording:
                self.frames.append(indata.copy())
        
        with sd.InputStream(channels=1, callback=callback, 
                          samplerate=self.sample_rate):
            while self.is_recording:
                sd.sleep(100)
    
    def save_and_process_audio(self):
        if not self.frames:
            self.update_status('No audio recorded')
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"recording_{timestamp}.wav"
            audio_filepath = os.path.join(self.recordings_dir, audio_filename)

            audio_data = np.concatenate(self.frames, axis=0)

            with wave.open(audio_filepath, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16))
            
            # Process audio with external function
            self.update_status('Converting speech to video...')
            self.video_path = self.speech_to_video_function(audio_filepath)
            print(self.video_path)
            Clock.schedule_once(lambda dt: self.play_video(self.video_path))
            
        except Exception as e:
            self.update_status(f'Error: {str(e)}')
    
    def play_video(self, video_path):
        if os.path.exists(video_path):
            self.update_status('Playing video externally...')
            
            if platform.system() == "Windows":
                os.startfile(video_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", video_path])
            else:  # Linux
                subprocess.run(["xdg-open", video_path])

            Clock.schedule_once(lambda dt: self.delete_video(video_path), 10)
        else:
            self.update_status('Video file not found')
            
    def delete_video(self, video_path):
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print("File deleted successfully")
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            
    def update_status(self, text):
        Clock.schedule_once(lambda dt: self.set_status(text))
    
    def set_status(self, text):
        self.status_label.text = text

# Home Screen with Audio/Video functionality
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        header = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        title = Label(text='Audio Video App', font_size=20)
        self.logout_btn = Button(text='Logout', size_hint_x=0.3)
        self.logout_btn.bind(on_press=self.logout)
        
        header.add_widget(title)
        header.add_widget(self.logout_btn)

        self.audio_video_interface = AudioVideoInterface()

        layout.add_widget(header)
        layout.add_widget(self.audio_video_interface)
        
        self.add_widget(layout)
    
    def logout(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'login'

class AudioVideoApp(App):
    def build(self):
        self.db = Database()

        self.sm = ScreenManager()

        self.login_screen = LoginScreen(self.db, name='login')
        self.register_screen = RegisterScreen(self.db, name='register')
        self.home_screen = HomeScreen(name='home')
        
        self.sm.add_widget(self.login_screen)
        self.sm.add_widget(self.register_screen)
        self.sm.add_widget(self.home_screen)

        self.sm.current = 'login'
        
        return self.sm
    
    def on_stop(self):
        try:
            if os.path.exists("recordings"):
                for file in os.listdir("recordings"):
                    if file.endswith((".mp4", ".wav")):  # Clean up audio and video files
                        try:
                            file_path = os.path.join("recordings", file)
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                print(f"Deleted: {file}")
                        except Exception as e:
                            print(f"Error deleting {file}: {str(e)}")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

if __name__ == '__main__':
    AudioVideoApp().run()