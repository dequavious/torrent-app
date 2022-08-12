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
