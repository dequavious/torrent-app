# TORRENT APPLICATION
A torrenting application that scrapes the search results of https://www.1377x.to/ and displays the name, seeds, leeches and size for each 
torrent. Users are able to page through the search results and can start a download by double-clicking on the 
torrent they want. Users are also able to start a torrent download manually by uploading a ".torrent" file or by pasting 
a magnet link. Multiple concurrent torrent downloads are possible as well configuring settings such as file priorities, 
adding trackers, enabling sequential downloads, setting upload/download limits, etc. Torrents that have not been removed 
are saved upon exit along with their settings and resume when the app is started again.
## Requirements
1. Open terminal in project directory.
2. Install all system requirements and required python packages:
   ```
   $ bash scripts/install.sh
   ```

### PostgreSQL database setup
1. Open terminal in project directory.
2. Set the PostgreSQL superuser password and create the database to store all relevant torrent settings and info using
   ```
   $ bash scripts/setup_db.sh
   ```

## How to run application
1. Open terminal in the project directory
2. Run app using:
   ```
   $ bash scripts/run.sh
   ```

* Download a torrent in the search results by double-clicking on it.
