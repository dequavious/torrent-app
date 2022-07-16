import time
import libtorrent as lt


class Torrent:
    def get_metadata(self):
        while not self.handle.has_metadata():
            time.sleep(1)
        self.info = self.handle.get_torrent_info()

    def resume(self):
        self.handle.resume()

    def pause(self):
        self.handle.pause()

    def stop(self):
        self.handle.stop_when_ready(True)

    def seeding(self):
        return self.handle.status().state == lt.torrent_status.seeding

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
        while not self.handle.has_metadata:
            time.sleep(1)
        self.handle.set_upload_limit(limit)

    def set_download_limit(self, limit):
        while not self.handle.has_metadata:
            time.sleep(1)
        self.handle.set_download_limit(limit)

    def set_sequential_download(self, value):
        self.sequential = value
        self.handle.set_sequential_download(value)

    def add_trackers(self, trackers):
        if self.magnet_link is not None:
            for tracker in trackers:
                self.info.add_trackers(tracker)
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

    def __init__(self, name, handle, info, magnet_link, filepath, priorities=None, sequential=False):
        self.state = ['queued', 'checking', 'fetching meta-info', 'downloading', 'finished', 'seeding', 'allocating',
                      'checking resume data']
        self.name = name
        self.handle = handle
        self.info = info
        self.magnet_link = magnet_link
        self.filepath = filepath

        if priorities is not None:
            self.set_priorities(priorities)

        self.sequential = sequential
        if sequential:
            self.handle.set_sequential_download(True)

