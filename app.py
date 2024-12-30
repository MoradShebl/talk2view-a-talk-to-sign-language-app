import speech_recognition as sr
import keyboard
import wave
import cv2
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess
from speech_recognition import Recognizer
import sounddevice as sd



class talk2view():
    def __init__(self):
        self.lang = 'ar-EG'
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024
        self.OUTPUT_FILENAME = f"output.wav"

        self.sign_language_folder = "sign_language_images"
        self.space_image_path = os.path.join(self.sign_language_folder, "space.jpg")  # Define space image
        self.sign_language_words_folder = f'sign language words/{self.lang}'

        self.recognizing = False

    def start(self, lang):
        self.record_audio()
        text = self.recognize_audio(self.OUTPUT_FILENAME, lang)
        self.text_to_sign_language_video(text)

    def stop(self):
        global recognizing
        self.recognizing = False
        print("Stop function called.")

    def record_audio(self):
        self.recognizing = True
        print("Recording... Press 'q' to stop or call stop().")

        # Ensure frames is properly initialized as a list
        frames = []

        # Define a callback function to process audio data
        def callback(indata, frames_per_buffer, time_info, status):
            if status:
                print(f"Stream status: {status}")
            if self.recognizing and not keyboard.is_pressed('q'):
                # Append audio data to the frames list
                frames.append(indata.copy())
            else:
                # Stop the callback by raising a Stop exception
                self.recognizing = False
                raise sd.CallbackStop()

        # Define audio parameters
        self.FORMAT = 'float32'  # Use 'float32' as default format for sounddevice
        self.CHANNELS = 1
        self.RATE = 44100

        try:
            # Open an audio stream
            with sd.InputStream(
                    samplerate=self.RATE,
                    channels=self.CHANNELS,
                    dtype=self.FORMAT,
                    callback=callback
            ):
                # Block while recording
                while self.recognizing:
                    sd.sleep(100)
        except Exception as e:
            print(f"Error during recording: {e}")

        # Convert frames to a NumPy array for saving
        audio_data = np.concatenate(frames, axis=0)

        # Save the audio data to a WAV file
        with wave.open(self.OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)  # 2 bytes for int16
            wf.setframerate(self.RATE)
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())

        print(f"Audio saved as {self.OUTPUT_FILENAME}")

    def recognize_audio(self, audio, lang="ar-EG"):
        recognizer: Recognizer = sr.Recognizer()
        audio_file = sr.AudioFile(audio)

        with audio_file as source:
            audio_data = recognizer.record(source)

        try:
            print("Recognizing speech...")
            transcript = recognizer.recognize_google(audio_data, language=lang)
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
            transcript = ""
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            transcript = ""

        print("Recognized text:", transcript)
        return transcript


    def arabic_to_number(self, letter):
        mapping = {
            'ا': '1', 'أ': '1', 'إ': '1', 'آ': '1',
            'ب': '2', 'ت': '3', 'ث': '4', 'ج': '5',
            'ح': '6', 'خ': '7', 'د': '8', 'ذ': '9',
            'ر': '10', 'ز': '11', 'س': '12', 'ش': '13',
            'ص': '14', 'ض': '15', 'ط': '16', 'ظ': '17',
            'ع': '18', 'غ': '19', 'ف': '20', 'ق': '21',
            'ك': '22', 'ل': '23', 'م': '24', 'ن': '25',
            'ه': '26', 'ة': '26', 'و': '27', 'ي': '28',
            '0': '29', '1': '30', '2': '31', '3': '32',
            '4': '33', '5': '34', '6': '35', '7': '36',
            '8': '37', '9': '38',
            'A': '39', 'a': '39', 'B': '40', 'b': '40',
            'C': '41', 'c': '41', 'D': '42', 'd': '42',
            'E': '43', 'e': '43', 'F': '44', 'f': '44',
            'G': '45', 'g': '45', 'H': '46', 'h': '46',
            'I': '47', 'i': '47', 'J': '48', 'j': '48',
            'K': '49', 'k': '49', 'L': '50', 'l': '50',
            'M': '51', 'm': '51', 'N': '52', 'n': '52',
            'O': '53', 'o': '53', 'P': '54', 'p': '54',
            'Q': '55', 'q': '55', 'R': '56', 'r': '56',
            'S': '57', 's': '57', 'T': '58', 't': '58',
            'U': '59', 'u': '59', 'V': '60', 'v': '60',
            'W': '61', 'w': '61', 'X': '62', 'x': '62',
            'Y': '63', 'y': '63', 'Z': '64', 'z': '64'
        }
        return mapping.get(letter, None)

    def word_to_number(self, word):
        if self.lang == 'ar-EG':
            mapping = {
                'مرحبا': '1',
                'احبك': '2',
                'لا': '3',
                'موافق': '4',
                'سؤال': '5',
                'انت': '6',
                'اقتباس': '7',
                'اضحكتني': '8'
            }
            return mapping.get(word, None)
        elif self.lang == "en-US":  #####i will drive and eat and drink and stop sleep and play
            mapping = {
                'drive': '1',
                'eat': '2',
                'drink': '3',
                'stop': '4',
                'sleep': '5',
                'play': '6',
                'go': '7'
            }
            return mapping.get(word, None)



    def overlay_arabic_text(self, image, text='', position=(50, 100), font_path="arial.ttf", font_size=60, color=(0, 0, 0)):
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        font = ImageFont.truetype(font_path, font_size)
        draw.text(position, text, font=font, fill=color)
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


    def search_all(self):
        folder_path = f"sign language words/{self.lang}"
        files_list = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                files_list.append(file)

        return files_list


    def text_to_sign_language_video(self, text):
        words = text.split()
        fps = 3  # decrease to slower

        base_name = os.path.splitext(f'output.avi')[0]
        mp4_file_path = f"{base_name}.mp4"

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(mp4_file_path, fourcc, fps, (640, 480))  # Increased frame rate

        for word in words:

            if f"{self.word_to_number(word)}.jpg" not in self.search_all():

                for letter in word:
                    letter_image_path = os.path.join(self.sign_language_folder, f"{self.arabic_to_number(letter)}.jpg")

                    if os.path.exists(letter_image_path):
                        letter_image = cv2.imread(letter_image_path)
                        letter_image = self.overlay_arabic_text(
                            image=letter_image,
                            text=letter,
                            position=(420, 20),
                            font_path="C:/Windows/Fonts/arial.ttf",
                            font_size=80,
                            color=(0, 0, 0),
                        )
                        letter_image_resized = cv2.resize(letter_image, (640, 480))
                        video_writer.write(letter_image_resized)
                    else:
                        print(f"Image for '{letter}' not found.")
                        blank_image = 255 * np.ones((480, 640, 3), dtype=np.uint8)
                        blank_image = self.overlay_arabic_text(
                            image=blank_image,
                            text=letter,
                            position=(200, 200),
                            font_path="C:/Windows/Fonts/arial.ttf",
                            font_size=80,
                            color=(0, 0, 0),
                        )
                        video_writer.write(blank_image)

            elif f"{self.word_to_number(word)}.jpg" in self.search_all():
                word_image_path = self.sign_language_words_folder + '/' + f"{self.word_to_number(word)}.jpg"
                print(f"found the word path is {word_image_path}")

                if os.path.exists(word_image_path):
                    word_image = cv2.imread(word_image_path)
                    word_image = self.overlay_arabic_text(
                        image=word_image,
                        position=(420, 20),
                        font_path="C:/Windows/Fonts/arial.ttf",
                        font_size=80,
                        color=(0, 0, 0),
                    )
                    letter_image_resized = cv2.resize(word_image, (640, 480))
                    video_writer.write(letter_image_resized)
                else:
                    print(f"Image for '{word}.jpg' not found.")
                    blank_image = 255 * np.ones((480, 640, 3), dtype=np.uint8)
                    blank_image = self.overlay_arabic_text(
                        image=blank_image,
                        text=word,
                        position=(200, 200),
                        font_path="C:/Windows/Fonts/arial.ttf",
                        font_size=80,
                        color=(0, 0, 0),
                    )
                    video_writer.write(blank_image)

            if os.path.exists(self.space_image_path):
                space_image = cv2.imread(self.space_image_path)
                space_image_resized = cv2.resize(space_image, (640, 480))
                video_writer.write(space_image_resized)

        video_writer.release()
        print(f"Sign language video created successfully as {mp4_file_path}!")

    def display_video(self, video_path):
        subprocess.run(['open', video_path], check=True) if os.name == 'posix' else subprocess.run(['start', video_path], shell=True, check=True)

############################################################ Terminal Control #########################################
    def terminal(self):
        global lang
        while True:
            choice = input("ماذا تريد؟ \n 1/من الكلام الي لغه اشاره \n 2/من نص الي لفه اشاره\n 3/تغيير اللغه \n 4/الخروج \n")

            if choice == '1':
                self.start(self.lang)
            elif choice == '2':
                transscript = input(f"اللغه هي {self.lang} اكتب ما تريد تغيره الي لغه اشاره: ")
                self.text_to_sign_language_video(transscript)

            elif choice == '3':
                languages_choose = input(f"اختر لغتك هناك العربية (1) و الإنجليزية (2) الافتراضي هو {self.lang} ")
                if languages_choose == '1':
                    self.lang = "ar-EG"
                    self.sign_language_words_folder = f'sign language words/ar-EG'
                elif languages_choose == '2':
                    self.lang = "en-US"
                    self.sign_language_words_folder = f'sign language words/en-US'
                print(f"language now is {self.lang}")
                print(f"sign language folder now is {self.sign_language_words_folder}")

            elif choice == '4':
                break
############################################################ Terminal Control #########################################
if __name__ == "__main__":
    talk2view = talk2view()
    talk2view.terminal()