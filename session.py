import os
import shutil
from shutil import SameFileError

import libtorrent as lt

from torrent import Torrent


class Session:
    def start(self):
        self.session.start_dht()

    def stop(self):
        self.session.stop_dht()

    def add_magnet(self, magnet_link, torrent_name=None, priorities=None, sequential=False):
        if not magnet_link:
            raise ValueError("no magnet link provided!")

        try:
            handle = lt.add_magnet_uri(self.session, magnet_link, {'save_path': self.save_path,
                                                                   'storage_mode': lt.storage_mode_t(2)})
            if torrent_name is not None:
                return Torrent(torrent_name, handle, None, magnet_link, None, priorities, sequential)
            else:
                return Torrent(handle.name(), handle, None, magnet_link, None, priorities, sequential)
        except RuntimeError:
            return None

    def add_torrent_file(self, filepath, torrent_name, priorities=None, sequential=False):
        if not os.path.isdir('torrents'):
            os.makedirs('torrents')

        try:
            path = shutil.copy(filepath, 'torrents')
        except SameFileError:
            path = filepath

        try:
            handle = self.session.add_torrent({'ti': lt.torrent_info(path), 'save_path': f'{self.save_path}'})
            return Torrent(torrent_name, handle, lt.torrent_info(path), None, path, priorities, sequential)
        except RuntimeError:
            return None

    def change_save_directory(self, directory):
        self.save_path = directory

    def __init__(self, save_path):
        self.id = 0
        self.torrents = {}
        self.save_path = save_path
        self.session = lt.session()
        self.session.listen_on(6881, 6891)
        self.state = ['queued', 'checking', 'fetching meta-info', 'downloading', 'finished', 'seeding', 'allocating',
                      'checking resume data']

        if not os.path.isdir(f'{save_path}'):
            os.makedirs(f'{save_path}')
