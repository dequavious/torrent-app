 #!/bin/bash
echo "Enter your postgres superuser username: "
read username
echo "Enter a password you would like to use for the postgres superuser: "
read password
sudo -u postgres psql --command="ALTER USER ${username} with password '${password}';"

SCRIPT_RELATIVE_DIR=$(dirname "${BASH_SOURCE[0]}")
cd $SCRIPT_RELATIVE_DIR
cd ..

. venv/bin/activate

cd database

if test -f .env; then
    rm .env
fi

echo "POSTGRES_USERNAME=${username}" >> .env
echo "POSTGRES_PASSWORD=${password}" >> .env

python3 setupdb.py
