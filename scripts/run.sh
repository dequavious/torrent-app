 #!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[1]}")" ; pwd -P )
cd "$parent_path"
. venv/bin/activate
python3 main.py