import os
from moviepy import VideoFileClip, ImageClip, concatenate_videoclips
import cv2
import numpy as np

class SignLanguageCompiler:
    def __init__(self, signs_directory):
        self.signs_dir = signs_directory
        self.supported_extensions = {'.mp4', '.jpg', '.png', '.gif'}
        
    def find_file(self, name):
        name = name.capitalize()
        for ext in self.supported_extensions:
            path = os.path.join(self.signs_dir, f"{name}{ext}")
            if os.path.exists(path):
                return path
        return None
    
    def create_clip(self, file_path, duration=1.0):
        if file_path.endswith('.mp4'):
            clip = VideoFileClip(file_path)
        else:
            clip = ImageClip(file_path).set_duration(duration)
        return clip
    
    def spell_word(self, word):
        letter_clips = []
        for letter in word:
            if letter.isalpha():
                letter_path = self.find_file(letter)
                if letter_path is None:
                    raise ValueError(f"Letter not found: {letter}")
                clip = self.create_clip(letter_path, duration=0.5)
                letter_clips.append(clip)
        return concatenate_videoclips(letter_clips) if letter_clips else None
    
    def compile_sentence(self, sentence, output_path):
        words = ''.join(c for c in sentence if c.isalnum() or c.isspace()).split()
        
        clips = []
        for word in words:
            sign_path = self.find_file(word)
            if sign_path:
                # Use existing sign video/image
                clip = self.create_clip(sign_path)
            else:
                # Spell out the word
                clip = self.spell_word(word)
            if clip:  # Only add if we successfully created a clip
                clips.append(clip)
        
        if not clips:
            raise ValueError("No valid clips were created")
        final_video = concatenate_videoclips(clips)
        
        # Write the final video
        final_video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio=False
        )
        final_video.close()
        for clip in clips:
            clip.close()

def main_sign(text):
    compiler = SignLanguageCompiler(signs_directory="signs/")
    for i in range(10):
        print(text)
    sentence = "I have an Apple"
    compiler.compile_sentence(text, "output_sign_language.mp4")
    return "output_sign_language.mp4"

if __name__ == "__main__":
    main_sign()