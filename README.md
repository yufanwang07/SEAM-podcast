# Podcast Audio Scraper

This project first uses the iTunes search API to find the most recent podcast featuring a person/keyword, then scrapes the page for the source website of the podcast. Once this source website is found, the website is scraped for the source audio, which is then transcribed via Groq Whisper and formatted via Gemini.

For API scripting to work, create a .env file with
```env
GROQ_KEY= (groq api key here)
GEMINI_KEY= (gemini api key here)
```
in the same folder as podcast.py.