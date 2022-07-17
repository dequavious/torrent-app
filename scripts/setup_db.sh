 #!/bin/bash
echo "Enter your postgres superuser username: "
read username
echo "Enter a password you would like to use for the postgres superuser: "
read password
sudo -u postgres psql --command="ALTER USER ${username} with password '${password}';"

parent_path=$( cd "$(dirname "${BASH_SOURCE[1]}")" ; pwd -P )
cd "$parent_path"
. venv/bin/activate
python3 database/setupdb.py  ${username} ${password}
