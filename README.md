# TORRENT APPLICATION
A torrenting application that scrapes the search results of https://www.1337x.to/ and displays the name, seeds, leeches and size for each 
torrent. Users are able to page through the search results and can start a download by double-clicking on the 
torrent they want. Users are also able to start a torrent download manually by uploading a ".torrent" file or by pasting 
a magnet link. Multiple concurrent torrent downloads are possible as well configuring settings such as file priorities, 
adding trackers, enabling sequential downloads, setting upload/download limits, etc. Torrents that have not been removed 
are saved upon exit along with their settings and resume when the app is started again.
## Requirements
### Install chromedriver
1. Find the appropriate `chromedriver` executable for your system from https://googlechromelabs.github.io/chrome-for-testing/#stable and copy the link.
2. Download, extract and move the `chromedriver` executable to `/usr/bin/` using:
    ```
    $ bash scripts/chromedriver.sh <COPIED_LINK>
    ```
### Install other dependencies
1. Open terminal in project directory.
2. Install all system requirements, required python packages and setup PostgreSQL database:
   ```
   $ bash scripts/install.sh
   ```

## How to run application
You can either run the desktop icon that has been created, or:
1. Open terminal in the project directory
2. Run app using:
   ```
   $ bash scripts/run.sh
   ```

* Download a torrent in the search results by double-clicking on it.
