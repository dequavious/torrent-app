 #!/bin/bash
sudo apt update
sudo apt install python3-venv -y
sudo apt install postgresql -y
sudo apt-get install postgresql postgresql-contrib -y
sudo apt-get install libpq-dev python3-dev -y

SCRIPT_RELATIVE_DIR=$(dirname "${BASH_SOURCE[0]}")
cd $SCRIPT_RELATIVE_DIR
cd ..

python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

bash scripts/setup_db.sh

cd ~/Desktop
echo "[Desktop Entry]
      Version=1.0
      Exec=bash ${SCRIPT_RELATIVE_DIR}/run.sh
      Name=Torrent App
      GenericName=Torrent App
      Comment=Search/download torrents
      Encoding=UTF-8
      Terminal=false
      Type=Application
      Categories=Application;Torrenting;" > torrent_app.desktop
gio set torrent_app.desktop metadata::trusted true
chmod a+x torrent_app.desktop

