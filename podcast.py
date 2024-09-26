import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime

AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.aac', '.flac']

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

    response = requests.get(source_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        print(response.text[:len(response.text)//4])
        print(find_audio_links(soup))
        print(find_download_links(soup))
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

def main():
    person_name = input("Name or keyword: ")
    podcasts = search(person_name)

    if not podcasts:
        print("No podcasts found.")
        return

    latest_podcast = get_latest_podcast(podcasts)

    if latest_podcast:
        print(f"\nLatest \"{person_name}\" Podcast")
        print(f"Title: {latest_podcast.get('collectionName')} -- {latest_podcast.get('trackName')}")
        print(f"Author: {latest_podcast.get('artistName')}")
        print(f"Date: {latest_podcast.get('releaseDate')}")
        # print(f"URL: {latest_podcast.get('collectionViewUrl')}") # collection
        print(f"URL: {latest_podcast.get('trackViewUrl')}")
        # latest_podcast.get('artworkUrl600') # thumbnail

        podcast_website = find_source(latest_podcast.get('trackViewUrl'))
        if podcast_website:
            print(f"Source website found: {podcast_website}")
            scrape_for_audio(podcast_website)

    else:
        print("Fatal error: failed to order.")

if __name__ == "__main__":
    main()
