 #!/bin/bash
echo "Enter your postgres superuser username: "
read superuser_username
echo "Enter a password you would like to use for the postgres superuser: "
read superuser_password

sudo -u postgres psql --command="ALTER USER ${superuser_username} with password '${superuser_password}'";

echo "Enter a username you would like to use for the database: "
read username
echo "Enter a password you would like to use for this user: "
read password

sudo -u postgres psql --command="
DO
\$do$
BEGIN
   IF EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = '${username}') THEN
	  ALTER USER ${username} WITH PASSWORD '${password}';
   ELSE
   CREATE USER ${username} WITH PASSWORD '${username}';
   END IF;
END
\$do\$;"

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
echo "POSTGRES_SUPER_USERNAME=${superuser_username}" >> .env
echo "POSTGRES_SUPER_PASSWORD=${superuser_password}" >> .env

python3 setupdb.py
