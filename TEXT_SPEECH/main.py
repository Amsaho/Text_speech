import streamlit as st
from moviepy.editor import VideoFileClip, AudioFileClip
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
import openai
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "studious-plate-438707-k3-df28c2244c5f.json"

# Function to transcribe audio using Google Speech-to-Text
def transcribe_audio(audio_path):
    client = speech.SpeechClient()
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    response = client.recognize(config=config, audio=audio)
    return " ".join([result.alternatives[0].transcript for result in response.results])

# Function to correct transcription using GPT-4
def correct_transcription(transcription):
    openai.api_key = os.getenv("api_key")
    response = openai.Completion.create(
        model="gpt-4",
        prompt=f"Correct the following transcription: {transcription}",
        max_tokens=500
    )
    return response.choices[0].text.strip()

# Function to generate AI voice from text using Google Text-to-Speech
def generate_ai_voice(text, output_path):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Journey-F"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    with open(output_path, "wb") as out:
        out.write(response.audio_content)
    return output_path

# Function to replace audio in video
def replace_audio(video_path, audio_path, output_path):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    video = video.set_audio(audio)
    video.write_videofile(output_path, codec='libx264', audio_codec='aac')

# Streamlit app
st.title("Video Audio Replacement with AI Voice")

uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"], key="video_uploader")

if st.button("Process Video"):
    if uploaded_video is not None:
        video_path = uploaded_video.name
        with open(video_path, "wb") as f:
            f.write(uploaded_video.getbuffer())
        
        # Extract audio from video
        video = VideoFileClip(video_path)
        audio_path = "extracted_audio.wav"
        video.audio.write_audiofile(audio_path)
        
        # Transcribe audio
        try:
            transcription = transcribe_audio(audio_path)
            st.write("Transcription:", transcription)
        except Exception as e:
            st.error(f"Error transcribing audio: {e}")
            st.stop()
        
        # Correct transcription
        try:
            corrected_transcription = correct_transcription(transcription)
            st.write("Corrected Transcription:", corrected_transcription)
        except Exception as e:
            st.error(f"Error correcting transcription: {e}")
            st.stop()
        
        # Generate AI voice
        try:
            ai_audio_path = "ai_voice.mp3"
            generate_ai_voice(corrected_transcription, ai_audio_path)
        except Exception as e:
            st.error(f"Error generating AI voice: {e}")
            st.stop()
        
        # Replace audio in video
        try:
            output_video_path = "output_video.mp4"
            replace_audio(video_path, ai_audio_path, output_video_path)
            st.video(output_video_path)
            st.success("Audio replaced successfully!")
        except Exception as e:
            st.error(f"Error replacing audio in video: {e}")
    else:
        st.error("Please upload a video file.")
