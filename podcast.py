import requests
import json
import os
from pydub import AudioSegment
from dotenv import load_dotenv
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from datetime import datetime
import google.generativeai as genai
from groq import Groq


load_dotenv()
GROQ_KEY = os.getenv('GROQ_KEY')
GEMINI_KEY = os.getenv('GEMINI_KEY')
genai.configure(api_key=GEMINI_KEY)

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)

chat_session = model.start_chat(
  history=[
  ]
)

client = Groq(api_key=GROQ_KEY)
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.aac', '.flac']


import warnings
warnings.filterwarnings("ignore")


def search(person_name, limit=100):
    """
    :param person_name: Name of the person to search for.
    :param limit: Number of results to retrieve.
    :return: List of podcast results.
    """
    url = 'https://itunes.apple.com/search'
    params = {
        'term': person_name,
        'media': 'podcast',
        'entity': 'podcastEpisode',
        'limit': limit
    }

    print("Awaiting...")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('results')
    else:
        print(f"Error {response.status_code}")
        return []


def find_audio_links(soup):
    """
    Look for any potential audio file sources in the HTML soup.
    
    :param soup: BeautifulSoup object containing parsed HTML.
    :return: List of found audio file URLs.
    """
    audio_links = []
    
    # Look for <a> tags and check their href attributes for audio file extensions
    for tag in soup.find_all('a', href=True):
        href = tag['href']
        if any(ext in href for ext in AUDIO_EXTENSIONS):
            audio_links.append(href)
    
    # Look for <audio> or <source> tags with src attributes
    for audio_tag in soup.find_all(['audio', 'source']):
        src = audio_tag.get('src')
        if src and any(ext in src for ext in AUDIO_EXTENSIONS):
            audio_links.append(src)
    
    return audio_links


def find_download_links(soup):
    """
    Search for download-related links, buttons, or elements.
    
    :param soup: BeautifulSoup object containing parsed HTML.
    :return: List of found download links.
    """
    download_links = []


    
    for tag in soup.find_all('a', href=True):
        if "download" in tag.text.lower() or any(ext in tag['href'] for ext in AUDIO_EXTENSIONS):
            download_links.append(tag['href'])
    
    for button in soup.find_all(['button', 'input']):
        if "download" in button.get_text(strip=True).lower():
            download_links.append(button.get('href') or button.get('value'))
    
    return download_links


def scrape_for_audio(source_url):
    """
    Scrape the source page for audio files/transcription
    
    :param source_url: The URL of the source website.
    :return: TBD
    """
    this_session = HTMLSession()
    response = this_session.get(source_url)
    response.html.render()
    
    if response.status_code == 200:
        # print(response.html)
        soup = BeautifulSoup(response.html.raw_html, 'html.parser')
        # print(response.text[:len(response.text)])

        audio_links = find_audio_links(soup)
        download_links = find_download_links(soup)

        if len(audio_links) > 0:
            print(f"Found: {audio_links}")
            audio_source = requests.get(audio_links[0])
            return audio_source
        elif len(download_links) > 0:
            print(f"Found: {audio_links}")
    else:
        print(f"Error {response.status_code} while scraping")
        return None


def find_source(track_url):
    """
    Scrape the trackViewUrl page for a link to the podcast website.
    
    :param track_url: The URL of the podcast track.
    :return: The href of the original podcast website.
    """

    response = requests.get(track_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # The link should be titled "podcast website"
        element = soup.find(string=lambda text: text and "episode webpage" in text.lower())

        if element:
            parent = element.parent.parent
            if parent and parent.has_attr('href'):
                return parent['href']
            else:
                print("No 'href' found on expected position")
                # print(f"Element: {element}")
                # print(f"Parent: {parent}")
                # print(f"Parent: {parent.parent}")
        else:
            print("No 'episode webpage' link found.")
    else:
        print(f"Error {response.status_code} while scraping")
        return None

def get_latest_podcast(podcasts):
    """
    :param podcasts: List of podcast dictionaries.
    :return: The latest podcast dictionary.
    """
    latest_podcast = None
    latest_date = None

    for podcast in podcasts:
        release_date_str = podcast.get('releaseDate')
        
        if release_date_str:
            release_date = datetime.strptime(release_date_str, "%Y-%m-%dT%H:%M:%SZ")
            if not latest_date or release_date > latest_date:
                latest_date = release_date
                latest_podcast = podcast

    return latest_podcast


def transcribe_audio():
    """
    Transcribe podcast with Groq Whisper
    """
    with open("podcast.mp3", "rb") as file:
        try:
            transcription = client.audio.transcriptions.create(
                file=("podcast.mp3", file.read()),
                model="whisper-large-v3",
                prompt="The audio is from a podcast with potentially multiple speakers. Format with linebreaks.",
                response_format="text"
            )
            return transcription
        except Exception as e:
            print(e)
            return None


def main():
    person_name = input("Name or keyword: ")
    podcasts = search(person_name)

    if not podcasts:
        print("No podcasts found.")
        return

    latest_podcast = get_latest_podcast(podcasts)

    if latest_podcast:
        print("------------------------------------------")
        print(f"| Latest \"{person_name}\" Podcast")
        print(f"| Title: {f"{latest_podcast.get('collectionName')} -- {latest_podcast.get('trackName')}"[:102]}...")
        # print(f"Author: {latest_podcast.get('artistName')}") # only works for collection
        print(f"| Date: {latest_podcast.get('releaseDate')}")
        # print(f"URL: {latest_podcast.get('collectionViewUrl')}") # collection
        print(f"| Podcast Link: {latest_podcast.get('trackViewUrl')[:95]}...")
        # latest_podcast.get('artworkUrl600') # thumbnail

        podcast_website = find_source(latest_podcast.get('trackViewUrl'))
        if podcast_website:
            print(f"| Source Found: {podcast_website[:95]}...")
            print("------------------------------------------")
            print("Scraping source for audio...")
            audio = scrape_for_audio(podcast_website)
            if (audio):
                with open("podcast.mp3","wb") as file:
                    file.write(audio.content)
                print("Parsing audio...")
                audio = AudioSegment.from_file("podcast.mp3", format="mp3")

                if (len(audio) > 3600000):
                    print("Audio is too long to transcribe. Audio is capped at 1 hour for usability purposes.")
                elif (len(audio) > 1800000):
                    print("Segmenting...")
                    cut1 = audio[:1800000] 
                    cut2 = audio[1800000:] 
                    print("Compressing...")
                    cut1.export("podcast.mp3", format="mp3", bitrate="64k") 
                    print("Done! Transcribing audio below...")
                    print("------------------------------------------")
                    transcription = transcribe_audio()
                    print(transcription)
                    cut2.export("podcast.mp3", format="mp3", bitrate="64k")
                    transcription2 = transcribe_audio()
                    print(transcription2)
                    print("------------------------------------------")
                    print("Done transcribing audio!")
                    transcription += transcription2
                    print("Correcting, formatting, and translating...")
                    response = chat_session.send_message(f"Correct the following raw transcription, and format it (linebreaks with speakers, try to label names where possible). Remove unecessary excess content (such as repeated oh yeah, yeah, yeah, repeated ums, etc.). Respond with only the corrected script (no title!). Translate to english if applicable. \n{transcription}")
                    print("Formatted!")
                    print("------------------------------------------")
                    print(response.text)
                    
                else:
                    print("Done! Transcribing audio...")
                    print("------------------------------------------")
                    transcription = transcribe_audio()
                    print(transcription)
            else:
                print("Audio source not found.")
            


    else:
        print("Fatal error: failed to order.")

if __name__ == "__main__":
    main()
