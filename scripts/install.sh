 #!/bin/bash
sudo apt update
sudo apt install python3-venv -y
sudo apt install postgresql -y
sudo apt-get install postgresql postgresql-contrib -y
sudo apt-get install libpq-dev python3-dev -y

parent_path=$( cd "$(dirname "${BASH_SOURCE[1]}")" ; pwd -P )
cd "$parent_path"
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
