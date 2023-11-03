import streamlit as st
import json
from bs4 import BeautifulSoup
from scripts.bible_api_util import (
    get_all_bibles,
    get_list_of_books_and_book_id,
    get_list_of_chapters_and_chapter_id_in_specific_book,
    get_full_chapter_text,
    get_bible_id_and_name,
    get_information_about_specific_bible,
    request_data,
    get_specific_verse_in_bible
)

with st.sidebar:
    st.markdown("Powered by [API.Bible](https://scripture.api.bible/)")


# Load cross-reference data
with open('data/cross_ref.json', 'r') as f:
    cross_ref_data = json.load(f)


# Function to extract verse content
def extract_verse_content(verse_json, settings):
    try:
        if isinstance(verse_json, str):
            verse_dict = json.loads(verse_json)
        else:
            verse_dict = verse_json  # assume it's already a dictionary

        content = verse_dict.get("data", {}).get("data", {}).get("content", "")
        soup = BeautifulSoup(content, 'html.parser')
        formatted_text = ""

        for p in soup.find_all('p', class_='p'):
            for element in p.children:
                if element.name is None:
                    formatted_text += str(element)
                else:
                    classes = element.get('class', [])
                    styles = []

                    if 'v' in classes:
                        styles.append(f'font-weight: {"bold" if settings["bold_verse_numbers"] else "normal"}')
                        formatted_text += f'<sub style="{";".join(styles)}">[{element.text}]</sub>'
                    elif 'wj' in classes:
                        styles.append(f'color: {"red" if settings["color_jesus_words"] else "black"}')
                        formatted_text += f'<span style="{";".join(styles)}">{element.text}</span>'
                    elif 'add' in classes:
                        formatted_text += f'<span style="font-style: italic;">{element.text}</span>'
                    elif 'nd' in classes:
                        text = element.text
                        formatted_text += f'<span>{text}</span>'

                    else:
                        formatted_text += element.decode_contents()

        return formatted_text.strip()
    except Exception as e:
        print(f"Error in extracting verse content: {e}")
        return None


# Function to search cross-references for a specific book and chapter
def custom_search_cross_ref(book_id: str, chapter: str, cross_ref_data: dict) -> dict:
    search_prefix = f"{book_id}.{chapter}."
    chapter_cross_refs = {verse: refs for verse, refs in cross_ref_data.items() if verse.startswith(search_prefix)}
    return chapter_cross_refs

# Function to parse JSON strings
def parse_json(json_str):
    return json.loads(json_str)['data']


# Function to display verse from a reference
def display_verse_from_ref(ref):
    settings = {
        "color_jesus_words": True,  # Replace with Streamlit checkbox value
        "bold_verse_numbers": True,  # Replace with Streamlit checkbox value
    }

    ref_bible_id, ref_book, ref_chapter, ref_verse = ref.split('_')
    verse_text_json = get_specific_verse_in_bible(ref_bible_id, ref_book, ref_chapter, ref_verse)
    if verse_text_json is not None:
        verse_text = extract_verse_content(verse_text_json, settings)
        if verse_text is not None:
            st.markdown(f"📜 **{ref_book} {ref_chapter}:{ref_verse}** - {verse_text}\n\n\n---------------\n\n\n Below are all the cross references associated with {ref_book} {ref_chapter}:{ref_verse}\n\n\n ---", unsafe_allow_html=True)
        else:
            st.write(f"Debug: Could not extract verse content for {ref}")
    else:
        st.write(f"Debug: Could not fetch JSON for {ref}")

# Sidebar for customization settings
st.sidebar.title('Settings')
color_jesus_words = st.sidebar.checkbox("Color Jesus' words in Red")
bold_verse_numbers = st.sidebar.checkbox('Bold Verse Numbers')

# Global variable for clarification words
clarification_words = {}

# Function to format chapter text
def format_chapter_text(chapter_html):
    global clarification_words
    clarification_words = {}
    current_verse = None

    if not chapter_html:
        st.warning("Content for the selected chapter is not available.")
        return

    soup = BeautifulSoup(chapter_html, 'html.parser')
    formatted_text = ""

    # Check if the chapter is 'intro'
    is_intro = 'mt1' in [p.get('class', [])[0] for p in soup.find_all('p')]

    if is_intro:
        # Handle the 'intro' chapter differently
        for p in soup.find_all('p', class_='mt1'):
            formatted_text += f'\n\n{p.text}'
    else:
        # Handle regular chapters
        for p in soup.find_all('p', class_='p'):
            formatted_text += "\n \n"
            for element in p.children:
                if element.name is None:
                    formatted_text += str(element)
                else:
                    classes = element.get('class', [])
                    styles = []
                    if 'v' in classes:
                        current_verse = element.text
                        styles.append(f'font-weight: {"bold" if bold_verse_numbers else "normal"}')
                        formatted_text += f'<sub style="{";".join(styles)}">[{element.text}]</sub>'
                    elif 'wj' in classes:
                        styles.append(f'color: {"red" if color_jesus_words else "white"}')
                        formatted_text += f'<span style="{";".join(styles)}">{element.text}</span>'
                    elif 'add' in classes:
                        formatted_text += f'<span style="font-style: italic;">{element.text}</span>'
                    elif 'nd' in classes:
                        text = element.text
                        formatted_text += f'<span>{text}</span>'
                    else:
                        formatted_text += element.decode_contents()
                
    st.markdown(formatted_text, unsafe_allow_html=True)

def get_default_book_and_chapter_index(book_names, chapter_numbers, default_book="Genesis", default_chapter="1"):
    try:
        default_book_index = book_names.index(default_book) if default_book in book_names else 0
        default_chapter_index = chapter_numbers.index(default_chapter) if default_chapter in chapter_numbers else 0
        return default_book_index, default_chapter_index
    except Exception as e:
        print(f"Error in getting default book and chapter index: {e}")
        return 0, 0  # Return the first book and chapter as default in case of any error

def get_default_bible_index(all_bibles_data, default_bible_id="de4e12af7f28f599-01"):
    try:
        for index, bible in enumerate(all_bibles_data):
            if bible['id'] == default_bible_id:
                return index
        print("Debug: Default Bible ID not found in the list of all Bibles.")
        return 0  # Return the first Bible as default if the specified default is not found
    except Exception as e:
        print(f"Error in getting default Bible index: {e}")
        return 0  # Return the first Bible as default in case of any error

def main():
    st.session_state.selected_refs = st.session_state.get("selected_refs", [])

    st.title("Bible Viewer")

    # Step 1: Load all Bibles
    all_bibles_data_str = get_all_bibles()
    all_bibles_data = parse_json(all_bibles_data_str)
    # Generate a list of just the Bible names for the select box
    bible_name_options = [bible['name'] for bible in all_bibles_data]

    # Create a mapping from Bible names to IDs for easy lookup later
    bible_name_to_id = {bible['name']: bible['id'] for bible in all_bibles_data}

    # Get the default Bible index
    default_bible_index = get_default_bible_index(all_bibles_data)

    # Use only the names in the selectbox
    selected_bible_name = st.selectbox(
        "Select a Bible Translation:", bible_name_options, index=default_bible_index
    )

    # Get the corresponding Bible ID based on the selected name
    selected_bible_id = bible_name_to_id.get(selected_bible_name, None)

    if selected_bible_name and selected_bible_id:
        # Step 2: Load and Select Book
        books_data_str = get_list_of_books_and_book_id(selected_bible_id)
        books_data = parse_json(books_data_str)
        book_names = [book['name'] for book in books_data['data']]

        # Get the index of the default book "Genesis"
        default_book_index = book_names.index("Genesis") if "Genesis" in book_names else 0

        selected_book = st.selectbox("Select a Book:", book_names, index=default_book_index)

        if selected_book:
            selected_book_id = next((book['id'] for book in books_data['data'] if book['name'] == selected_book), None)

            # Step 3: Load and Select Chapter
            chapters_data_str = get_list_of_chapters_and_chapter_id_in_specific_book(selected_bible_id, selected_book_id)
            chapters_data = parse_json(chapters_data_str)
            chapter_numbers = [str(chapter['number']) for chapter in chapters_data['data']]

            # Get the index of the default chapter "1"
            default_chapter_index = chapter_numbers.index("1") if "1" in chapter_numbers else 0

            selected_chapter = st.selectbox("Select a Chapter:", chapter_numbers, index=default_chapter_index)

            # Step 4: Display format options
            #display_format = st.radio('Display Format:', ('Chapter (Paragraph View)', 'Verse by Verse'))

            # Step 5: Fetch and Display Chapter Text
            if selected_chapter:
                chapter_text_str = get_full_chapter_text(selected_bible_id, selected_book_id, selected_chapter)
                chapter_text_data = parse_json(chapter_text_str)
                
                if 'content' in chapter_text_data.get('data', {}):
                    formatted_text = format_chapter_text(chapter_text_data['data']['content'])

        # Cross-reference expander
        with st.expander("Cross References", expanded=False):
            st.subheader(f"Cross References for {selected_book} Chapter {selected_chapter}")
            chapter_cross_refs = custom_search_cross_ref(selected_book_id, selected_chapter, cross_ref_data)
            
            if chapter_cross_refs:
                # Search Box
                #search_term = st.text_input("Search for a verse:", "")
                search_term =""
                # Grid Layout for Verses
                filtered_verses = [verse for verse in chapter_cross_refs.keys() if search_term.lower() in verse.lower()]
                for i in range(0, len(filtered_verses), 3):
                    row_verses = filtered_verses[i:i+3]
                    cols = st.columns(len(row_verses))
                    for col, verse in zip(cols, row_verses):
                        if col.button(f"Verse {verse}", key=f"grid_{verse}"):
                            ref = f"{selected_bible_id}_{selected_book}_{selected_chapter}_{verse.split('.')[-1]}"
                            display_verse_from_ref(ref)

                            # Display cross references
                            refs = chapter_cross_refs[verse]
                            for j in range(0, len(refs), 3):
                                row_refs = refs[j:j+3]
                                ref_cols = st.columns(len(row_refs))
                                for ref_col, ref in zip(ref_cols, row_refs):
                                    if ref_col.button(f"{ref}", key=f"{verse}_{ref}"):
                                        display_verse_from_ref(ref)
                    st.markdown("---")  # Horizontal line for separation
            else:
                st.write("❌ No cross references available for this chapter.")
                

if __name__ == "__main__":
    main()