import time

import libtorrent as lt


class Torrent:
    def get_metadata(self):
        try:
            while not self.handle.has_metadata():
                time.sleep(1)
            self.info = self.handle.get_torrent_info()
            self.handle.auto_managed(False)
            self.handle.stop_when_ready(True)
            self.handle.resume()
        except RuntimeError:
            pass

    def stop(self):
        self.session.remove_torrent(self.handle)

    def resume(self):
        self.handle.resume()

    def pause(self):
        self.handle.pause()

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

    def __init__(self, session, name, handle, info, magnet_link, filepath, priorities=None, limits=None,
                 sequential=False):
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

        if limits is not None:
            if limits[0] is not None:
                self.set_upload_limit(limits[0])
            if limits[1] is not None:
                self.set_download_limit(limits[1])

        self.sequential = sequential
        if sequential:
            self.handle.set_sequential_download(True)