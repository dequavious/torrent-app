import os
import shutil
import time
from shutil import SameFileError
from threading import Thread

import libtorrent as lt

from torrent import Torrent


class Session:
    def dht_node_count(self):
        return self.session.status().dht_nodes + self.session.status().dht_node_cache

    def start(self):
        self.session.start_dht()
        self.session.start_lsd()

    def stop(self):
        self.session.stop_dht()
        self.session.stop_lsd()

    def add_magnet(self, magnet_link, torrent_name=None, priorities=None, sequential=False):
        if not magnet_link:
            raise ValueError("no magnet link provided!")

        try:
            handle = lt.add_magnet_uri(self.session, magnet_link, {'save_path': self.save_path,
                                                                   'storage_mode': lt.storage_mode_t(2)})
            if torrent_name is not None:
                return Torrent(self.session, torrent_name, handle, None, magnet_link, None, priorities, sequential)
            else:
                return Torrent(self.session, handle.name(), handle, None, magnet_link, None, priorities, sequential)
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
            return Torrent(self.session, torrent_name, handle, lt.torrent_info(path), None, path, priorities, sequential)
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
        self.session.apply_settings({'dht_restrict_routing_ips': False})
        self.session.apply_settings({'dht_restrict_search_ips': False})
        self.session.add_dht_router("router.utorrent.com", 6881)
        self.session.add_dht_router("router.bittorrent.com", 6881)
        self.session.add_dht_router("router.bitcomet.com", 6881)
        self.session.add_dht_router("dht.transmissionbt.com", 6881)
        self.session.add_dht_router('dht.transmission.com', 6881)
        self.session.add_dht_router("dht.aelitis.com", 6881)

        if not os.path.isdir(f'{save_path}'):
            os.makedirs(f'{save_path}')
