import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DB:
    def reset(self):
        self.cur.execute("""DROP TABLE IF EXISTS torrents CASCADE;
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
        self.cur.execute("""DROP TABLE IF EXISTS priorities CASCADE;
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

    def get_global_limits(self):
        self.cur.execute("""SELECT upload_limit, download_limit FROM settings WHERE id = 1;""")
        return self.cur.fetchone()

    def set_global_upload_limit(self, limit):
        self.cur.execute(f"""UPDATE settings SET upload_limit = {limit} WHERE id = 1;""")

    def set_global_download_limit(self, limit):
        self.cur.execute(f"""UPDATE settings SET download_limit = {limit} WHERE id = 1;""")

    def get_torrents(self):
        self.cur.execute("""SELECT name, magnet_link, filepath, upload_limit, download_limit, sequential FROM torrents;
                         """)
        return self.cur.fetchall()

    def get_priorities(self, torrent_id):
        self.cur.execute(f"""SELECT fid, priority FROM priorities WHERE tid = {torrent_id}""")
        return self.cur.fetchall()

    def get_save_path(self):
        self.cur.execute("""SELECT save_path FROM settings WHERE id = 1;""")
        return self.cur.fetchone()[0]

    def update_save_path(self, new_directory):
        self.cur.execute(f"""UPDATE settings SET save_path = '{new_directory}' WHERE id = 1;""")

    def save(self, torrent_name, torrent_magnet, filepath, priorities, sequential, upload_limit, download_limit):
        self.id += 1
        if torrent_magnet is not None:
            if (upload_limit == -1 or upload_limit == 0) and (download_limit == -1 or download_limit == 0):
                self.cur.execute(
                    f"""INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential)
                    VALUES({self.id}, '{torrent_name}', '{torrent_magnet}', NULL, NULL, NULL, {sequential});""")
            elif upload_limit == -1 or upload_limit == 0:
                self.cur.execute(
                    f"""INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential)
                    VALUES({self.id}, '{torrent_name}', '{torrent_magnet}', NULL, NULL, {download_limit}, {sequential});
                    """)
            elif download_limit == -1 or download_limit == 0:
                self.cur.execute(
                    f"""INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential)
                    VALUES({self.id}, '{torrent_name}', '{torrent_magnet}', NULL, {upload_limit}, NULL,
                    {sequential});""")
            else:
                self.cur.execute(
                    f"""INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential)
                    VALUES({self.id}, '{torrent_name}', NULL, '{filepath}', {upload_limit}, {download_limit},
                    {sequential});""")
        else:
            if (upload_limit == -1 or upload_limit == 0) and (download_limit == -1 or download_limit == 0):
                self.cur.execute(
                    f"""INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential)
                    VALUES({self.id}, '{torrent_name}', NULL, '{filepath}', NULL, NULL, {sequential})""")
            elif upload_limit == -1 or upload_limit == 0:
                self.cur.execute(
                    f"""INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential)
                    VALUES({self.id}, '{torrent_name}', NULL, '{filepath}', NULL, {download_limit}, {sequential});""")
            elif download_limit == -1 or download_limit == 0:
                self.cur.execute(
                    f"""INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential)
                    VALUES({self.id}, '{torrent_name}', NULL, '{filepath}', {upload_limit}, NULL, {sequential});""")
            else:
                self.cur.execute(
                    f"""INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential)
                    VALUES({self.id}, '{torrent_name}', NULL, '{filepath}', {upload_limit}, {download_limit},
                    {sequential});""")
        for i, priority in enumerate(priorities):
            self.cur.execute(f"""INSERT INTO priorities(tid, fid, priority) VALUES({self.id}, {i}, {priority});""")

    def __init__(self):
        self.id = 0

        load_dotenv()

        self.conn = psycopg2.connect(
            host='localhost',
            user=os.getenv('POSTGRES_USERNAME'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database='torrent_db'
        )

        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur = self.conn.cursor()
