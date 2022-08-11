import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

if __name__ == "__main__":
    load_dotenv()

    username = os.getenv('POSTGRES_USERNAME')
    password = os.getenv('POSTGRES_PASSWORD')

    conn = psycopg2.connect(
        host='localhost',
        user=username,
        password=password)

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()
    cur.execute("""DROP DATABASE IF EXISTS torrent_db;""")
    cur.execute(f"""CREATE DATABASE torrent_db OWNER {username};""")

    conn = psycopg2.connect(
        host='localhost',
        user=username,
        password=password,
        database='torrent_db'
    )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("""DROP TABLE IF EXISTS settings;
                    CREATE TABLE settings
                    (
                    "id" SERIAL PRIMARY KEY NOT NULL,
                    "save_path" text NOT NULL,
                    "upload_limit" INTEGER,
                    "download_limit" INTEGER
                    );""")
    cur.execute("""INSERT INTO settings(save_path, upload_limit, download_limit) VALUES('downloads', NULL, NULL);""")
    cur.execute("""DROP TABLE IF EXISTS torrents CASCADE;
                    CREATE TABLE torrents
                    (
                    "id" INTEGER PRIMARY KEY NOT NULL,
                    "name" text NOT NULL,
                    "magnet_link" text,
                    "filepath" text,
                    "upload_limit" INTEGER,
                    "download_limit" INTEGER,
                    "sequential" BOOLEAN NOT NULL
                    );""")
    cur.execute("""DROP TABLE IF EXISTS priorities CASCADE;
                    CREATE TABLE priorities
                    (
                    "id" SERIAL PRIMARY KEY NOT NULL,
                    "tid" INTEGER,
                    "fid" INTEGER NOT NULL,
                    "priority" INTEGER NOT NULL,
                    CONSTRAINT fk_priorities
                       FOREIGN KEY(tid)
                           REFERENCES torrents(id)
                    );""")
