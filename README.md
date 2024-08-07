# TuneTracker
TuneTracker is a tool designed to analyze chord progressions of bands and artists. By utilizing rule mining and statistical techniques, it uncovers patterns and insights within musical compositions. The process begins with retrieving an artist's discography from the Spotify API using their Spotify ID, which includes the artist's albums and songs. The song names are then used to scrape chord progressions from chordify.net.

To enhance generalization and results, the chord progressions are converted to Roman numeral notation. For example, a progression of Cm -> Dm -> Gm in the key of C major will be represented as i -> iii -> v in Roman numeral notation. These progressions are treated as buckets, and a rule mining algorithm is employed to discover patterns in the artist's music.

Setup
1. Install Dependencies:
   Begin by executing the requirements.txt file to ensure the necessary requirements are installed:
   pip install -r requirements.txt
   
2. Using the Included Database:
   The music_db.db file includes three artists (Laufey, Polyphia, Mitski). For a trial run, use one of these artists to skip the scraping phase and speed up execution time. The database is set up 
   automatically by the script.

3. Using Your Own Artist:
   If you intend to run the program on an artist of your choosing, you must install a Firefox WebDriver, as it is necessary to pull the chord progressions from the web. You can download it here.

# Execution
1. The execution is simple, simply navigate to the terminal and run the command
   python main.py
2. you will then be prompted to enter an artist's spotify ID and you will be presented with the results on submission.
