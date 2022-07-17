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
                                 '"type" text NOT NULL\n'
                                 ');'
                                 ))
        self.cur.execute(sql.SQL('DROP TABLE IF EXISTS magnets CASCADE;\n'
                                 'CREATE TABLE IF NOT EXISTS magnets\n'
                                 '(\n'
                                 '"id" SERIAL PRIMARY KEY NOT NULL,\n'
                                 '"tid" INTEGER,\n'
                                 '"magnet_link" text NOT NULL,\n'
                                 'CONSTRAINT fk_magnet'
                                 '   FOREIGN KEY(tid)'
                                 '       REFERENCES torrents(id)'
                                 '       ON DELETE CASCADE'
                                 ');'
                                 ))
        self.cur.execute(sql.SQL('DROP TABLE IF EXISTS files CASCADE;\n'
                                 'CREATE TABLE IF NOT EXISTS files\n'
                                 '(\n'
                                 '"id" SERIAL PRIMARY KEY NOT NULL,\n'
                                 '"tid" INTEGER,\n'
                                 '"filepath" text NOT NULL,\n'
                                 'CONSTRAINT fk_file'
                                 '   FOREIGN KEY(tid)'
                                 '       REFERENCES torrents(id)'
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
        self.cur.execute(sql.SQL('DROP TABLE IF EXISTS sequential;\n'
                                 'CREATE TABLE IF NOT EXISTS sequential\n'
                                 '(\n'
                                 '"id" SERIAL PRIMARY KEY NOT NULL,\n'
                                 '"tid" INTEGER NOT NULL,\n'
                                 'CONSTRAINT fk_seq'
                                 '   FOREIGN KEY(tid)'
                                 '       REFERENCES torrents(id)'
                                 ');'
                                 ))
        self.cur.execute(sql.SQL('DROP TABLE IF EXISTS torrent_limits;\n'
                                 'CREATE TABLE IF NOT EXISTS torrent_limits\n'
                                 '(\n'
                                 '"id" SERIAL PRIMARY KEY NOT NULL,\n'
                                 '"tid" INTEGER NOT NULL,\n'
                                 '"upload_limit" INTEGER,\n'
                                 '"download_limit" INTEGER,\n'
                                 'CONSTRAINT fk_lim'
                                 '   FOREIGN KEY(tid)'
                                 '       REFERENCES torrents(id)'
                                 ');'
                                 ))

    def get_global_limits(self):
        self.cur.execute(sql.SQL("SELECT upload_limit, download_limit FROM global_limits WHERE id = 1;"))
        return self.cur.fetchall()[0]

    def get_torrent_limits(self, torrent_id):
        self.cur.execute(sql.SQL(f"SELECT upload_limit, download_limit FROM torrent_limits WHERE tid = {torrent_id};"))
        return self.cur.fetchall()[0]

    def set_global_upload_limit(self, limit):
        self.cur.execute(sql.SQL(f"UPDATE global_limits SET upload_limit = {limit} WHERE id = 1;"))

    def set_global_download_limit(self, limit):
        self.cur.execute(sql.SQL(f"UPDATE global_limits SET download_limit = {limit} WHERE id = 1;"))

    def get_torrents(self):
        self.cur.execute(sql.SQL("SELECT name, magnet_link, filepath, m.tid, f.tid "
                                 "FROM torrents t JOIN (magnets m FULL OUTER JOIN files f USING (tid)) "
                                 "ON t.id = m.tid OR t.id = f.tid"))
        return self.cur.fetchall()

    def get_priorities(self, torrent_id):
        self.cur.execute(sql.SQL(f"SELECT fid, priority FROM priorities WHERE tid = {torrent_id}"))
        return self.cur.fetchall()

    def get_sequential(self, torrent_id):
        self.cur.execute(sql.SQL(f"SELECT tid FROM sequential WHERE tid = {torrent_id}"))
        return self.cur.fetchall()

    def get_save_path(self):
        self.cur.execute(sql.SQL("SELECT directory FROM save_path WHERE id = 1;"))
        return self.cur.fetchall()[0][0]

    def update_save_path(self, new_directory):
        self.cur.execute(sql.SQL(f"UPDATE save_path SET directory = '{new_directory}' WHERE id = 1;"))

    def save(self, torrent_name, torrent_magnet, filepath, priorities, sequential, upload_limit, download_limit):
        self.id += 1
        if torrent_magnet is not None:
            self.cur.execute(sql.SQL(f"INSERT INTO torrents(id, name, type) "
                                     f"VALUES({self.id}, '{torrent_name}', 'magnet');"))
            self.cur.execute(sql.SQL(f"INSERT INTO magnets(tid, magnet_link) VALUES({self.id}, '{torrent_magnet}');"))
        else:
            self.cur.execute(sql.SQL(f"INSERT INTO torrents(id, name, type) "
                                     f"VALUES({self.id}, '{torrent_name}', 'file');"))
            self.cur.execute(sql.SQL(f"INSERT INTO files(tid, filepath) VALUES({self.id}, '{filepath}');"))
        for i, priority in enumerate(priorities):
            self.cur.execute(sql.SQL(f"INSERT INTO priorities(tid, fid, priority) "
                                     f"VALUES({self.id}, {i}, {priority});"))
        if sequential:
            self.cur.execute(sql.SQL(f"INSERT INTO sequential(tid) VALUES({self.id});"))

        if (upload_limit == -1 or upload_limit == 0) and (download_limit == -1 or download_limit == 0):
            self.cur.execute(sql.SQL(f"INSERT INTO torrent_limits(tid, upload_limit, download_limit) "
                                     f"VALUES({self.id}, NULL, NULL);"))
        elif upload_limit == -1 or upload_limit == 0:
            self.cur.execute(sql.SQL(f"INSERT INTO torrent_limits(tid, upload_limit, download_limit) "
                                     f"VALUES({self.id}, NULL, {download_limit});"))
        elif download_limit == -1 or download_limit == 0:
            self.cur.execute(sql.SQL(f"INSERT INTO torrent_limits(tid, upload_limit, download_limit) "
                                     f"VALUES({self.id}, {upload_limit}, NULL);"))
        else:
            self.cur.execute(sql.SQL(f"INSERT INTO torrent_limits(tid, upload_limit, download_limit) "
                                     f"VALUES({self.id}, {upload_limit}, {download_limit});"))

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
