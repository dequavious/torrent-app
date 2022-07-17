import os
import shutil
from shutil import SameFileError

import libtorrent as lt

from torrent import Torrent


class Session:
    def dht_node_count(self):
        return self.session.status().dht_nodes + self.session.status().dht_node_cache

    def start(self):
        self.session.start_dht()

    def stop(self):
        self.session.stop_dht()

    def set_upload_limit(self, limit):
        self.session.set_upload_rate_limit(limit)

    def set_download_limit(self, limit):
        self.session.set_download_rate_limit(limit)

    def get_upload_limit(self):
        return self.session.upload_rate_limit()

    def get_download_limit(self):
        return self.session.download_rate_limit()

    def add_magnet(self, magnet_link, torrent_name=None, upload=None, download=None, sequential=False, priorities=None):
        if not magnet_link:
            raise ValueError("no magnet link provided!")

        try:
            handle = lt.add_magnet_uri(self.session, magnet_link, {'save_path': self.save_path,
                                                                   'storage_mode': lt.storage_mode_t(2)})
            if torrent_name is not None:
                return Torrent(self.session, torrent_name, handle, None, magnet_link, None, upload=upload,
                               download=download, sequential=sequential, priorities=priorities)
            else:
                return Torrent(self.session, handle.name(), handle, None, magnet_link, None, upload=upload,
                               download=download, sequential=sequential, priorities=priorities)
        except RuntimeError:
            return None

    def add_torrent_file(self, filepath, torrent_name, upload=None, download=None, sequential=False, priorities=None):
        if not os.path.isdir('torrents'):
            os.makedirs('torrents')

        try:
            path = shutil.copy(filepath, 'torrents')
        except SameFileError:
            path = filepath

        try:
            handle = self.session.add_torrent({'ti': lt.torrent_info(path), 'save_path': f'{self.save_path}'})
            return Torrent(self.session, torrent_name, handle, lt.torrent_info(path), None, path, upload=upload,
                           download=download, sequential=sequential, priorities=priorities)
        except RuntimeError:
            return None

    def change_save_directory(self, directory):
        self.save_path = directory

    def __init__(self, save_path, limits):
        self.id = 0
        self.torrents = {}
        self.save_path = save_path
        self.session = lt.session()
        self.session.listen_on(6881, 6891)

        self.session.apply_settings({'dht_restrict_routing_ips': False})
        self.session.apply_settings({'dht_restrict_search_ips': False})

        self.session.add_dht_node(("router.utorrent.com", 6881))
        self.session.add_dht_node(("router.bittorrent.com", 6881))
        self.session.add_dht_node(("router.bitcomet.com", 6881))
        self.session.add_dht_node(("dht.transmissionbt.com", 6881))
        self.session.add_dht_node(('dht.transmission.com', 6881))
        self.session.add_dht_node(("dht.aelitis.com", 6881))

        self.session.add_dht_router("router.utorrent.com", 6881)
        self.session.add_dht_router("router.bittorrent.com", 6881)
        self.session.add_dht_router("router.bitcomet.com", 6881)
        self.session.add_dht_router("dht.transmissionbt.com", 6881)
        self.session.add_dht_router('dht.transmission.com', 6881)
        self.session.add_dht_router("dht.aelitis.com", 6881)

        if not os.path.isdir(f'{save_path}'):
            os.makedirs(f'{save_path}')

        if limits[0] is not None:
            self.set_upload_limit(limits[0])

        if limits[1] is not None:
            self.set_download_limit(limits[1])
