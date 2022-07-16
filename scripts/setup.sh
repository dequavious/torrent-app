 #!/bin/sh
parent_path=$( cd "$(dirname "${BASH_SOURCE[1]}")" ; pwd -P )
cd "$parent_path"
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt