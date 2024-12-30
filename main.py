import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.logger import Logger
import threading
import os
import sys
import traceback
import platform
import bidi.algorithm
from kivy.app import App
from kivy.uix.label import Label
from kivy.core.window import Window

Window.icon = "icon.png"

from app import talk2view

try:
    from jnius import autoclass

    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    FileProvider = autoclass('androidx.core.content.FileProvider')
except ImportError:
    PythonActivity = None
    Intent = None
    Uri = None
    FileProvider = None


class AndroidVideoOpener:
    @staticmethod
    def open_video(video_path):
        if not all([PythonActivity, Intent, Uri, FileProvider]):
            Logger.error('Talk2View: Unable to import Android classes')
            return False

        try:
            full_path = os.path.abspath(video_path)

            if not os.path.exists(full_path):
                Logger.error(f'Talk2View: Video file not found at {full_path}')
                return False

            activity = PythonActivity.mActivity

            # Create a content URI using FileProvider (Android 7.0+)
            file = autoclass('java.io.File')(full_path)
            context = activity.getApplicationContext()

            # Use FileProvider to get content URI
            content_uri = FileProvider.getUriForFile(
                context,
                f"{context.getPackageName()}.fileprovider",
                file
            )

            # Create an intent to view the video
            intent = Intent(Intent.ACTION_VIEW)

            # Set the data and type for video
            intent.setDataAndType(content_uri, "video/*")

            # Add read permissions flag
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            # Start the activity
            activity.startActivity(intent)

            return True

        except Exception as e:
            Logger.error(f'Talk2View: Android video open error: {str(e)}')
            return False


class GradientButton(Button):
    """Custom button with gradient background"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = [0, 0, 0, 0]  # Transparent
        self.background_normal = ''
        self.bind(size=self.draw_gradient, pos=self.draw_gradient)

    def draw_gradient(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Blue to Green gradient
            Color(*get_color_from_hex('#4A90E2'))  # Start color
            self.rect1 = Rectangle(pos=self.pos, size=(self.width / 2, self.height))

            Color(*get_color_from_hex('#50C878'))  # End color
            self.rect2 = Rectangle(pos=(self.pos[0] + self.width / 2, self.pos[1]),
                                   size=(self.width / 2, self.height))


class Talk2ViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_path = "output.mp4"  # Set the video path
        self.video_popup = None
        self.converter = None

    def build(self):
        self.title = "تكلّم حتّى أراك"
        # Set up the main window
        Window.clearcolor = get_color_from_hex('#F5F5F5')  # Light gray background
        Window.size = (380, 650)  # Slightly larger mobile-like size

        # Create the main layout
        main_layout = FloatLayout()

        # Card-like container with elevation effect
        card = BoxLayout(
            orientation='vertical',
            size_hint=(0.92, 0.92),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            padding=dp(25),
            spacing=dp(15)
        )

        # Add white background to card with shadow effect
        with card.canvas.before:
            Color(1, 1, 1, 1)  # White background
            self.card_rect = Rectangle(pos=card.pos, size=card.size)
            # Add a subtle shadow
            Color(0.8, 0.8, 0.8, 0.3)
            self.shadow_rect = Rectangle(pos=(card.pos[0] - dp(5), card.pos[1] - dp(5)),
                                         size=(card.size[0] + dp(10), card.size[1] + dp(10)))
        card.bind(pos=self.update_card_rect, size=self.update_card_rect)

        # Title Label with more styling
        title_label = Label(
            text='Talk2View\nSign Language Converter',
            font_size='24sp',
            color=get_color_from_hex('#2C3E50'),
            bold=True,
            size_hint_y=None,
            height=dp(300)
        )
        card.add_widget(title_label)

        # Language Spinner with improved styling
        self.language_spinner = Spinner(
            text='Select Language',
            values=('English', 'Arabic'),
            size_hint=(1, None),
            height=dp(50),
            background_color=get_color_from_hex('#ECF0F1')
        )
        card.add_widget(self.language_spinner)

        # Start Recording Button
        self.start_btn = GradientButton(
            text='Start Recording',
            size_hint=(1, None),
            height=dp(50)
        )
        self.start_btn.bind(on_press=self.start_speech_conversion)
        card.add_widget(self.start_btn)

        # Stop Button
        self.stop_btn = Button(
            text='Stop Recording',
            background_color=get_color_from_hex('#E74C3C'),
            color=get_color_from_hex('#FFFFFF'),
            size_hint=(1, None),
            height=dp(50),
            disabled=True
        )
        self.stop_btn.bind(on_press=self.stop_conversion)
        card.add_widget(self.stop_btn)

        # Text to Sign Language Button
        text_to_sign_btn = GradientButton(
            text='Text to Sign Language',
            size_hint=(1, None),
            height=dp(50),
        )
        text_to_sign_btn.bind(on_press=self.start_text_conversion)
        card.add_widget(text_to_sign_btn)

        # Add card to main layout
        main_layout.add_widget(card)

        return main_layout

    def update_card_rect(self, instance, value):
        self.card_rect.pos = instance.pos
        self.card_rect.size = instance.size
        # Update shadow rect to match card with offset
        self.shadow_rect.pos = (instance.pos[0] - dp(5), instance.pos[1] - dp(5))
        self.shadow_rect.size = (instance.size[0] + dp(10), instance.size[1] + dp(10))

    def start_speech_conversion(self, instance):
        try:
            # Validate language selection
            if self.language_spinner.text == 'Select Language':
                self.show_error_popup('Please select a language first.')
                Logger.error('Talk2View: No language selected')
                return

            # Disable the Start button
            self.start_btn.disabled = True
            self.stop_btn.disabled = False

            # Create an instance of talk2view
            self.converter = talk2view()

            # Set language based on spinner selection
            if self.language_spinner.text == "Arabic":
                self.converter.lang = 'ar-EG'
                self.converter.sign_language_words_folder = f'sign language words/ar-EG'
            elif self.language_spinner.text == "English":
                self.converter.lang = 'en-US'
                self.converter.sign_language_words_folder = f'sign language words/en-US'

            # Use a separate thread to prevent the UI from freezing
            thread = threading.Thread(target=self.run_conversion, daemon=True)
            thread.start()

        except Exception as e:
            error_msg = f'Error starting conversion: {str(e)}'
            Logger.error(f'Talk2View: {error_msg}')
            print(f'ERROR: {error_msg}', file=sys.stderr)
            traceback.print_exc()
            self.show_error_popup(error_msg)
            self.reset_buttons()

    def run_conversion(self):
        try:
            if self.converter:
                self.converter.start(self.converter.lang)

                # Check if video was generated
                if os.path.exists(self.video_path):
                    # Open the generated video
                    self.open_video_popup()
                else:
                    raise FileNotFoundError("Generated video not found.")

        except Exception as e:
            error_msg = f'Conversion error: {str(e)}'
            Logger.error(f'Talk2View: {error_msg}')
            print(f'ERROR: {error_msg}', file=sys.stderr)
            traceback.print_exc()

            # Use Clock to show popup on main thread
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.show_error_popup(error_msg))

            # Reset buttons
            Clock.schedule_once(lambda dt: self.reset_buttons())

    def open_video_popup(self):
        try:
            # Verify video path
            if not os.path.exists(self.video_path):
                self.show_error_popup('Video file not found.')
                Logger.error(f'Talk2View: Video not found at {self.video_path}')
                return

            # Try Android-specific method first
            if PythonActivity and AndroidVideoOpener.open_video(self.video_path):
                self.reset_buttons()
                return

            # Fallback for other platforms
            system = platform.system()

            if system == 'Darwin':  # macOS
                import subprocess
                subprocess.call(('open', self.video_path))
            elif system == 'Windows':
                os.startfile(self.video_path)
            else:  # Linux and others
                import subprocess
                subprocess.call(('xdg-open', self.video_path))

            self.reset_buttons()

        except Exception as e:
            error_msg = f'Video display error: {str(e)}'
            Logger.error(f'Talk2View: {error_msg}')
            self.show_error_popup(error_msg)

    def start_text_conversion(self, instance):
        try:
            # Validate language selection
            if self.language_spinner.text == 'Select Language':
                self.show_error_popup('Please select a language first.')
                Logger.error('Talk2View: No language selected for text conversion')
                return

            # Create an instance of talk2view
            converter = talk2view()

            # Set language based on spinner selection
            converter.lang = 'ar-EG' if self.language_spinner.text == 'Arabic' else 'en-US'

            # Text input popup
            content = BoxLayout(orientation='vertical', spacing=dp(10))
            text_input = TextInput(
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                hint_text='Enter text to convert'
            )
            submit_btn = Button(
                text='Convert',
                size_hint_y=None,
                height=dp(50),
                background_color=get_color_from_hex('#2ECC71'),
                color=get_color_from_hex('#FFFFFF')
            )

            content.add_widget(text_input)
            content.add_widget(submit_btn)

            popup = Popup(
                title='Text to Sign Language',
                content=content,
                size_hint=(0.8, 0.3)
            )

            def on_submit(instance):
                if not text_input.text.strip():
                    self.show_error_popup('Please enter some text.')
                    Logger.error('Talk2View: Empty text input')
                    return

                try:
                    # Convert text to sign language video
                    arabic_text = text_input.text
                    converter.text_to_sign_language_video(text_input.text)

                    # Open the generated video
                    self.open_video_popup()

                    # Close text input popup
                    popup.dismiss()

                except Exception as e:
                    error_msg = f'Text conversion error: {str(e)}'
                    Logger.error(f'Talk2View: {error_msg}')
                    print(f'ERROR: {error_msg}', file=sys.stderr)
                    traceback.print_exc()
                    self.show_error_popup(error_msg)

            submit_btn.bind(on_press=on_submit)
            popup.open()

        except Exception as e:
            error_msg = f'Error in text conversion: {str(e)}'
            Logger.error(f'Talk2View: {error_msg}')
            print(f'ERROR: {error_msg}', file=sys.stderr)
            traceback.print_exc()
            self.show_error_popup(error_msg)

    def stop_conversion(self, instance):
        try:
            # Call the stop function
            if self.converter:
                self.converter.stop()
            self.reset_buttons()
            Logger.info('Talk2View: Conversion stopped by user')
        except Exception as e:
            error_msg = f'Error stopping conversion: {str(e)}'
            Logger.error(f'Talk2View: {error_msg}')
            print(f'ERROR: {error_msg}', file=sys.stderr)
            traceback.print_exc()
            self.show_error_popup(error_msg)

    def reset_buttons(self):
        # Run on main thread to avoid Kivy threading issues
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._reset_buttons_impl())

    def _reset_buttons_impl(self):
        self.start_btn.disabled = False
        self.stop_btn.disabled = True

    def show_error_popup(self, message):
        # Run on main thread to avoid Kivy threading issues
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._show_error_popup(message))

    def _show_error_popup(self, message):
        popup = Popup(
            title='Error',
            content=Label(
                text=message,
                text_size=(None, None),
                halign='center',
                valign='center'
            ),
            size_hint=(0.8, 0.3)
        )
        popup.open()


def run_app():
    try:
        Talk2ViewApp().run()
    except Exception as e:
        Logger.error(f'Talk2View App Fatal Error: {str(e)}')
        print(f'FATAL ERROR: {str(e)}', file=sys.stderr)
        traceback.print_exc()


if __name__ == '__main__':
    run_app()