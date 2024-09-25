import requests
import json
from datetime import datetime

def search(person_name, limit=50):
    """
    :param person_name: Name of the person to search for.
    :param limit: Number of results to retrieve.
    :return: List of podcast results.
    """
    url = 'https://itunes.apple.com/search'
    params = {
        'term': person_name,
        'media': 'podcast',
        'entity': 'podcast',
        'limit': limit
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('results')
    else:
        print(f"Error {response.status_code}")
        return []

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
        print(f"Podcast Name: {latest_podcast.get('collectionName')}")
        print(f"Author: {latest_podcast.get('artistName')}")
        print(f"Release Date: {latest_podcast.get('releaseDate')}")
        print(f"Link: {latest_podcast.get('collectionViewUrl')}")
        # latest_podcast.get('artworkUrl600') # thumbnail
    else:
        print("Fatal error: failed to order.")

if __name__ == "__main__":
    main()
