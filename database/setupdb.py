import sys

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Incorrect number of arguments used.\n USAGE: python3 setupdb.py <username> [password]\nNB: MAKE SURE "
              "THAT YOUR POSTGRESQL SUPERUSER HAS A PASSWORD SETUP")
        exit(1)

    user = sys.argv[1]
    password = sys.argv[2]

    conn = psycopg2.connect(
        host='localhost',
        user=user,
        password=password)

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()
    cur.execute(sql.SQL('DROP DATABASE IF EXISTS torrent_db;'))
    cur.execute(sql.SQL(f'CREATE DATABASE torrent_db OWNER {user};'))

    conn = psycopg2.connect(
        host='localhost',
        user=user,
        password=password,
        database='torrent_db'
    )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute(sql.SQL('DROP TABLE IF EXISTS settings;\n'
                        'CREATE TABLE IF NOT EXISTS settings\n'
                        '(\n'
                        '"id" SERIAL PRIMARY KEY NOT NULL,\n'
                        '"save_path" text NOT NULL, \n'
                        '"upload_limit" INTEGER,\n'
                        '"download_limit" INTEGER\n'
                        ');'
                        ))
    cur.execute(sql.SQL("INSERT INTO settings(save_path, upload_limit, download_limit) "
                        "VALUES('downloads', NULL, NULL);"))
    cur.execute(sql.SQL('DROP TABLE IF EXISTS torrents CASCADE;\n'
                        'CREATE TABLE IF NOT EXISTS torrents\n'
                        '(\n'
                        '"id" INTEGER PRIMARY KEY NOT NULL,\n'
                        '"name" text NOT NULL,\n'
                        '"magnet_link" text,\n'
                        '"filepath" text,\n'
                        '"upload_limit" INTEGER,\n'
                        '"download_limit" INTEGER,\n'
                        '"sequential" BOOLEAN NOT NULL'
                        ');'
                        ))
    cur.execute(sql.SQL('DROP TABLE IF EXISTS priorities CASCADE;\n'
                        'CREATE TABLE IF NOT EXISTS priorities\n'
                        '(\n'
                        '"id" SERIAL PRIMARY KEY NOT NULL,\n'
                        '"tid" INTEGER,\n'
                        '"fid" INTEGER NOT NULL,\n'
                        '"priority" INTEGER NOT NULL,\n'
                        'CONSTRAINT fk_priorities'
                        '   FOREIGN KEY(tid)'
                        '       REFERENCES torrents(id)'
                        ');'
                        ))
