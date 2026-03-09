from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit,
    QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSizeGrip, QSizePolicy, QDesktopWidget, QCheckBox, QProgressBar
)
from PyQt5.QtCore import QObject, Qt, QSize, QTimer, QEvent, QThread, pyqtSignal, QMutex
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat, QTextCursor
from dotenv import dotenv_values
import sys
import os
import time
import threading
import json
import subprocess
import psutil
from collections import deque

# Thread-safe initialization
_file_mutex = QMutex()

# Global monitoring variables
mic_frequency_history = deque(maxlen=50)  # Store last 50 frequency readings
current_mic_frequency = 0

# Environment setup with error handling
try:
    env_vars = dotenv_values(".env")
    if not env_vars:
        # Try alternative paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        env_path = os.path.join(project_root, ".env")
        if os.path.exists(env_path):
            env_vars = dotenv_values(env_path)
        else:
            env_vars = {}
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    env_vars = {}

Assistantname = env_vars.get("Assistantname", "Jarvis")
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
old_chat_message = ""

# Create paths with proper error handling
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
GraphicsDirPath = os.path.join(current_dir, "Frontend", "Graphics")

# Ensure directories exist
try:
    os.makedirs(TempDirPath, exist_ok=True)
    os.makedirs(GraphicsDirPath, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create directories: {e}")
    # Fallback to current directory
    TempDirPath = os.path.join(os.getcwd(), "Files")
    GraphicsDirPath = os.path.join(os.getcwd(), "Graphics")
    os.makedirs(TempDirPath, exist_ok=True)
    os.makedirs(GraphicsDirPath, exist_ok=True)

# --- Utility functions -----------------------------------------------------
def AnswerModifier(Answer):
    """Remove empty lines from answer text"""
    try:
        if not Answer:
            return ""
        lines = str(Answer).split("\n")
        non_empty_lines = [line for line in lines if line.strip()]
        modified_answer = "\n".join(non_empty_lines)
        return modified_answer
    except Exception as e:
        print(f"Error in AnswerModifier: {e}")
        return str(Answer) if Answer else ""

def QueryModifier(Query):
    """Format query with proper punctuation and capitalization"""
    try:
        new_query = (Query or "").lower().strip()
        if new_query == "":
            return ""

        query_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "can you", "what's", "where's", "how's"]
        # decide punctuation
        if any(word in new_query for word in query_words):
            if new_query and new_query[-1] in ['.', ',', '?', '!']:
                new_query = new_query[:-1] + "?"
            else:
                new_query += "?"
        else:
            if new_query and new_query[-1] in ['.', ',', '?', '!']:
                new_query = new_query[:-1] + "."
            else:
                new_query += "."
        return new_query.capitalize()
    except Exception as e:
        print(f"Error in QueryModifier: {e}")
        return str(Query) if Query else ""

def SetMicrophoneStatus(Command):
    # --- MODIFIED --- Use mutex for thread-safe file access
    _file_mutex.lock()
    try:
        os.makedirs(TempDirPath, exist_ok=True)
        with open(rf'{TempDirPath}\Mic.data', "w", encoding='utf-8') as file:
            file.write(str(Command))
    except Exception as e:
        print(f"Error setting microphone status: {e}")
    finally:
        _file_mutex.unlock()

def GetMicrophoneStatus():
    # --- MODIFIED --- Use mutex for thread-safe file access
    _file_mutex.lock()
    try:
        with open(rf'{TempDirPath}\Mic.data', "r", encoding='utf-8') as file:
            Status = file.read()
    except FileNotFoundError:
        Status = "False"
    finally:
        _file_mutex.unlock()
    return Status

def SetAssistantStatus(Status):
    # --- MODIFIED --- Use mutex for thread-safe file access
    _file_mutex.lock()
    try:
        os.makedirs(TempDirPath, exist_ok=True)
        with open(rf'{TempDirPath}\Status.data', "w", encoding='utf-8') as file:
            file.write(str(Status))
    except Exception as e:
        print(f"Error setting assistant status: {e}")
    finally:
        _file_mutex.unlock()

def GetAssistantStatus():
    # --- MODIFIED --- Use mutex for thread-safe file access
    _file_mutex.lock()
    try:
        with open(rf'{TempDirPath}\Status.data', "r", encoding='utf-8') as file:
            Status = file.read()
    except FileNotFoundError:
        Status = ""
    finally:
        _file_mutex.unlock()
    return Status

def MicButtonInitialed():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")

def GraphicsDirectoryPath(Filename):
    return rf'{GraphicsDirPath}\{Filename}'

def TempDirectoryPath(Filename):
    return rf'{TempDirPath}\{Filename}'

def ShowTextToScreen(Text):
    # --- MODIFIED --- Use mutex for thread-safe file access
    _file_mutex.lock()
    try:
        os.makedirs(TempDirPath, exist_ok=True)
        with open(rf'{TempDirPath}\Responses.data', "w", encoding='utf-8') as file:
            file.write(str(Text))
    except Exception as e:
        print(f"Error showing text to screen: {e}")
    finally:
        _file_mutex.unlock()

# --- System Monitoring Functions ---
def get_wifi_status():
    """Get current WiFi connection status"""
    try:
        # Windows command to check WiFi status
        result = subprocess.run(['netsh', 'wlan', 'show', 'profiles'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and "Profile" in result.stdout:
            # Check if currently connected
            result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                  capture_output=True, text=True, timeout=5)
            if "State" in result.stdout and "connected" in result.stdout.lower():
                return True
        return False
    except Exception as e:
        print(f"Error checking WiFi status: {e}")
        return False

def get_bluetooth_status():
    """Get current Bluetooth status"""
    try:
        # PowerShell command to check Bluetooth status
        ps_command = 'Get-WmiObject -Class Win32_PnPEntity | Where-Object {$_.Name -like "*Bluetooth*"} | Select-Object Status'
        result = subprocess.run(['powershell', '-Command', ps_command], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and "OK" in result.stdout:
            return True
        return False
    except Exception as e:
        print(f"Error checking Bluetooth status: {e}")
        return False

def get_microphone_frequency():
    """Get real-time microphone frequency/activity level"""
    global current_mic_frequency, mic_frequency_history
    try:
        import pyaudio
        import numpy as np
        
        # Audio parameters
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        p = pyaudio.PyAudio()
        
        # Open microphone stream
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)
        
        # Read audio data
        data = stream.read(CHUNK, exception_on_overflow=False)
        
        # Convert to numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # Calculate frequency/amplitude
        frequency = np.fft.fft(audio_data)
        magnitude = np.abs(frequency)
        
        # Get dominant frequency
        dominant_freq = np.argmax(magnitude)
        freq_hz = dominant_freq * RATE // CHUNK
        
        # Calculate volume/activity level
        volume = np.sqrt(np.mean(audio_data**2))
        
        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Update global variables
        current_mic_frequency = min(freq_hz, 1000)  # Cap at 1000 Hz for display
        mic_frequency_history.append(current_mic_frequency)
        
        return current_mic_frequency, volume
        
    except Exception as e:
        print(f"Error getting microphone frequency: {e}")
        return 0, 0

def is_microphone_active():
    """Check if microphone is currently active and working"""
    try:
        # Check if microphone status file says it's on
        mic_status = GetMicrophoneStatus()
        if mic_status != "True":
            return False
            
        # Try to access microphone hardware
        import pyaudio
        p = pyaudio.PyAudio()
        
        # Check if any microphone device is available
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # Has input capability
                try:
                    # Test if we can open the device
                    stream = p.open(format=pyaudio.paInt16,
                                   channels=1,
                                   rate=44100,
                                   input=True,
                                   input_device_index=i,
                                   frames_per_buffer=1024)
                    stream.close()
                    p.terminate()
                    return True
                except:
                    continue
        
        p.terminate()
        return False
        
    except Exception as e:
        print(f"Error checking microphone: {e}")
        return False


# --- System Monitoring Widget ---
class SystemMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.setup_timer()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel("🔍 System Monitor")
        title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Microphone Status Section
        mic_frame = QFrame()
        mic_frame.setFrameStyle(QFrame.Box)
        mic_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 5px; background-color: #1a1a1a; }")
        mic_layout = QVBoxLayout(mic_frame)
        
        # Microphone checkbox
        self.mic_checkbox = QCheckBox("🎤 Microphone Active")
        self.mic_checkbox.setStyleSheet("color: white; font-size: 12px;")
        self.mic_checkbox.setEnabled(False)  # Read-only status indicator
        mic_layout.addWidget(self.mic_checkbox)
        
        # Microphone frequency display
        self.mic_freq_label = QLabel("Frequency: 0 Hz")
        self.mic_freq_label.setStyleSheet("color: #888; font-size: 10px;")
        mic_layout.addWidget(self.mic_freq_label)
        
        # Microphone activity bar
        self.mic_activity_bar = QProgressBar()
        self.mic_activity_bar.setMaximum(100)
        self.mic_activity_bar.setValue(0)
        self.mic_activity_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 3px;
                background-color: #2a2a2a;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        mic_layout.addWidget(self.mic_activity_bar)
        
        layout.addWidget(mic_frame)
        
        # WiFi Status Section
        wifi_frame = QFrame()
        wifi_frame.setFrameStyle(QFrame.Box)
        wifi_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 5px; background-color: #1a1a1a; }")
        wifi_layout = QVBoxLayout(wifi_frame)
        
        self.wifi_checkbox = QCheckBox("📶 WiFi Connected")
        self.wifi_checkbox.setStyleSheet("color: white; font-size: 12px;")
        self.wifi_checkbox.setEnabled(False)  # Read-only status indicator
        wifi_layout.addWidget(self.wifi_checkbox)
        
        layout.addWidget(wifi_frame)
        
        # Bluetooth Status Section
        bt_frame = QFrame()
        bt_frame.setFrameStyle(QFrame.Box)
        bt_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 5px; background-color: #1a1a1a; }")
        bt_layout = QVBoxLayout(bt_frame)
        
        self.bluetooth_checkbox = QCheckBox("🔷 Bluetooth Active")
        self.bluetooth_checkbox.setStyleSheet("color: white; font-size: 12px;")
        self.bluetooth_checkbox.setEnabled(False)  # Read-only status indicator
        bt_layout.addWidget(self.bluetooth_checkbox)
        
        layout.addWidget(bt_frame)
        
        # Set widget size
        self.setFixedWidth(200)
        self.setFixedHeight(200)
        
    def setup_timer(self):
        """Setup timer for real-time monitoring"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # Update every 1 second
        
    def update_status(self):
        """Update all system status indicators"""
        try:
            # Update microphone status
            mic_active = is_microphone_active()
            self.mic_checkbox.setChecked(mic_active)
            
            if mic_active:
                self.mic_checkbox.setStyleSheet("color: #4CAF50; font-size: 12px;")
                # Get microphone frequency
                try:
                    freq, volume = get_microphone_frequency()
                    self.mic_freq_label.setText(f"Frequency: {freq:.0f} Hz")
                    # Update activity bar based on volume
                    activity_level = min(100, int(volume / 100))
                    self.mic_activity_bar.setValue(activity_level)
                except:
                    self.mic_freq_label.setText("Frequency: -- Hz")
                    self.mic_activity_bar.setValue(0)
            else:
                self.mic_checkbox.setStyleSheet("color: #f44336; font-size: 12px;")
                self.mic_freq_label.setText("Frequency: -- Hz")
                self.mic_activity_bar.setValue(0)
            
            # Update WiFi status
            wifi_active = get_wifi_status()
            self.wifi_checkbox.setChecked(wifi_active)
            if wifi_active:
                self.wifi_checkbox.setStyleSheet("color: #4CAF50; font-size: 12px;")
            else:
                self.wifi_checkbox.setStyleSheet("color: #f44336; font-size: 12px;")
            
            # Update Bluetooth status
            bt_active = get_bluetooth_status()
            self.bluetooth_checkbox.setChecked(bt_active)
            if bt_active:
                self.bluetooth_checkbox.setStyleSheet("color: #4CAF50; font-size: 12px;")
            else:
                self.bluetooth_checkbox.setStyleSheet("color: #f44336; font-size: 12px;")
                
        except Exception as e:
            print(f"Error updating system monitor: {e}")

# --- Audio Visualization Widget ---
class AudioVisualizationWidget(QWidget):
    """Audio visualization widget that shows animation when microphone is active"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.setup_timers()
        
    def initUI(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create a container for the audio visualization
        self.visualization_label = QLabel()
        self.visualization_label.setAlignment(Qt.AlignCenter)
        self.visualization_label.setStyleSheet("border: none; background: transparent;")
        
        # Load the audio.gif as audio visualization (with transparent background)
        gif_path = "f:/audio.gif"
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.movie.setScaledSize(QSize(400, 150))  # Appropriate size for home screen bottom
            self.visualization_label.setMovie(self.movie)
            self.movie.start()
        else:
            # Fallback if gif doesn't exist - show animated bars
            self.movie = None
            self.visualization_label.setText("🎤")
            self.visualization_label.setStyleSheet("""
                color: #4CAF50;
                font-size: 48px;
                background: transparent;
            """)
        
        layout.addWidget(self.visualization_label)
        
        # Set initial appearance (hidden) and transparent background
        self.setVisible(False)
        self.setMaximumHeight(160)
        self.setStyleSheet("background: transparent; border: none;")
        
    def setup_timers(self):
        # Timer to update visualization
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_microphone_status)
        self.update_timer.start(500)  # Check every 500ms
        
    def check_microphone_status(self):
        """Check if microphone is active and show/hide accordingly"""
        try:
            mic_status = GetMicrophoneStatus()
            if mic_status == "True":
                # Microphone is ON - show visualization
                if not self.isVisible():
                    self.setVisible(True)
                    if self.movie:
                        self.movie.start()
            else:
                # Microphone is OFF - hide visualization
                if self.isVisible():
                    self.setVisible(False)
                    if self.movie:
                        self.movie.stop()
        except Exception as e:
            print(f"Error checking mic status in audio widget: {e}")

# --- Widgets ----------------------------------------------------------------
class ChatSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(-10, 40, 40, 100)
        layout.setSpacing(-10)

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        self.chat_text_edit.setStyleSheet("background-color: black;")
        layout.addWidget(self.chat_text_edit)

        layout.setStretch(0, 1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        text_color = QColor(Qt.blue)
        text_color_text = QTextCharFormat()
        text_color_text.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_color_text)

        self.gif_label = QLabel()
        gif_path = GraphicsDirectoryPath("Jarvis.gif")
        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            max_gif_size_W = 480
            max_gif_size_H = 270
            movie.setScaledSize(QSize(max_gif_size_W, max_gif_size_H))
            self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
            self.gif_label.setMovie(movie)
            movie.start()
        else:
            # Fallback if gif doesn't exist
            self.gif_label.setText("Assistant")
            self.gif_label.setStyleSheet("color: white; font-size: 24px; text-align: center;")
            self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        layout.addWidget(self.gif_label)

        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size:16px; margin-right: 195px; border: none; margin-top: -30px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)

        # Add chat input section
        self.chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
        self.chat_input.setPlaceholderText("Type your message here...")
        self.chat_input.returnPressed.connect(self.send_message)  # Enter key to send
        
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        self.chat_input_layout.addWidget(self.chat_input)
        self.chat_input_layout.addWidget(self.send_button)
        
        # Create a container widget for the input section
        input_container = QWidget()
        input_container.setLayout(self.chat_input_layout)
        input_container.setStyleSheet("background-color: black;")
        input_container.setFixedHeight(60)
        
        layout.addWidget(input_container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.start(100)  # Refresh every 100ms for faster updates
        
        # Add status update timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.updateStatus)
        self.status_timer.start(100)  # Update status every 100ms
        
        # Ensure auto-scroll is always active
        self.auto_scroll_timer = QTimer(self)
        self.auto_scroll_timer.timeout.connect(self.scrollToBottom)
        self.auto_scroll_timer.start(500)  # Auto-scroll every 500ms

        self.chat_text_edit.viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        # Handle scroll events and other events for the chat text edit
        if event.type() == QEvent.Wheel:
            # Allow scrolling in the chat area
            return False
        return super().eventFilter(source, event)

    def updateStatus(self):
        # Update the status label with current speech recognition text
        self.SpeechRecogText()

        self.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical {
                background: black;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::sub-line:vertical {
                background: black;
                subcontrol-position: top;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                color: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    def loadMessages(self):
        global old_chat_message
        # --- MODIFIED --- Use GetMicrophoneStatus for safe file access
        current_mic_status = GetMicrophoneStatus() 
        try:
            # --- MODIFIED --- Use _file_mutex for thread-safe file access
            _file_mutex.lock()
            with open(TempDirectoryPath('Responses.data'), "r", encoding='utf-8') as file:
                messages = file.read()
        except FileNotFoundError:
            messages = ""
        finally:
            _file_mutex.unlock()


        if not messages or messages == "None":
            # Show default chat if no messages, try to load from Chatlog.json
            try:
                chatlog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data', 'Chatlog.json')
                with open(chatlog_path, 'r', encoding='utf-8') as file:
                    chat_history = json.load(file)
                
                if chat_history:  # If there are existing chats
                    chat_display = ""
                    for chat in chat_history:
                        role = "User" if chat["role"] == "user" else Assistantname
                        chat_display += f"{role}: {chat['content']}\n"
                    messages = chat_display
                else:
                    # If chat history is empty, show default
                    messages = f"User: Hello {Assistantname}, How are you?\n{Assistantname}: I am doing well. How may I help you?"
            except (FileNotFoundError, json.JSONDecodeError):
                messages = f"User: Hello {Assistantname}, How are you?\n{Assistantname}: I am doing well. How may I help you?"

        if str(old_chat_message) != str(messages):
            # Clear the existing text and show the new complete conversation
            self.chat_text_edit.clear()
            self.addMessage(message=messages, color='white')
            old_chat_message = messages
            
            # Force scroll to bottom after loading new messages
            QTimer.singleShot(50, self.scrollToBottom)

    def SpeechRecogText(self):
        # --- MODIFIED --- Use GetAssistantStatus for safe file access
        messages = GetAssistantStatus()
        self.label.setText(messages)

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        char_format = QTextCharFormat()
        block_format = QTextBlockFormat()
        block_format.setTopMargin(10)
        block_format.setLeftMargin(10)
        char_format.setForeground(QColor(color))
        
        # Move to end and add message
        cursor.movePosition(QTextCursor.End)
        cursor.setCharFormat(char_format)
        cursor.setBlockFormat(block_format)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)
        
        # Force scroll to the bottom to show the latest message
        scrollbar = self.chat_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Ensure the cursor stays at the end
        cursor.movePosition(QTextCursor.End)
        self.chat_text_edit.setTextCursor(cursor)
        
        # Force update the display
        self.chat_text_edit.update()
        self.chat_text_edit.repaint()
    
    def send_message(self):
        """Handle sending text messages"""
        message = self.chat_input.text().strip()
        if message:
            # Clear the input field
            self.chat_input.clear()
            
            # Process the message (similar to voice commands)
            self.process_text_message(message)
    
    def process_text_message(self, message):
        """Process text message like voice commands"""
        try:
            # Add user message to chat display
            user_message = f"User: {message}"
            self.addMessage(message=user_message, color='white')
            
            # Import the main processing function
            from Main import process_user_query
            import asyncio
            
            # Process the message asynchronously
            def run_async():
                try:
                    # Create a new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(process_user_query(message))
                    loop.close()
                except Exception as e:
                    print(f"Error processing text message: {e}")
                    # Add error response to chat
                    error_message = f"{Assistantname}: Sorry, I encountered an error processing your message."
                    self.addMessage(message=error_message, color='red')
            
            # Run in a separate thread to avoid blocking GUI
            import threading
            thread = threading.Thread(target=run_async, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"Error in process_text_message: {e}")
            error_message = f"{Assistantname}: Sorry, I couldn't process your message."
            self.addMessage(message=error_message, color='red')

    def scrollToBottom(self):
        """Force scroll to the bottom of the chat"""
        scrollbar = self.chat_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        # Ensure cursor is at the end
        cursor = self.chat_text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_text_edit.setTextCursor(cursor)


class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            desktop = QApplication.desktop()
            screen_width = desktop.screenGeometry().width()
            screen_height = desktop.screenGeometry().height()
        except Exception:
            # Fallback to default resolution
            screen_width = 1920
            screen_height = 1080
        content_layout = QVBoxLayout(self)
        content_layout.setContentsMargins(0, 0, 0, 0)

        gif_container = QWidget()
        gif_layout = QVBoxLayout(gif_container)
        gif_layout.setContentsMargins(0, 0, 0, 0)

        gif_label = QLabel()
        gif_path = GraphicsDirectoryPath("Jarvis.gif")
        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            movie.setScaledSize(QSize(screen_width, screen_height))
            gif_label.setAlignment(Qt.AlignCenter)
            gif_label.setMovie(movie)
            movie.start()
        else:
            # Fallback if gif doesn't exist
            gif_label.setText("AI Assistant")
            gif_label.setStyleSheet("color: white; font-size: 48px; text-align: center;")
            gif_label.setAlignment(Qt.AlignCenter)
        gif_layout.addWidget(gif_label)
        
        # Status label (listening, recognizing, displaying) - positioned ABOVE mic button
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.status_label)
        
        # Mic button container
        mic_container = QWidget(self)
        mic_layout = QHBoxLayout(mic_container)
        mic_layout.setContentsMargins(0, 0, 0, 20)  # Remove left margin, add bottom margin
        
        self.icon_label = QLabel()
        mic_on_path = GraphicsDirectoryPath('Mic_on.png')
        if os.path.exists(mic_on_path):
            pixmap = QPixmap(mic_on_path)
            if not pixmap.isNull():
                new_pixmap = pixmap.scaled(60, 60)
                self.icon_label.setPixmap(new_pixmap)
        else:
            # Fallback if image doesn't exist
            self.icon_label.setText("🎤")
            self.icon_label.setStyleSheet("color: green; font-size: 48px; text-align: center;")
            self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(150, 150)
        
        # --- MODIFIED --- Initialize toggled state based on actual mic status
        self.toggled = (GetMicrophoneStatus() == "True")
        self.update_mic_icon() # Ensure icon matches initial state
        self.icon_label.mousePressEvent = self.toggle_icon
        
        mic_layout.addWidget(self.icon_label)
        mic_layout.addStretch()
        
        content_layout.addWidget(gif_container, stretch=1)
        content_layout.addWidget(mic_container, alignment=Qt.AlignCenter | Qt.AlignBottom)  # Center align
        
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size:16px; margin-bottom: 0;")
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        
        self.setLayout(content_layout)

        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: black;")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(200)
        
        # Status update timer for mic activity
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_mic_activity_status)
        self.status_timer.start(100)  # Update every 100ms

    def SpeechRecogText(self):
        """Update status based on assistant activity and microphone state"""
        try:
            messages = GetAssistantStatus()
            self.label.setText(messages)
            mic_status = GetMicrophoneStatus()
            
            # Update status label based on assistant activity with proper priority
            if messages and messages.strip():
                status_lower = messages.lower()
                
                # LISTENING states - when actively listening for voice input
                if "listening" in status_lower:
                    self.status_label.setText("🎤 Listening...")
                
                # RECOGNIZING states - when processing/searching
                elif "recognizing" in status_lower or "realtime searching" in status_lower or "searching" in status_lower:
                    self.status_label.setText("🔍 Recognizing...")
                
                # DISPLAYING states - when showing output/results
                elif "displaying" in status_lower or "task completed" in status_lower or "executing" in status_lower or "showing" in status_lower:
                    self.status_label.setText("✅ Displaying...")
                
                # THINKING/PROCESSING states
                elif "thinking" in status_lower or "chatting" in status_lower or "processing" in status_lower:
                    self.status_label.setText("💭 Processing...")
                
                # Error/Stop states - clear the status
                elif "stopped" in status_lower or "stopping" in status_lower or "error" in status_lower or "no response" in status_lower:
                    self.status_label.setText("")
                
                # Default: if there's any other message, consider it as displaying
                else:
                    self.status_label.setText("📢 Displaying...")
            
            # If mic is ON but no assistant activity, show listening
            elif mic_status == "True":
                self.status_label.setText("🎤 Listening...")
            
            # If mic is OFF, clear status
            else:
                self.status_label.setText("")
                
        except Exception as e:
            print(f"Error in SpeechRecogText: {e}")
    
    def update_mic_activity_status(self):
        """Real-time status updates for microphone and assistant states"""
        try:
            mic_status = GetMicrophoneStatus()
            assistant_status = GetAssistantStatus()
            
            # Priority 1: Show actual assistant status messages
            if assistant_status and assistant_status.strip():
                status_lower = assistant_status.lower()
                
                # LISTENING - Voice recognition active
                if "listening" in status_lower:
                    self.status_label.setText("🎤 Listening...")
                
                # RECOGNIZING - Searching or processing information
                elif "recognizing" in status_lower or "realtime searching" in status_lower or "searching" in status_lower:
                    self.status_label.setText("🔍 Recognizing...")
                
                # DISPLAYING - Showing results or completing tasks
                elif "displaying" in status_lower or "task completed" in status_lower or "executing" in status_lower or "showing held" in status_lower:
                    self.status_label.setText("✅ Displaying...")
                
                # PROCESSING - Thinking or chatting
                elif "thinking" in status_lower or "chatting" in status_lower or "processing" in status_lower:
                    self.status_label.setText("💭 Processing...")
                
                # Clear status on stop/error
                elif "stopped" in status_lower or "stopping" in status_lower or "error" in status_lower or "no response" in status_lower or "timeout" in status_lower:
                    self.status_label.setText("")
                
                # Default for other statuses
                else:
                    self.status_label.setText("📢 Displaying...")
            
            # Priority 2: Show listening when mic is on and no assistant activity
            elif mic_status == "True":
                self.status_label.setText("🎤 Listening...")
            
            # Priority 3: Clear status when mic is off
            else:
                self.status_label.setText("")
                
        except Exception as e:
            print(f"Error updating mic activity status: {e}")

    def load_icon(self, path, width=60, height=60):
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if pixmap and not pixmap.isNull():
                new_pixmap = pixmap.scaled(width, height)
                self.icon_label.setPixmap(new_pixmap)
                return True
        return False
    
    # --- MODIFIED --- New method to update icon based on toggled state
    def update_mic_icon(self):
        if self.toggled: # Mic is ON (Unmuted - shows mic icon)
            success = self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 60, 60)
            if not success:
                self.icon_label.setText("🎤")
                self.icon_label.setStyleSheet("color: green; font-size: 48px; text-align: center;")
            SetMicrophoneStatus("True")
            print("[GUI] Microphone status set to ON (Unmuted)")
        else: # Mic is OFF (Muted - shows muted mic icon)
            success = self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 60, 60)
            if not success:
                self.icon_label.setText("🔇")
                self.icon_label.setStyleSheet("color: red; font-size: 48px; text-align: center;")
            SetMicrophoneStatus("False")
            print("[GUI] Microphone status set to OFF (Muted)")

    def toggle_icon(self, event=None):
        self.toggled = not self.toggled
        self.update_mic_icon()


class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            desktop = QApplication.desktop()
            screen_width = desktop.screenGeometry().width()
            screen_height = desktop.screenGeometry().height()
        except Exception:
            # Fallback to default resolution
            screen_width = 1920
            screen_height = 1080
        layout = QVBoxLayout()
        label = QLabel("")
        layout.addWidget(label)
        chat_section = ChatSection(self)
        layout.addWidget(chat_section)
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)


class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.initUI(stacked_widget)
        self.current_screen = None
        self.stacked_widget = stacked_widget

    def initUI(self, stacked_widget):
        self.setFixedHeight(50)
        layout = QHBoxLayout()
        
        # Add spacer to push other buttons to the right
        layout.addStretch()
        layout.setAlignment(Qt.AlignRight)

        home_button = QPushButton()
        home_icon_path = GraphicsDirectoryPath("Home.png")
        if os.path.exists(home_icon_path):
            home_icon = QIcon(home_icon_path)
            home_button.setIcon(home_icon)
        home_button.setText(" Home")
        # --- MODIFIED STYLE ---
        home_button.setStyleSheet("QPushButton { background-color: black; color: white; }")

        message_button = QPushButton()
        message_icon_path = GraphicsDirectoryPath("Chats.png")
        if os.path.exists(message_icon_path):
            message_icon = QIcon(message_icon_path)
            message_button.setIcon(message_icon)
        message_button.setText(" Chat")
        # --- MODIFIED STYLE ---
        message_button.setStyleSheet("QPushButton { background-color: black; color: white; }")
        
        minimize_button = QPushButton()
        minimize_icon_path = GraphicsDirectoryPath('Minimize2.png')
        if os.path.exists(minimize_icon_path):
            minimize_icon = QIcon(minimize_icon_path)
            minimize_button.setIcon(minimize_icon)
        else:
            minimize_button.setText("-")
        minimize_button.setStyleSheet("background-color:white")
        minimize_button.clicked.connect(self.minimizeWindow)

        self.maximize_button = QPushButton()
        maximize_icon_path = GraphicsDirectoryPath('Maximize.png')
        restore_icon_path = GraphicsDirectoryPath('Minimize.png')
        if os.path.exists(maximize_icon_path):
            self.maximize_icon = QIcon(maximize_icon_path)
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.maximize_button.setText("□")
        
        if os.path.exists(restore_icon_path):
            self.restore_icon = QIcon(restore_icon_path)
        else:
            # Create a simple restore icon fallback
            self.restore_icon = QIcon()
            
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color:white")
        self.maximize_button.clicked.connect(self.maximizeWindow)

        close_button = QPushButton()
        close_icon_path = GraphicsDirectoryPath('Close.png')
        if os.path.exists(close_icon_path):
            close_icon = QIcon(close_icon_path)
            close_button.setIcon(close_icon)
        else:
            close_button.setText("X")
        close_button.setStyleSheet("background-color:white")
        close_button.clicked.connect(self.closeWindow)

        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet("border-color: black;")

        title_label = QLabel(f"{str(Assistantname).capitalize()} AI")
        title_label.setStyleSheet("color: black; font-size: 18px; background-color:white")

        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        layout.addWidget(line_frame)

        self.setLayout(layout)
        self.draggable = True
        self.offset = None

    def paintEvent(self, event):
        super().paintEvent(event)

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

    def showMessageScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
        message_screen = MessageScreen(self.parent())
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(message_screen)
            self.current_screen = message_screen

    def showInitialScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
        initial_screen = InitialScreen(self.parent())
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(initial_screen)
            self.current_screen = initial_screen

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            if hasattr(self, 'maximize_icon') and not self.maximize_icon.isNull():
                self.maximize_button.setIcon(self.maximize_icon)
            else:
                self.maximize_button.setText("□")
        else:
            self.parent().showMaximized()
            if hasattr(self, 'restore_icon') and not self.restore_icon.isNull():
                self.maximize_button.setIcon(self.restore_icon)
            else:
                self.maximize_button.setText("◱")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        try:
            desktop = QApplication.desktop()
            screen_width = desktop.screenGeometry().width()
            screen_height = desktop.screenGeometry().height()
        except Exception:
            # Fallback to default resolution
            screen_width = 1920
            screen_height = 1080

        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen(self)
        message_screen = MessageScreen(self)
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)

        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")

        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)


def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    GraphicalUserInterface()