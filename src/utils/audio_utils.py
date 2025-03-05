"""
Audio Processing Utilities for Travin Canvas

This module provides audio processing utilities for the Travin Canvas application.
It handles speech-to-text and text-to-speech conversions using OpenAI's APIs.
The module supports real-time audio capture, processing, and playback to enable
voice interactions with the chat interface.

Key features:
- Real-time audio recording with configurable duration
- Speech-to-text transcription using OpenAI's Whisper API
- Text-to-speech synthesis using OpenAI's TTS API
- Audio playback for synthesized speech
- Resource management for audio streams and temporary files

Dependencies:
- openai: For API access to OpenAI's audio models
- pyaudio: For audio capture and playback
- pydub: For audio file manipulation
- wave: For WAV file handling
- numpy: For audio data processing
"""

import os
import tempfile
import time
from pathlib import Path
import numpy as np
import pyaudio
import wave
from pydub import AudioSegment
from pydub.playback import play
import httpx
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
    
# Create a custom httpx client without proxies
http_client = httpx.Client()

# Initialize OpenAI client with the custom httpx client
# This avoids the 'proxies' parameter issue in the newer OpenAI SDK
client = OpenAI(api_key=api_key, http_client=http_client)

class AudioProcessor:
    """
    Handles audio capture, transcription, and speech synthesis.
    
    This class provides a comprehensive interface for audio processing,
    handling all aspects of voice interactions including:
    - Real-time audio recording from microphone
    - Conversion of speech to text using OpenAI's Whisper API
    - Conversion of text to speech using OpenAI's TTS API
    - Audio playback for synthesized speech responses
    - Resource management for audio streams and temporary files
    
    The class is designed to work seamlessly with the chat interface
    to enable voice-based interactions with the LLM.
    """
    
    def __init__(self):
        """Initialize the audio processor with default settings."""
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.audio = pyaudio.PyAudio()
        self.recording = False
        
    def start_recording(self, max_seconds=10):
        """
        Start recording audio from the microphone.
        
        Args:
            max_seconds (int): Maximum recording duration in seconds
            
        Returns:
            str: Path to the saved audio file
        """
        self.recording = True
        frames = []
        
        # Open stream
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        print("Recording started...")
        
        # Record for max_seconds or until stopped
        start_time = time.time()
        while self.recording and (time.time() - start_time) < max_seconds:
            data = stream.read(self.chunk)
            frames.append(data)
            
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        print("Recording stopped.")
        
        # Save the recorded audio to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            
        return temp_file.name
    
    def stop_recording(self):
        """Stop the current recording."""
        self.recording = False
        
    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio file to text using OpenAI's Whisper API.
        
        Args:
            audio_file_path (str): Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""
        
    def text_to_speech(self, text, voice="alloy"):
        """
        Convert text to speech using OpenAI's Text-to-Speech API.
        
        Args:
            text (str): Text to convert to speech
            voice (str): Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Save to a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            response.stream_to_file(temp_file.name)
            
            return temp_file.name
        except Exception as e:
            print(f"Error generating speech: {e}")
            return None
    
    def play_audio(self, audio_file_path):
        """
        Play an audio file.
        
        Args:
            audio_file_path (str): Path to the audio file to play
        """
        try:
            sound = AudioSegment.from_file(audio_file_path)
            play(sound)
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        self.audio.terminate() 