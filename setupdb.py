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

    cur.execute(sql.SQL('DROP TABLE IF EXISTS save_path;\n'
                        'CREATE TABLE IF NOT EXISTS save_path\n'
                        '(\n'
                        '"id" SERIAL PRIMARY KEY NOT NULL,\n'
                        '"directory" text NOT NULL\n'
                        ');'
                        ))
    cur.execute(sql.SQL("INSERT INTO save_path(directory) VALUES('downloads');"))
    cur.execute(sql.SQL('DROP TABLE IF EXISTS global_limits;\n'
                        'CREATE TABLE IF NOT EXISTS global_limits\n'
                        '(\n'
                        '"id" SERIAL PRIMARY KEY NOT NULL,\n'
                        '"upload_limit" INTEGER,\n'
                        '"download_limit" INTEGER\n'
                        ');'
                        ))
    cur.execute(sql.SQL("INSERT INTO global_limits(upload_limit, download_limit) VALUES(NULL, NULL);"))
    cur.execute(sql.SQL('DROP TABLE IF EXISTS torrents CASCADE;\n'
                        'CREATE TABLE IF NOT EXISTS torrents\n'
                        '(\n'
                        '"id" INTEGER PRIMARY KEY NOT NULL,\n'
                        '"name" text NOT NULL,\n'
                        '"type" text NOT NULL\n'
                        ');'
                        ))
    # cur.execute(sql.SQL('DROP TABLE IF EXISTS magnets CASCADE;\n'
    #                     'CREATE TABLE IF NOT EXISTS magnets\n'
    #                     '(\n'
    #                     '"id" SERIAL PRIMARY KEY NOT NULL,\n'
    #                     '"tid" INTEGER,\n'
    #                     '"magnet_link" text NOT NULL,\n'
    #                     'CONSTRAINT fk_magnet'
    #                     '   FOREIGN KEY(tid)'
    #                     '       REFERENCES torrents(id)'
    #                     '       ON DELETE CASCADE'
    #                     ');'
    #                     ))
    # cur.execute(sql.SQL('DROP TABLE IF EXISTS files CASCADE;\n'
    #                     'CREATE TABLE IF NOT EXISTS files\n'
    #                     '(\n'
    #                     '"id" SERIAL PRIMARY KEY NOT NULL,\n'
    #                     '"tid" INTEGER,\n'
    #                     '"filepath" text NOT NULL,\n'
    #                     'CONSTRAINT fk_file'
    #                     '   FOREIGN KEY(tid)'
    #                     '       REFERENCES torrents(id)'
    #                     ');'
    #                     ))
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
    # cur.execute(sql.SQL('DROP TABLE IF EXISTS sequential;\n'
    #                     'CREATE TABLE IF NOT EXISTS sequential\n'
    #                     '(\n'
    #                     '"id" SERIAL PRIMARY KEY NOT NULL,\n'
    #                     '"tid" INTEGER NOT NULL,\n'
    #                     'CONSTRAINT fk_seq'
    #                     '   FOREIGN KEY(tid)'
    #                     '       REFERENCES torrents(id)'
    #                     ');'
    #                     ))
    # cur.execute(sql.SQL('DROP TABLE IF EXISTS torrent_limits;\n'
    #                     'CREATE TABLE IF NOT EXISTS torrent_limits\n'
    #                     '(\n'
    #                     '"id" SERIAL PRIMARY KEY NOT NULL,\n'
    #                     '"tid" INTEGER NOT NULL,\n'
    #                     '"upload_limit" INTEGER,\n'
    #                     '"download_limit" INTEGER,\n'
    #                     'CONSTRAINT fk_lim'
    #                     '   FOREIGN KEY(tid)'
    #                     '       REFERENCES torrents(id)'
    #                     ');'
    #                     ))
