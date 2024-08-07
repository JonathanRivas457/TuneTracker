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
import sqlite3
import ast


# Initialize the Spotify client
client_credentials_manager = SpotifyClientCredentials(client_id='98c92df339b44755b057c9e2be8a9d24', client_secret='295fb3083f4d4e348acf8afded757d9a')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


# Define a function to display artist's discography
def display_discography(discography):
    for key, value in discography.items():
        print('Album:', key, 'Tracks:', value)


# Define a function to retrieve all tracks by an artist
def get_artist_tracks(artist_id):
    discography = {}
    # Get the artist's albums
    albums = sp.artist_albums(artist_id, album_type=['album'], limit=50)  # Adjust limit as needed
    # singles = sp.artist_albums(artist_id, album_type=['single'], limit=50)

    # Get artist name
    artist_name = sp.artist(artist_id)['name']

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

    return discography, artist_name


# Define a function to retrieve search URL of songs
def construct_song_search_urls(artist_dictionary):
    url_list = []
    for artist, discography in artist_dictionary.items():
        for album, tracks in discography.items():
            for song, link in tracks.items():
                link = re.sub(r'\s', '%20', song)
                curr_url = 'https://chordify.net/search/' + artist + '%20' + link
                artist_dictionary[artist][album][song] = curr_url
                url_list.append(curr_url)
    return artist_dictionary


# Define a function to obtain chord URL from html
def scrape_song_chord_urls(artist_dictionary):
    # Initialize the WebDriver for Firefox (assuming geckodriver is in PATH)
    driver = webdriver.Firefox()

    try:
        for artist, discography in artist_dictionary.items():
            for album, tracks in discography.items():
                for song, url in tracks.items():
                    # Navigate to a webpage
                    driver.get(url)

                    # Sleep script so that contents are loaded properly
                    sleep(3)

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
def scrape_song_chords(artist_dictionary):
    # Initialize the WebDriver for Firefox (assuming geckodriver is in PATH)
    driver = webdriver.Firefox()
    progressions = []
    key_dictionary = {}
    first_chord_dictionary = {}
    try:
        for artist, discography in artist_dictionary.items():
            for album, tracks in discography.items():
                for song, url in tracks.items():
                    song_details = {}

                    # Navigate to a webpage
                    driver.get('https://chordify.net' + url)

                    # Sleep script so that contents are loaded properly
                    sleep(1)

                    # Retrieve the page source (HTML content)
                    html_content = driver.page_source

                    # Parse the HTML content using BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Find the div with class="aqpm70f"
                    div_element = soup.find('dl', class_='d6kp0is')

                    # Find all span elements with class="chord-label cbg1qdk" within the div
                    if div_element:

                        span_elements = div_element.find_all('span', class_='cbg1qdk ct1wuqa')
                        curr_chords = []
                        # Loop through each found span element
                        for span in span_elements:
                            print('Found span with class="chord-label cbg1qdk" within div with class="c1kzc79v":')
                            curr_chords.append(span.text)
                            # Update song details with data
                            reformatted_chords = reformat_chords(curr_chords)
                            print(reformatted_chords)
                            key = reformatted_chords[-1]
                            chords = reformatted_chords[:-1]

                        # Get scale data
                        scale, roman_numeral_progression = get_roman_numeral_notation(chords, key)
                        artist_dictionary[artist][album][song] = song_details
                        song_details['key'] = key
                        song_details['chords'] = chords
                        song_details['roman_numeral_progression'] = roman_numeral_progression
                        song_details['scale'] = scale

                        progressions.append(roman_numeral_progression)

                        # Update key dictionary to determine most common keys
                        if key not in key_dictionary:
                            key_dictionary[key] = 1
                        else:
                            key_dictionary[key] += 1

                        # Update first chord dictionary to determine most common starter chord
                        first_chord = roman_numeral_progression[0]
                        if first_chord not in first_chord_dictionary:
                            first_chord_dictionary[first_chord] = 1
                        else:
                            first_chord_dictionary[first_chord] += 1

                        artist_dictionary[artist][album][song] = song_details

        return artist_dictionary, key_dictionary, first_chord_dictionary, progressions
    finally:
        # Close the browser
        driver.quit()


def test_scrape():
    with open('test3.json', 'r') as f:
        artist_dictionary = json.load(f)
    key_dictionary = {}
    first_chord_dictionary = {}
    progressions = []
    for artist, discography in artist_dictionary.items():
        for album, tracks in discography.items():
            for song, details in tracks.items():
                chords = artist_dictionary[artist][album][song]['chords']
                key = artist_dictionary[artist][album][song]['key']
                scale, roman_numeral_progression = get_roman_numeral_notation(chords, key)
                artist_dictionary[artist][album][song]['roman'] = roman_numeral_progression
                artist_dictionary[artist][album][song]['scale'] = scale

                progressions.append(roman_numeral_progression)

                # Update key dictionary to determine most common keys
                if key not in key_dictionary:
                    key_dictionary[key] = 1
                else:
                    key_dictionary[key] += 1

                # Update first chord dictionary to determine most common starter chord
                first_chord = roman_numeral_progression[0]
                if first_chord not in first_chord_dictionary:
                    first_chord_dictionary[first_chord] = 1
                else:
                    first_chord_dictionary[first_chord] += 1

    # Sort dictionaries and create DF
    key_dictionary = sorted(key_dictionary.items(), key=lambda x: x[1], reverse=True)
    first_chord_dictionary = sorted(first_chord_dictionary.items(), key=lambda x: x[1], reverse=True)

    return artist_dictionary, key_dictionary, first_chord_dictionary, progressions


# Define function to populate database with scraped data
def populate_database(spotify_id, db_path):

    artist_dictionary = {}

    discography, artist_name = get_artist_tracks(spotify_id)
    artist_dictionary[artist_name] = discography

    display_discography(discography)
    artist_dictionary = construct_song_search_urls(artist_dictionary)

    artist_dictionary = scrape_song_chord_urls(artist_dictionary)

    artist_dictionary, key_dictionary, first_chord_dictionary, progressions = scrape_song_chords(artist_dictionary)

    # Connect to the database (or create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Populate database with scraped data
    for artist, discography in artist_dictionary.items():
        cursor.execute('''
            INSERT INTO artist (artist, spotify_id)
            VALUES (?, ?)
            ''', (artist_name, spotify_id))
        artist_id = cursor.lastrowid

        for album, tracks in discography.items():
            cursor.execute('''
                INSERT INTO album (artist_id, album)
                VALUES (?,?)
                ''', (artist_id, album))
            album_id = cursor.lastrowid

            for song, details in tracks.items():
                key = details['key']
                progression = details['roman_numeral_progression']
                cursor.execute('''
                                INSERT INTO song (artist_id, album_id, song, key, progression)
                                VALUES (?,?,?,?,?)
                                ''', (artist_id, album_id, song, key, str(progression)))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    rules = rule_mining(progressions)
    return rules, key_dictionary, first_chord_dictionary


# Define function to populate database with scraped data
def test_populate_database(spotify_id, artist_name, db_path):

    artist_dictionary, key_dictionary, first_chord_dictionary, progressions = test_scrape()

    # Connect to the database (or create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Populate database with scraped data
    for artist, discography in artist_dictionary.items():
        cursor.execute('''
            INSERT INTO artist (artist, spotify_id)
            VALUES (?, ?)
            ''', (artist_name, spotify_id))
        artist_id = cursor.lastrowid

        for album, tracks in discography.items():
            cursor.execute('''
                INSERT INTO album (artist_id, album)
                VALUES (?,?)
                ''', (artist_id, album))
            album_id = cursor.lastrowid

            for song, details in tracks.items():
                key = details['key']
                progression = details['roman_numeral_progression']
                cursor.execute('''
                                INSERT INTO song (artist_id, album_id, song, key, progression)
                                VALUES (?,?,?,?,?)
                                ''', (artist_id, album_id, song, key, str(progression)))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    rules_sorted = rule_mining(progressions)

    return rules_sorted, key_dictionary, first_chord_dictionary


# Define function to setup database
def database_setup(db_path):
    # Connect to the database (or create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the artist table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS artist (
                       id INTEGER PRIMARY KEY,
                       artist TEXT NOT NULL,
                       spotify_id TEXT NOT NULL
                   )
                   ''')

    # Create the album table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS album (
                       id INTEGER PRIMARY KEY,
                       artist_id INTEGER,
                       album TEXT NOT NULL,
                       FOREIGN KEY (artist_id) REFERENCES artist (id)
                   )
                   ''')

    # Create the song table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS song (
                       id INTEGER PRIMARY KEY,
                       artist_id INTEGER,
                       album_id INTEGER,
                       song TEXT NOT NULL,
                       key TEXT,
                       progression TEXT,
                       FOREIGN KEY (artist_id) REFERENCES artist (id),
                       FOREIGN KEY (album_id) REFERENCES album (id)
                   )
                   ''')
    conn.commit()
    conn.close()


def pull_from_database(spotify_id, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT* FROM artist WHERE spotify_id = ? LIMIT 1
    ''', (spotify_id,)
    )

    result = cursor.fetchone()
    artist_id = result[0]
    artist_name = result[1]

    cursor.execute('''
    SELECT* FROM song WHERE artist_id = ?
    ''', (artist_id,))

    result = cursor.fetchall()

    progressions = []
    key_dictionary = {}
    first_chord_dictionary = {}
    for song in result:
        curr_progression = ast.literal_eval(song[5])
        key = song[4]
        first_chord = curr_progression[0]

        progressions.append(curr_progression)

        # Update key dictionary to determine most common keys
        if key not in key_dictionary:
            key_dictionary[key] = 1
        else:
            key_dictionary[key] += 1

        # Update first chord dictionary to determine most common starter chord
        if first_chord not in first_chord_dictionary:
            first_chord_dictionary[first_chord] = 1
        else:
            first_chord_dictionary[first_chord] += 1

        # Sort dictionaries and create DF
    key_dictionary = sorted(key_dictionary.items(), key=lambda x: x[1], reverse=True)
    first_chord_dictionary = sorted(first_chord_dictionary.items(), key=lambda x: x[1], reverse=True)

    return progressions, key_dictionary, first_chord_dictionary


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
def rule_mining(progressions):

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


def format_rules(rules):
    formatted_rules = {}
    print(f'length? {len(rules)}')
    for row in rules.itertuples():
        curr_entry = {'antecedents': list(row.antecedents), 'consequents': list(row.consequents),
                      'support': round(row.support, 2), 'confidence': round(row.confidence, 2)}

        formatted_rules[row.Index] = curr_entry

    print(f'formatted: {formatted_rules}')
    return formatted_rules


def run_core(spotify_id):
    # setup database
    db_path = 'db/music_database.db'
    database_setup(db_path)

    # Check if requested artist exists in database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"SELECT 1 FROM artist WHERE spotify_id = ? LIMIT 1"
    cursor.execute(query, (spotify_id,))
    result = cursor.fetchone()
    conn.close()

    # Scrape artist data if not in database
    if result is None:
        print('artist does not exist in database, beginning database population...')
        rules, key_dictionary, first_chord_dictionary = populate_database(spotify_id, db_path)
        # rules, key_dictionary, first_chord_dictionary = test_populate_database(spotify_id, artist_name, db_path)
        print(key_dictionary)
        print(first_chord_dictionary)
        print(rules)

    # Pull data if artist exists in database
    else:
        print('artist exists in database...')
        progressions, key_dictionary, first_chord_dictionary = pull_from_database(spotify_id, db_path)
        print(progressions)
        rules = rule_mining(progressions)
        print(first_chord_dictionary)


# spotify_id = '7gW0r5CkdEUMm42w9XpyZO'
# run_core(spotify_id)