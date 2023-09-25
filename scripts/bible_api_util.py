import json
import urllib
from bible_helper import BASE_URL, auto_correct_bible_id,get_bible_id,get_close_matches,bible_data, abbreviations_dict, request_data, normalize_book_name,validate_chapter_and_verse_format
import requests
import streamlit as st





@st.cache_data
def get_bible_id_and_name(search_term):
    # Input validation
    if not isinstance(search_term, str) or len(search_term.strip()) == 0:
        return json.dumps({"data": {"id": "invalid_input", "name": "Invalid search term provided."}})
    
    search_term = search_term.strip()

    for name, details in bible_data.items():
        if any(search_term.lower() in str(value).lower() for value in (name, details.get('abbreviation', ''), details.get('language', ''), details.get('script', ''))):
            return json.dumps({"data": {"id": details['id'], "name": name}})

    data = request_data(f"{BASE_URL}/bibles?query={search_term}")
    
    if data and 'data' in data and data['data']:
        return json.dumps({"data": {"id": data['data'][0]['id'], "name": data['data'][0]['name']}})
    
    return json.dumps({"data": {"id": "not_found", "name": "No matching results. Please try again with a different term."}})

@st.cache_data
def get_list_of_verses_in_chapter_and_verse_id(bible_id, chapter_id):
    # Check the Bible ID
    try:
        bible_id = get_bible_id(bible_id)
    except ValueError as e:
        return json.dumps({"data": str(e)})
    # Validate the chapter format
    is_valid, chapter = validate_chapter_and_verse_format(chapter_id, "1")
    if not is_valid:
        return json.dumps({"data": chapter})
    
    chapter = chapter[0]  # Extract the corrected chapter value

    data = request_data(f"{BASE_URL}/bibles/{bible_id}/chapters/{chapter}/verses")
    modified_data = {
        "data": [
            f"{data_item['bookId']}.{data_item['chapter']}.{data_item['verse']}"
            for data_item in data['data']
        ]
    }
    return modified_data


@st.cache_data
def get_book_id(book_name):
    book_id = abbreviations_dict.get(book_name, {}).get('id', None)
    if book_id:
        return json.dumps({"data": book_id})
    else:
        # Suggest a close match if not found
        suggestions = get_close_matches(book_name, abbreviations_dict.keys(), n=1)
        if suggestions:
            return json.dumps({"data": "Did you mean: " + suggestions[0]})
        else:
            return json.dumps({"data": "Invalid book name provided."})

@st.cache_data
def search_bible_by_language(language):
    result = [(name, details['id']) for name, details in bible_data.items() if language.lower() in details['language'].lower()]
    return json.dumps({"data": result})

@st.cache_data
def search_bible_by_script(script):
    result = [(name, details['id']) for name, details in bible_data.items() if script.lower() in details['script'].lower()]
    return json.dumps({"data": result})

@st.cache_data
def get_information_about_specific_bible(bible_id):
    # Check the Bible ID
    # After:
    try:
        bible_id = get_bible_id(bible_id)
    except ValueError as e:
        return json.dumps({"data": str(e)})
    data = request_data(f"{BASE_URL}/bibles/{bible_id}")
    return json.dumps({"data": data})

@st.cache_data
def get_list_of_books_and_book_id(bible_id):
    # Check the Bible ID
    # After:
    try:
        bible_id = get_bible_id(bible_id)
    except ValueError as e:
        return json.dumps({"data": str(e)})
    data = request_data(f"{BASE_URL}/bibles/{bible_id}/books")
    return json.dumps({"data": data})


@st.cache_data
def get_full_chapter_text(bible_id, book, chapter_number):
    # Check the Bible ID
    try:
        bible_id = get_bible_id(bible_id)
    except ValueError as e:
        return json.dumps({"data": str(e)})

    # Format the chapter_id for the API
    chapter_id = f"{book}.{chapter_number}"
   
    data = request_data(f"{BASE_URL}/bibles/{bible_id}/chapters/{chapter_id}")
    return json.dumps({"data": data})


@st.cache_data
def get_list_of_chapters_and_chapter_id_in_specific_book(bible_id, book_name):
    # Check if the book name is valid using abbreviations dictionary
    # After:
    try:
        bible_id = get_bible_id(bible_id)
    except ValueError as e:
        return json.dumps({"data": str(e)})
    data = request_data(f"{BASE_URL}/bibles/{bible_id}/books/{book_name}/chapters")
    return json.dumps({"data": data})


@st.cache_data
def get_specific_verse_in_bible(bible_id, book_name, chapter, verse):
    # Check the Bible ID
    # After:
    try:
        bible_id = get_bible_id(bible_id)
    except ValueError as e:
        return json.dumps({"data": str(e)})
    
    # Normalize the book name
    book_abbr = normalize_book_name(book_name)

    # If no valid abbreviation is found, return an error
    if not book_abbr:
        return json.dumps({"data": "Invalid book name provided."})

    # Validate chapter and verse format
    is_valid, result = validate_chapter_and_verse_format(chapter, verse)
    if not is_valid:
        return json.dumps({"data": result})

    chapter, verse = result  # unpack the corrected chapter and verse values

    verse_id = f"{book_abbr}.{chapter}.{verse}"
    data = request_data(f"{BASE_URL}/bibles/{bible_id}/verses/{verse_id}")
    return json.dumps({"data": data})


@st.cache_data
def search_bible_for_keyword(bible_id, query):
    # After:
    try:
        bible_id = get_bible_id(bible_id)
    except ValueError as e:
        return json.dumps({"data": str(e)})

    query = urllib.parse.quote(query)
    data = request_data(f"{BASE_URL}/bibles/{bible_id}/search?query={query}")

    if not data or not data.get('data'):
        return json.dumps({"data": "No results found for the provided query."})
    
    return json.dumps({"data": data})


@st.cache_data
def get_passages_in_chapter(bible_id, chapter_id, content_type='html', 
                            include_notes=True, include_titles=True, 
                            include_chapter_numbers=True, include_verse_numbers=True, 
                            include_verse_spans=True, parallels=None):
    """
    Fetch all passages in a specific chapter.
    """
    # After:
    try:
        bible_id = get_bible_id(bible_id)
    except ValueError as e:
        return json.dumps({"data": str(e)})

    params = {
        "content-type": content_type,
        "include-notes": include_notes,
        "include-titles": include_titles,
        "include-chapter-numbers": include_chapter_numbers,
        "include-verse-numbers": include_verse_numbers,
        "include-verse-spans": include_verse_spans,
        "parallels": parallels
    }

    data = request_data(f"{BASE_URL}/bibles/{bible_id}/passages/{chapter_id}", params=params)
    
    return json.dumps({"data": data})


@st.cache_data
def search_passage(bible_id, query, limit=10, offset=0):
    if not isinstance(query, str) or len(query.strip()) == 0:
        return json.dumps({"data": "Invalid search query provided."})

    try:
        bible_id = auto_correct_bible_id(bible_id)
    except ValueError as e:
        return json.dumps({"data": str(e)})

    params = {
        "query": query.strip(),
        "limit": limit,
        "offset": offset
    }

    data = request_data(f"{BASE_URL}/bibles/{bible_id}/search", params=params)

    if not data or not data.get('data'):
        return json.dumps({"data": "No results found for the provided query."})
    
    return json.dumps({"data": data})



@st.cache_data
def get_all_bibles():
    try:
        response = requests.get(f"{BASE_URL}/bibles")
        if response.status_code == 200:
            return json.dumps({"data": response.json()['data']})
        else:
            st.error(f"Error fetching data: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"An exception occurred: {e}")
        return None

@st.cache_data
def get_all_bibles():
    try:
        url = f"{BASE_URL}/bibles"
        response_data = request_data(url)
        if 'data' in response_data:
            return json.dumps({"data": response_data['data']})
        else:
            st.error("Error fetching data: Data field missing in response")
            return None
    except Exception as e:
        st.error(f"An exception occurred: {e}")
        return None