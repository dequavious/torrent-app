import time
from threading import Thread

import libtorrent as lt
from urllib.parse import quote


class Torrent:
    def get_metadata(self):
        try:
            while not self.handle.has_metadata():
                time.sleep(1)
            self.info = self.handle.get_torrent_info()
        except RuntimeError:
            pass

    def stop(self):
        self.session.remove_torrent(self.handle)

    def resume(self):
        self.handle.resume()
        self.handle.auto_managed(True)

    def pause(self):
        self.handle.pause()
        self.handle.auto_managed(False)

    def seeding_or_stopped(self):
        try:
            return self.handle.status().state == lt.torrent_status.seeding
        except RuntimeError:
            return True

    def get_files(self):
        files = []
        for i, file in enumerate(self.info.files()):
            files.append(file)
        return files

    def set_file_priority(self, i, value):
        self.handle.file_priority(i, value)

    def get_file_priority(self, i):
        return self.handle.file_priorities()[i]

    def get_file_progress(self, i):
        return self.handle.file_progress()[i]

    def get_peer_info(self):
        return self.handle.get_peer_info()

    def get_trackers(self):
        trackers = []
        for tracker in self.info.trackers():
            trackers.append(tracker.url)
        return trackers

    def set_upload_limit(self, limit):
        self.handle.set_upload_limit(limit)

    def set_download_limit(self, limit):
        self.handle.set_download_limit(limit)

    def get_upload_limit(self):
        return self.handle.upload_limit()

    def get_download_limit(self):
        return self.handle.download_limit()

    def set_sequential_download(self, value):
        self.sequential = value
        self.handle.set_sequential_download(value)

    def add_trackers(self, trackers):
        if self.magnet_link is not None:
            for tracker in trackers:
                self.info.add_tracker(tracker)
                encoded_url = quote(tracker, safe='')
                if not self.magnet_link.__contains__(encoded_url):
                    self.magnet_link += f'&tr={tracker}'
        else:
            decoded_data = lt.bdecode(open(self.filepath, 'rb').read())
            for tracker in trackers:
                if decoded_data.get('announce-list'):
                    if tracker not in decoded_data['announce-list']:
                        decoded_data['announce-list'].append([tracker])
                else:
                    decoded_data['announce-list'] = []
                    decoded_data['announce-list'].append([tracker])

            f = open(self.filepath, "wb")
            f.write(lt.bencode(decoded_data))
            f.close()

    def get_file_priorities(self):
        return self.handle.file_priorities()

    def set_priorities(self, priorities):
        for priority in priorities:
            self.set_file_priority(priority[0], priority[1])

    def move_to_top(self):
        try:
            while self.handle.status().state == lt.torrent_status.downloading_metadata:
                self.handle.queue_position_up()
                time.sleep(1)
        except RuntimeError:
            return True

    def __init__(self, session, name, handle, info, magnet_link, filepath, upload=None, download=None, sequential=False,
                 priorities=None):
        self.state = ['queued', 'checking', 'fetching meta-info', 'downloading', 'finished', 'seeding', 'allocating',
                      'checking resume data']
        self.session = session
        self.name = name
        self.handle = handle
        self.info = info
        self.magnet_link = magnet_link
        self.filepath = filepath

        if priorities is not None:
            self.set_priorities(priorities)

        if upload is not None:
            self.set_upload_limit(upload)
        if download is not None:
            self.set_download_limit(download)

        self.sequential = sequential
        if sequential:
            self.handle.set_sequential_download(True)

        Thread(target=self.move_to_top, daemon=True).start()