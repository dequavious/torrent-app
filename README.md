# TORRENT APPLICATION
A torrenting application that scrapes the search results of https://www.1377x.to/ and displays the name, seeds, leeches and size for each 
torrent. Users are able to page through the search results and can start a download by double-clicking on the 
torrent they want. Users are also able to start a torrent download manually by uploading a ".torrent" file or by pasting 
a magnet link. Multiple concurrent torrent downloads are possible as well configuring settings such as file priorities, 
adding trackers, enabling sequential downloads, setting upload/download limits, etc. Torrents that have not been removed 
are saved upon exit along with their settings and resume when the app is started again.
## REQUIREMENTS
1. Open terminal in project directory.
2. Install all system requirements:
   ```
   $ bash scripts/install.sh
   ```
3. Create a virtual environment and install required packages, using:
   ```
   $ bash scripts/setup.sh
   ```

### PostgreSQL SETUP
1. Open terminal in project directory.
2. Set the PostgreSQL superuser password
   ```
   $ sudo -u postgres psql --command="ALTER USER postgres with password '<password>'";
   ```
   Where _\<password\>_ is the password you want to use.

   **NOTE:** The default PostgreSQL superuser on linux is 'postgres'


3. To create the database to store all relevant torrent info use:
    ```
    $ python3 setupdb.py <username> <password>
    ```
   Where _\<username\>_ and _\<password\>_ are compulsory parameters that correspond to your PostgreSQL superuser's username 
   and password.

## STEPS TO RUN APPLICATION
1. Open terminal in the project directory
2. Run app using:
   ```
   $ bash scripts/run.sh
   ```

* Download a torrent in the search results by double-clicking on it.
