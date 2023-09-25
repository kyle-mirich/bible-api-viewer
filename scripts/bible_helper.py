import os
import json
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from difflib import get_close_matches

bible_api_key = os.getenv('BIBLE_API_KEY')

# Constants
BASE_URL = "https://api.scripture.api.bible/v1"

# Construct the paths to the files
current_directory = os.path.dirname(os.path.abspath(__file__))
bible_data_path = os.path.join(current_directory, '..', '..', 'reference-tools', 'bible-id.json')
abbreviations_path = os.path.join(current_directory, '..', '..', 'reference-tools', 'abbreviations.json')

# Loading the Bible data from 'bible-id.json'
with open(bible_data_path, 'r', encoding='utf-8') as file:
    bible_data = json.load(file)

# Loading the book abbreviations from 'abbreviations.json'
with open(abbreviations_path, 'r', encoding='utf-8') as file:
    abbreviations_dict = json.load(file)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def request_data(url, params=None):
    headers = {'api-key': bible_api_key}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error while requesting {url}: {e}")
        raise

def normalize_book_name(book_name):
    book_abbr = abbreviations_dict.get(book_name, {}).get('id', None)
    if not book_abbr:
        for key, value in abbreviations_dict.items():
            if value['id'] == book_name:
                book_abbr = book_name
                break
    return book_abbr

def get_bible_id(input_value):
    all_bible_ids = [details['id'] for details in bible_data.values()]
    if input_value in all_bible_ids:
        return input_value
    bible_detail = bible_data.get(input_value, None)
    if bible_detail:
        return bible_detail['id']
    closest_match = get_close_matches(input_value, bible_data.keys(), n=1)
    if closest_match:
        return bible_data[closest_match[0]]['id']
    raise ValueError("Invalid input. Neither a valid Bible ID nor a full name.")

def auto_correct_bible_id(bible_id):
    all_bible_ids = [details['id'] for details in bible_data.values()]
    if bible_id in all_bible_ids:
        return bible_id
    closest_matches = get_close_matches(bible_id, all_bible_ids, n=1)
    if closest_matches:
        return closest_matches[0]
    raise ValueError("Invalid Bible ID provided.")

def validate_chapter_and_verse_format(chapter, verse=None):
    try:
        chapter = str(int(chapter))
        if verse:
            verse = str(int(verse))
            return True, (chapter, verse)
        return True, chapter
    except ValueError:
        return False, "Invalid chapter or verse format."