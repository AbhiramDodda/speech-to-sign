from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.videoplayer import VideoPlayer
from kivy.clock import Clock
import sounddevice as sd
import numpy as np
import wave
import threading
import os
from datetime import datetime
from speech_to_text import main_text
import platform
import subprocess

class AudioVideoInterface(BoxLayout):
    def __init__(self, speech_to_video_function, **kwargs):
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
        
        # Record button
        self.record_btn = Button(
            text='Start Recording',
            size_hint_y=0.3
        )
        self.record_btn.bind(on_press=self.toggle_recording)
        
        # Add controls to top section
        self.top_section.add_widget(self.status_label)
        self.top_section.add_widget(self.record_btn)
        self.video_player = VideoPlayer(
            size_hint_y=0.7,
            state='stop',
            options={'allow_stretch': True}
        )
        
        # Add all sections to main layout
        self.add_widget(self.top_section)
        self.add_widget(self.video_player)
        
        # Recording state and settings
        self.is_recording = False
        self.frames = []
        self.sample_rate = 44100
        
        # Create recordings directory if it doesn't exist
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
            # Save audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"recording_{timestamp}.wav"
            audio_filepath = os.path.join(self.recordings_dir, audio_filename)
            
            # Combine all audio frames
            audio_data = np.concatenate(self.frames, axis=0)
            
            # Save as WAV file
            with wave.open(audio_filepath, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16))
            
            # Process audio with external function
            self.update_status('Converting speech to video...')
            video_path = self.speech_to_video_function(audio_filepath)
            print(video_path)
            Clock.schedule_once(lambda dt: self.play_video(video_path))
            
        except Exception as e:
            self.update_status(f'Error: {str(e)}')
    
    # def play_video(self, video_path):
    #     if os.path.exists(video_path):
    #         self.video_player.source = video_path
    #         self.video_player.state = 'play'
    #         self.update_status('Playing video')
    #     else:
    #         self.update_status('Video file not found')
    def play_video(self, video_path):
        if os.path.exists(video_path):
            self.update_status('Playing video externally...')
            
            # Open video with default player
            if platform.system() == "Windows":
                os.startfile(video_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", video_path])
            else:  # Linux
                subprocess.run(["xdg-open", video_path])
            
            # Schedule deletion after a short delay to allow video to play
            Clock.schedule_once(lambda dt: self.delete_video(video_path), 10)
        else:
            self.update_status('Video file not found')
    def update_status(self, text):
        Clock.schedule_once(lambda dt: self.set_status(text))
    
    def set_status(self, text):
        self.status_label.text = text

class AudioVideoApp(App):
    def build(self):
        # Replace this with your actual function
        def dummy_speech_to_video(audio_path):
            return "path/to/video.mp4"  # Replace with your function
            
        return AudioVideoInterface(main_text)
    def on_stop(self):
        # Delete all video files in the recordings directory on exit
        if os.path.exists(video_path):
            os.remove(video_path)
            print("File deleted successfully")
        else:
            print("File not found")
        for file in os.listdir("recordings"):
            if file.endswith(".mp4"):  # Ensure it's a video file
                os.remove(os.path.join("recordings", file))
                print(f"Deleted: {file}")

if __name__ == '__main__':
    AudioVideoApp().run()