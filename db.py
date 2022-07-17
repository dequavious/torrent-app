import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DB:
    def reset(self):
        self.cur.execute(sql.SQL('DROP TABLE IF EXISTS torrents CASCADE;\n'
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
        self.cur.execute(sql.SQL('DROP TABLE IF EXISTS priorities CASCADE;\n'
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

    def get_global_limits(self):
        self.cur.execute(sql.SQL("SELECT upload_limit, download_limit FROM global_limits WHERE id = 1;"))
        return self.cur.fetchall()[0]

    def set_global_upload_limit(self, limit):
        self.cur.execute(sql.SQL(f"UPDATE global_limits SET upload_limit = {limit} WHERE id = 1;"))

    def set_global_download_limit(self, limit):
        self.cur.execute(sql.SQL(f"UPDATE global_limits SET download_limit = {limit} WHERE id = 1;"))

    def get_torrents(self):
        self.cur.execute(sql.SQL("SELECT name, magnet_link, filepath, upload_limit, download_limit, sequential "
                                 "FROM torrents;"))
        return self.cur.fetchall()

    def get_priorities(self, torrent_id):
        self.cur.execute(sql.SQL(f"SELECT fid, priority FROM priorities WHERE tid = {torrent_id}"))
        return self.cur.fetchall()

    def get_save_path(self):
        self.cur.execute(sql.SQL("SELECT directory FROM save_path WHERE id = 1;"))
        return self.cur.fetchall()[0][0]

    def update_save_path(self, new_directory):
        self.cur.execute(sql.SQL(f"UPDATE save_path SET directory = '{new_directory}' WHERE id = 1;"))

    def save(self, torrent_name, torrent_magnet, filepath, priorities, sequential, upload_limit, download_limit):
        self.id += 1
        if torrent_magnet is not None:
            if (upload_limit == -1 or upload_limit == 0) and (download_limit == -1 or download_limit == 0):
                self.cur.execute(sql.SQL(
                    f"INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential) "
                    f"VALUES({self.id}, '{torrent_name}', '{torrent_magnet}', NULL, NULL, NULL, {sequential});"))
            elif upload_limit == -1 or upload_limit == 0:
                self.cur.execute(sql.SQL(
                    f"INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential) "
                    f"VALUES({self.id}, '{torrent_name}', '{torrent_magnet}', NULL, NULL, {download_limit}, {sequential});"))
            elif download_limit == -1 or download_limit == 0:
                self.cur.execute(sql.SQL(
                    f"INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential) "
                    f"VALUES({self.id}, '{torrent_name}', '{torrent_magnet}', NULL, {upload_limit}, NULL, "
                    f"{sequential});"))
            else:
                self.cur.execute(sql.SQL(
                    f"INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential) "
                    f"VALUES({self.id}, '{torrent_name}', NULL, '{filepath}', {upload_limit}, {download_limit}, "
                    f"{sequential});"))
        else:
            if (upload_limit == -1 or upload_limit == 0) and (download_limit == -1 or download_limit == 0):
                self.cur.execute(sql.SQL(
                    f"INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential) "
                    f"VALUES({self.id}, '{torrent_name}', NULL, '{filepath}', NULL, NULL, {sequential});"))
            elif upload_limit == -1 or upload_limit == 0:
                self.cur.execute(sql.SQL(
                    f"INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential) "
                    f"VALUES({self.id}, '{torrent_name}', NULL, '{filepath}', NULL, {download_limit}, {sequential});"))
            elif download_limit == -1 or download_limit == 0:
                self.cur.execute(sql.SQL(
                    f"INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential) "
                    f"VALUES({self.id}, '{torrent_name}', NULL, '{filepath}', {upload_limit}, NULL, {sequential});"))
            else:
                self.cur.execute(sql.SQL(
                    f"INSERT INTO torrents(id, name, magnet_link, filepath, upload_limit, download_limit, sequential) "
                    f"VALUES({self.id}, '{torrent_name}', NULL, '{filepath}', {upload_limit}, {download_limit}, "
                    f"{sequential});"))
        for i, priority in enumerate(priorities):
            self.cur.execute(sql.SQL(f"INSERT INTO priorities(tid, fid, priority) "
                                     f"VALUES({self.id}, {i}, {priority});"))

    def __init__(self):
        self.id = 0

        self.conn = psycopg2.connect(
            host='localhost',
            user='postgres',
            password='password',
            database='torrent_db'
        )

        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur = self.conn.cursor()
