import requests
import json
import os
from pydub import AudioSegment
from dotenv import load_dotenv
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from datetime import datetime
from groq import Groq


load_dotenv()
GROQ_KEY = os.getenv('GROQ_KEY')
client = Groq(api_key=GROQ_KEY)
with open("podcast.mp3", "rb") as file:
    transcription = client.audio.transcriptions.create(
        file=("podcast.mp3", file.read()),
        model="whisper-large-v3",
        prompt="The audio is from a podcast. Label the different speakers.",
        response_format="text",
        language="en",
    )
    print(transcription)