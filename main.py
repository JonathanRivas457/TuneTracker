import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import json
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

# Initialize the Spotify client
client_credentials_manager = SpotifyClientCredentials(client_id='98c92df339b44755b057c9e2be8a9d24', client_secret='295fb3083f4d4e348acf8afded757d9a')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


# Define a function to display artist's discography
def display_discography(discography):
    for key, value in discography.items():
        print('Album:', key, 'Tracks:', value)


def convert_to_flat(note):
    sharp_to_flat = {
        'C#': 'Db',
        'D#': 'Eb',
        'F#': 'Gb',
        'G#': 'Ab',
        'A#': 'Bb'
    }

    note = sharp_to_flat[note]

    return note



def get_roman_numeral_notation(chords, key):
    note_list = ['A']

# Define a function to retrieve all tracks by an artist
def get_artist_tracks(artist_id):
    discography = {}
    # Get the artist's albums
    albums = sp.artist_albums(artist_id, album_type=['album'], limit=50)  # Adjust limit as needed
    singles = sp.artist_albums(artist_id, album_type=['single'], limit=50)  # Adjust limit as needed

    # Iterate through each album
    for album in albums['items']:

        if album['name'] not in discography and album['name'].find('Live at') == -1:
            discography[album['name']] = {}
            # Get the tracks from the album
            tracks = sp.album_tracks(album['id'])

            for track in tracks['items']:
                discography[album['name']][track['name']] = None


    # for single in singles['items']:
    #     if single['name'] not in discography:
    #         discography[single['name']] = []
    #         # Get the tracks from the album
    #         tracks = sp.album_tracks(single['id'])
    #
    #         # Append track names to the list
    #         track_names = [track['name'] for track in tracks['items']]
    #         discography[single['name']].extend(track_names)

    return discography


# Define a function to retrieve search URL of songs
def get_song_search_urls(artist_dictionary):
    url_list = []
    for artist, discography in artist_dictionary.items():
        for album, tracks in discography.items():
            for song, link in tracks.items():
                link = re.sub(r'\s', '%20', song)
                curr_url = 'https://chordify.net/search/' + artist +'%20' + link
                artist_dictionary[artist][album][song] = curr_url
                url_list.append(curr_url)
    return artist_dictionary


# Define a function to obtain chord URL from html
def get_song_chord_urls(artist_dictionary):
    # Initialize the WebDriver for Firefox (assuming geckodriver is in PATH)
    driver = webdriver.Firefox()

    try:
        for artist, discography in artist_dictionary.items():
            for album, tracks in discography.items():
                for song, url in tracks.items():
                    # Navigate to a webpage
                    driver.get(url)

                    # Sleep script so that contents are loaded properly
                    sleep(1)

                    # Retrieve the page source (HTML content)
                    html_content = driver.page_source

                    # Parse the HTML using BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    counter = 1
                    # Find all <a> tags
                    for link in soup.find_all('a'):
                        # Get the value of the href attribute
                        href = link.get('href')
                        # Print or further process the href value
                        if counter == 31:
                            print(f'chord link for url {url} found: {href}')
                            artist_dictionary[artist][album][song] = href
                        counter += 1

        return artist_dictionary

    finally:
        # Close the browser
        driver.quit()


# Define a function to convert notes to flat for consistency
def convert_to_flat(note):
    # Create dictionary for each sharp's corresponding flat
    sharp_to_flat = {
        'C#': 'Db',
        'D#': 'Eb',
        'F#': 'Gb',
        'G#': 'Ab',
        'A#': 'Bb'
    }

    # find sharp and convert it to its respective flat
    for key, value in sharp_to_flat.items():
        if key in note:
            # Return replacement
            note = note.replace(key, sharp_to_flat[key])

    return note


# Define a function to generate scale based on the key
def get_scale(key):
    root = key
    # Data structures for formatting and generation
    musical_notes = ['A', 'Bb', 'B', 'C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab']
    scale_construction_rules = {'major': [2, 2, 1, 2, 2, 2], 'minor': [2, 1, 2, 2, 1, 2]}
    roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']

    # Data structures to store data
    scale = []
    roman_numeral_dictionary = {}

    # Determine if scale is minor or major
    if 'm' in root:
        scale_type = 'minor'
        root = root.replace('m', '')
    else:
        scale_type = 'major'

    # Convert to flat if note is sharp
    if '#' in root:
        root = convert_to_flat(root)

    # Insert initial note
    scale.append(root)
    roman_numeral_dictionary[root] = roman_numerals[0]
    position = musical_notes.index(root)

    counter = 1
    # Construct the scale based on scale type and rules
    for step in scale_construction_rules[scale_type]:
        position = (position + step) % len(musical_notes)
        scale.append(musical_notes[position])
        roman_numeral_dictionary[musical_notes[position]] = roman_numerals[counter]
        counter += 1

    return scale, roman_numeral_dictionary


# Define a function to convert scale to roman numeral notation
def get_roman_numeral_notation(chords, key):

    # Get scale and dictionary to map chord to numeral notation
    scale, roman_numeral_dictionary = get_scale(key)
    roman_numeral_scale = []

    # Create a regex from the dictionary keys
    regex = re.compile("|".join(map(re.escape, roman_numeral_dictionary.keys())))
    for chord in chords:
        if '#' in chord or 'b' in chord:
            chord = convert_to_flat(chord)
            sharp_flat = 2
        else:
            sharp_flat = 1

        # For each match, look up the corresponding value in the dictionary
        reformatted_chord = regex.sub(lambda match: roman_numeral_dictionary[match.group(0)], chord[:sharp_flat])
        second_half = chord[sharp_flat:]
        reformatted_chord += second_half

        # Convert to lower if chord is minor
        if 'm' in reformatted_chord:
            reformatted_chord = reformatted_chord.replace('m', '')
            reformatted_chord = reformatted_chord.lower()

        # Remove 'MAJ' if found
        if 'MAJ' in reformatted_chord:
            reformatted_chord = reformatted_chord.replace('MAJ', '')
        roman_numeral_scale.append(reformatted_chord)

    return scale, roman_numeral_scale


# Define function to obtain chords from html
def get_song_chords(artist_dictionary):
    # Initialize the WebDriver for Firefox (assuming geckodriver is in PATH)
    driver = webdriver.Firefox()
    pd_data = []
    key_dictionary = {}
    first_chord_dictionary = {}
    try:
        for artist, discography in artist_dictionary.items():
            for album, tracks in discography.items():
                for song, url in tracks.items():
                    song_details = {'chords': None, 'key': None}

                    # Navigate to a webpage
                    driver.get('https://chordify.net' + url)

                    # Sleep script so that contents are loaded properly
                    sleep(1)

                    # Retrieve the page source (HTML content)
                    html_content = driver.page_source

                    # Parse the HTML content using BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Find the div with class="aqpm70f"
                    div_element = soup.find('div', class_='aqpm70f')

                    # Find all span elements with class="chord-label cbg1qdk" within the div
                    if div_element:
                        span_elements = div_element.find_all('span', class_='chord-label cbg1qdk')
                        curr_chords = []
                        # Loop through each found span element
                        for span in span_elements:
                            print('Found span with class="chord-label cbg1qdk" within div with class="aqpm70f":')
                            curr_chords.append(span.text)

                         # Update song details with data
                        reformatted_chords = reformat_chords(curr_chords)
                        key = reformatted_chords[-1]
                        chords = reformatted_chords[:-1]
                        song_details['key'] = key
                        song_details['chords'] = chords

                        # Get scale data
                        scale, roman_numeral_progression = get_roman_numeral_notation(chords, key)
                        song_details['roman'] = roman_numeral_progression
                        song_details['scale'] = scale
                        artist_dictionary[artist][album][song] = song_details

                        # Update pandas data
                        curr_entry = [artist, song, key, roman_numeral_progression]
                        pd_data.append(curr_entry)

                        # Update key dictionary to determine most common keys
                        if key not in key_dictionary:
                            key_dictionary[key] = 1
                        else:
                            key_dictionary[key] += 1
                        key_dictionary = sorted(key_dictionary.items(), key=lambda x: x[1], reverse=True)

                        # Update first chord dictionary to determine most common starter chord
                        first_chord = roman_numeral_progression[0]
                        if first_chord not in first_chord_dictionary:
                            first_chord_dictionary[first_chord] = 1
                        else:
                            first_chord_dictionary[first_chord] += 1
                        first_chord_dictionary = sorted(first_chord_dictionary.items(), key=lambda x: x[1], reverse=True)

                    else:
                        print('Div with class="aqpm70f" not found.')
        df = pd.DataFrame(columns=['artist', 'song', 'key', 'progression'], data=pd_data)
        return artist_dictionary, df, key_dictionary, first_chord_dictionary

    finally:
        # Close the browser
        driver.quit()


# Define a function to reformat unicode characters
def reformat_chords(chords):
    replacements = {'\u2098': 'm', '\u1d50': 'M', '\u1d43': 'A', '\u02b2': 'J', '\u2077': '7', '\u266d': 'b',
                              '\u266f': '#'}
    reformatted_chords = []
    for chord in chords:
        print(chord)
        # Create a regex from the dictionary keys
        regex = re.compile("|".join(map(re.escape, replacements.keys())))

        # For each match, look up the corresponding value in the dictionary
        reformatted_chord = regex.sub(lambda match: replacements[match.group(0)], chord)
        reformatted_chords.append(reformatted_chord)
    return reformatted_chords


# Define function to find patterns in chord progressions using rule mining
def rule_mining(df):
    # Gather progressions from df
    progressions = df['progression'].tolist()

    # Transform progression to df
    te = TransactionEncoder()
    te_ary = te.fit(progressions).transform(progressions)
    progression_df = pd.DataFrame(te_ary, columns=te.columns_)

    # Finding frequent itemsets
    frequent_itemsets = apriori(progression_df, min_support=0.1, use_colnames=True)

    # Generating association rules
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.3)

    # Sorting rules based on support in descending order
    rules_sorted = rules.sort_values(by='support', ascending=False)

    # Save rules to CSV
    rules_sorted.to_csv('rules.csv', index=False)

    return rules_sorted



# Example: Get all tracks by an artist (replace 'ARTIST_ID' with the artist's ID)
artist_id = '4vGrte8FDu062Ntj0RsPiZ'
artist_name = 'polyphia'
artist_dictionary = {}
discography = get_artist_tracks(artist_id)
artist_dictionary[artist_name] = discography

display_discography(discography)
artist_dictionary = get_song_search_urls(artist_dictionary)

artist_dictionary = get_song_chord_urls(artist_dictionary)

artist_dictionary, df, key_dictionary, first_chord_dictionary = get_song_chords(artist_dictionary)

df.to_csv('test.csv', index=False)
with open('test2.json', 'w') as f:
    json.dump(artist_dictionary, f, indent=4)
