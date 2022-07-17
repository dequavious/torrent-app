import sys
import time
from _tkinter import TclError
from threading import Thread
from tkinter import *
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showerror, showinfo, askokcancel
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Progressbar, Treeview, Style, Notebook

from database.db import DB
from scraper.scraper import Scraper, get_magnet_link
from torrent.session import Session

PAUSE = 0
RESUME = 1
PRIORITIES = range(8)


class ScrollableFrame(Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = Canvas(self)
        scrollbar = Scrollbar(self, orient=VERTICAL, command=canvas.yview)
        self.scrollable_frame = Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox(ALL)
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor=NW)

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)


class GUI:
    class Download:
        class Settings:
            class File:

                def track_progress(self):
                    while not (self.root.stopped and self.root.torrent.seeding_or_stopped()):
                        try:
                            percentage = int(round((self.root.torrent.get_file_progress(self.index) /
                                                    self.file.size) * 100))
                            if not self.root.stopped:
                                self.progressbar['value'] = percentage
                                if not self.root.stopped:
                                    self.frame.update_idletasks()
                        except TclError:
                            pass
                        time.sleep(1)

                def set_priority(self, *args):
                    self.root.torrent.set_file_priority(self.index, int(self.variable.get()))

                def __init__(self, root, frame, file, index):
                    self.root = root
                    self.frame = frame
                    self.file = file
                    self.index = index
                    file_name = file.path.split('/')[-1]
                    label_frame = LabelFrame(self.frame.scrollable_frame, text=f"{file_name}")
                    label_frame.pack(fill=BOTH, padx=10)
                    self.progressbar = Progressbar(label_frame,
                                                   style=f'{file_name}_pb.text.Horizontal.TProgressbar',
                                                   mode='determinate', length=550)
                    self.progressbar.pack(side=LEFT, padx=5)

                    self.variable = StringVar(label_frame)
                    self.variable.set(f'{PRIORITIES[root.torrent.get_file_priority(index)]}')

                    opt = OptionMenu(label_frame, self.variable, *PRIORITIES)
                    opt.config(font=('Helvetica', 12))
                    opt.pack(padx=5, side=RIGHT)

                    self.variable.trace("w", self.set_priority)

                    Thread(target=self.track_progress, daemon=True).start()

            def add_trackers(self):
                trackers = self.text.get('1.0', 'end-1c')
                if trackers != '':
                    self.parent.torrent.add_trackers(trackers.split("\n"))
                    for tracker in trackers.split("\n"):
                        self.tree.insert(parent='', index='end', values=(f"{tracker}",))
                    self.text.delete('1.0', 'end-1c')
                    showinfo('Info', 'Trackers have been added successfully.', parent=self.window)

            def refresh_peer_list(self):
                self.tree2.delete(*self.tree2.get_children())
                peers = self.parent.torrent.get_peer_info()
                for i, peer in enumerate(peers):
                    self.tree2.insert(parent='', index='end', values=(f"{peer.ip[0]}",))

            def set_sequential(self):
                self.sequential_var.set(1 - self.sequential_var.get())
                if self.sequential_var.get() == 1:
                    self.sequential_lbl['text'] = 'Enabled'
                    self.parent.torrent.set_sequential_download(True)
                    showinfo('Info', 'Sequential downloading has been enabled for this torrent.', parent=self.window)
                else:
                    self.sequential_lbl['text'] = 'Disabled'
                    self.parent.torrent.set_sequential_download(False)
                    showinfo('Info', 'Sequential downloading has been disabled for this torrent.', parent=self.window)

            def enable_disable_upload(self):
                self.upload_var.set(1 - self.upload_var.get())
                if self.upload_var.get() == 1:
                    self.upload_entry['state'] = 'disabled'
                else:
                    self.upload_entry['state'] = 'normal'

            def enable_disable_download(self):
                self.download_var.set(1 - self.download_var.get())
                if self.download_var.get() == 1:
                    self.download_entry['state'] = 'disabled'
                else:
                    self.download_entry['state'] = 'normal'

            def set_upload_limit(self):
                if self.upload_var.get() == 1:
                    self.parent.torrent.set_upload_limit(-1)
                    showinfo('Info', 'The upload limit for this torrent has been set successfully.',
                             parent=self.window)
                    self.window.destroy()
                elif self.upload_entry.get().isdigit():
                    self.parent.torrent.set_upload_limit(int(self.upload_entry.get()) * 1000)
                    showinfo('Info', 'The upload limit for this torrent has been set successfully.',
                             parent=self.window)
                    self.window.destroy()

            def set_download_limit(self):
                if self.download_var.get() == 1:
                    self.parent.torrent.set_download_limit(-1)
                    showinfo('Info', 'The download limit for this torrent has been set successfully.',
                             parent=self.window)
                    self.window.destroy()
                elif self.download_entry.get().isdigit():
                    self.parent.torrent.set_download_limit(int(self.download_entry.get()) * 1000)
                    showinfo('Info', 'The download limit for this torrent has been set successfully.',
                             parent=self.window)
                    self.window.destroy()

            def check_stopped(self):
                while True:
                    if self.parent.stopped:
                        self.window.destroy()
                        break
                    time.sleep(1)

            def __init__(self, parent):
                self.parent = parent

                self.window = Tk()
                self.window.resizable(False, False)
                self.window.title(parent.name)
                tab_control = Notebook(self.window)

                files_tab = Frame(tab_control)
                trackers_tab = Frame(tab_control)
                peers_tab = Frame(tab_control)
                general_tab = Frame(tab_control)

                tab_control.add(files_tab, text='Files')
                tab_control.add(trackers_tab, text='Trackers')
                tab_control.add(peers_tab, text='Peers')
                tab_control.add(general_tab, text='General')
                tab_control.pack(expand=True, fill=BOTH)

                files = parent.torrent.get_files()
                frame2 = ScrollableFrame(files_tab)
                frame3 = Frame(frame2.scrollable_frame)
                frame3.pack(fill=BOTH, pady=5)
                filename_lbl = Label(frame3, text='FILENAME', font=('Times BOLD', 12))
                filename_lbl.pack(side=LEFT)
                priority_lbl = Label(frame3, text='PRIORITY', font=('Times BOLD', 12))
                priority_lbl.pack(side=RIGHT)
                for i, file in enumerate(files):
                    self.File(parent, frame2, file, i)
                frame2.pack(expand=True, fill=BOTH, padx=5, pady=5)

                frame = Frame(trackers_tab)
                frame.pack(padx=5, pady=5, fill=X)
                self.tree = Treeview(frame, selectmode='browse')

                self.tree['columns'] = ('URL',)
                self.tree.column('#0', width=0, minwidth=0)
                self.tree.column('URL', anchor=W, width=650)

                self.tree.heading('URL', text='URL', anchor=CENTER)
                self.tree.pack(side=LEFT, fill=BOTH, expand=True, pady=5)

                scrollbar = Scrollbar(frame, orient="vertical")
                scrollbar.pack(side=RIGHT, fill=Y)
                self.tree.configure(yscrollcommand=scrollbar.set)
                scrollbar.configure(command=self.tree.yview)

                trackers = parent.torrent.get_trackers()
                for i, tracker in enumerate(trackers):
                    self.tree.insert(parent='', index='end', values=(f"{tracker}",))

                frame4 = LabelFrame(trackers_tab, text='Add trackers')
                frame4.pack(fill=BOTH, padx=5, pady=5)
                self.text = ScrolledText(frame4)
                self.text.pack()

                frame5 = Frame(trackers_tab)
                frame5.pack(fill=BOTH, padx=5, pady=5)
                add_btn = Button(
                    frame5,
                    text='Add',
                    bg='#081947',
                    fg='#fff',
                    command=lambda: self.add_trackers(),
                    font=('Times BOLD', 12)
                )
                add_btn.pack(side=RIGHT)

                frame6 = Frame(peers_tab)
                frame6.pack(padx=5, pady=5, expand=True, fill=BOTH)
                self.tree2 = Treeview(frame6, selectmode='browse')

                self.tree2['columns'] = ('IP',)
                self.tree2.column('#0', width=0, minwidth=0)
                self.tree2.column('IP', anchor=W, width=650)

                self.tree2.heading('IP', text='IP', anchor=CENTER)
                self.tree2.pack(side=LEFT, fill=BOTH, expand=True)

                scrollbar2 = Scrollbar(frame6, orient="vertical")
                scrollbar2.pack(side=RIGHT, fill=Y)
                self.tree2.configure(yscrollcommand=scrollbar2.set)
                scrollbar2.configure(command=self.tree2.yview)

                self.refresh_peer_list()

                frame7 = Frame(peers_tab)
                frame7.pack(fill=BOTH, padx=5, pady=5)
                add_btn = Button(
                    frame7,
                    text='Refresh',
                    bg='#081947',
                    fg='#fff',
                    command=lambda: self.refresh_peer_list(),
                    font=('Times BOLD', 12)
                )
                add_btn.pack(side=RIGHT)

                label_frame = LabelFrame(general_tab, text='Sequential download')
                label_frame.pack(padx=10, pady=10, fill=BOTH)
                if self.parent.torrent.sequential:
                    self.sequential_var = IntVar(value=1)
                    self.sequential_check = Checkbutton(label_frame, command=self.set_sequential)
                    self.sequential_check.pack(side=LEFT, pady=10, padx=10)
                    self.sequential_check.select()
                    self.sequential_lbl = Label(label_frame, text='Enabled')
                    self.sequential_lbl.pack(side=LEFT, padx=10, pady=10)
                else:
                    self.sequential_var = IntVar(value=0)
                    self.sequential_check = Checkbutton(label_frame, command=self.set_sequential)
                    self.sequential_check.pack(side=LEFT, pady=10, padx=10)
                    self.sequential_lbl = Label(label_frame, text='Disabled')
                    self.sequential_lbl.pack(side=LEFT, padx=10, pady=10)

                if self.parent.torrent.get_upload_limit() == -1 or self.parent.torrent.get_upload_limit() == 0:
                    upload_frame = LabelFrame(general_tab, text='Upload rate limit: None')
                else:
                    upload_limit = int(round(self.parent.torrent.get_upload_limit() / 1000))
                    upload_frame = LabelFrame(general_tab, text=f'Upload rate limit: {upload_limit} kb/s')
                upload_frame.pack(padx=10, pady=10, fill=BOTH)
                self.upload_var = IntVar(value=1)
                upload_check_btn = Checkbutton(upload_frame, variable=self.upload_var, text='None',
                                               command=self.enable_disable_upload)
                upload_check_btn.pack(side=LEFT, padx=10, pady=10)
                upload_check_btn.select()
                self.upload_entry = Entry(upload_frame, state='disabled')
                self.upload_entry.pack(side=LEFT, padx=10, pady=10)
                upload_lbl = Label(upload_frame, text='kb/s')
                upload_lbl.pack(side=LEFT, pady=10)
                Button(upload_frame,
                       text='Update',
                       command=self.set_upload_limit,
                       bg='#081947',
                       fg='#fff',
                       ).pack(side=LEFT, padx=10, pady=10)

                if self.parent.torrent.get_download_limit() == -1 or self.parent.torrent.get_download_limit() == 0:
                    download_frame = LabelFrame(general_tab, text='Download rate limit: None')
                else:
                    download_limit = int(round(self.parent.torrent.get_download_limit() / 1000))
                    download_frame = LabelFrame(general_tab, text=f'Download rate limit: {download_limit} kb/s')
                download_frame.pack(padx=10, pady=10, fill=BOTH)
                self.download_var = IntVar(value=1)
                download_check_btn = Checkbutton(download_frame, variable=self.download_var, text='None',
                                                 command=self.enable_disable_download)
                download_check_btn.pack(side=LEFT, padx=10, pady=10)
                download_check_btn.select()
                self.download_entry = Entry(download_frame, state='disabled')
                self.download_entry.pack(side=LEFT, padx=10, pady=10)
                download_lbl = Label(download_frame, text='kb/s')
                download_lbl.pack(side=LEFT, pady=10)
                Button(download_frame,
                       text='Update',
                       command=self.set_download_limit,
                       bg='#081947',
                       fg='#fff',
                       ).pack(side=LEFT, padx=10, pady=10)

                Thread(target=self.check_stopped, daemon=True).start()

                self.window.mainloop()

        def update_progress_bar(self, status):
            try:
                percentage = status.progress * 100
                if not self.stopped:
                    self.progressbar['value'] = percentage
                    if self.paused:
                        if not self.stopped:
                            self.style.configure(f'{self.pid}.text.Horizontal.TProgressbar',
                                                 text=f'{int(round(percentage))} % complete (download: '
                                                      f'{int(round(status.download_rate / 1000))} kb/s upload: '
                                                      f'{int(round(status.upload_rate / 1000))} kb/s peers: '
                                                      f'{status.num_peers}) '
                                                      'paused ')
                    else:
                        if not self.stopped:
                            self.style.configure(f'{self.pid}.text.Horizontal.TProgressbar',
                                                 text=f'{int(round(percentage))} % complete (download: '
                                                      f'{int(round(status.download_rate / 1000))} kb/s upload: '
                                                      f'{int(round(status.upload_rate / 1000))} kb/s peers: '
                                                      f'{status.num_peers}) '
                                                      f'{self.torrent.state[status.state]} ')
                    if not self.stopped:
                        self.frame.update_idletasks()
            except TclError:
                pass

        def track_progress(self):
            Thread(target=self.check_metadata, daemon=True).start()
            while not (self.stopped and self.torrent.seeding_or_stopped()):
                status = self.torrent.handle.status()
                if not self.stopped:
                    self.update_progress_bar(status)
                time.sleep(1)

            if not self.stopped:
                self.update_progress_bar(self.torrent.handle.status())

        def delete(self):
            self.stopped = True
            self.parent.remove_from_downloads(self.name)
            self.torrent.stop()
            self.frame.destroy()

        def pause_resume(self, action):
            if action == 1:
                self.paused = False
                self.pause_play_btn.__setitem__('command', lambda: self.pause_resume(PAUSE))
                self.pause_play_btn.__setitem__('image', self.PAUSE_IMG)
                Thread(target=self.torrent.resume, daemon=True).start()
            else:
                self.paused = True
                self.pause_play_btn.__setitem__('command', lambda: self.pause_resume(RESUME))
                self.pause_play_btn.__setitem__('image', self.PLAY_IMG)
                Thread(target=self.torrent.pause, daemon=True).start()

        def check_metadata(self):
            self.torrent.get_metadata()
            if not self.stopped:
                self.settings_btn['state'] = 'normal'

        def __init__(self, parent, torrent, frame, number, style):
            self.paused = False
            self.name = torrent.name
            self.parent = parent
            self.style = style
            self.torrent = torrent

            self.stopped = False

            self.frame = LabelFrame(frame, text=f'{self.name}')
            self.frame.pack(fill=BOTH, padx=10)

            self.pid = f'pb{number}'

            self.progressbar = Progressbar(self.frame,
                                           style=f'{self.pid}.text.Horizontal.TProgressbar',
                                           mode='determinate', length=880)
            self.progressbar.pack(side=LEFT)

            self.PAUSE_IMG = PhotoImage(file='gui/images/pause.jpg').subsample(30, 35)
            self.PLAY_IMG = PhotoImage(file='gui/images/play.jpg').subsample(15, 18)
            self.DELETE_IMG = PhotoImage(file='gui/images/delete.jpg').subsample(17, 20)
            self.SETTINGS_IMG = PhotoImage(file='gui/images/settings.jpg').subsample(55, 67)

            self.delete_btn = Button(self.frame, image=self.DELETE_IMG, compound=CENTER, command=lambda: self.delete())
            self.delete_btn.pack(side=RIGHT, anchor='n')
            self.settings_btn = Button(self.frame, image=self.SETTINGS_IMG, compound=CENTER,
                                       command=lambda: self.Settings(self),
                                       state='disabled')
            self.settings_btn.pack(side=RIGHT, anchor='n')
            self.pause_play_btn = Button(self.frame, image=self.PAUSE_IMG, compound=CENTER,
                                         command=lambda: self.pause_resume(PAUSE))
            self.pause_play_btn.pack(side=RIGHT, anchor='n')

            Thread(target=self.track_progress, daemon=True).start()

    class Magnet:
        def download(self):
            if self.text.get('1.0', 'end-1c'):
                torrent = self.parent.session.add_magnet(self.text.get('1.0', 'end-1c'))
                if torrent is not None:
                    if not self.parent.torrents.get(f"{torrent.handle.name()}"):
                        Thread(target=self.parent.start_download, daemon=True, args=(torrent,)).start()
                    else:
                        showerror('Error', 'Duplicate torrent.')
                    self.window.destroy()
                else:
                    showerror('Error', 'Invalid magnet link.')
                    self.window.destroy()

        def __init__(self, parent):
            self.parent = parent
            self.window = Tk()
            frame = LabelFrame(self.window, text='Magnet link')
            frame.pack(fill=BOTH, padx=5, pady=5)
            self.text = ScrolledText(frame)
            self.text.pack()
            self.button = Button(self.window,
                                 text='Download',
                                 command=lambda: self.download(),
                                 bg='#081947',
                                 fg='#fff',
                                 )
            self.button.pack(padx=10, pady=10, side=RIGHT)

            self.window.title("Magnet Link")
            self.window.resizable(False, False)

    class Settings:
        def change_directory(self):
            directory = askdirectory(parent=self.window, title='Select directory')
            if directory:
                self.folder_lbl.__setitem__('text', directory)
                self.parent.change_save_directory(directory)
                showinfo('Info', 'The download directory has been changed successfully',
                         parent=self.window)
                self.window.destroy()

        def enable_disable_upload(self):
            self.upload_var.set(1 - self.upload_var.get())
            if self.upload_var.get() == 1:
                self.upload_entry['state'] = 'disabled'
            else:
                self.upload_entry['state'] = 'normal'

        def enable_disable_download(self):
            self.download_var.set(1 - self.download_var.get())
            if self.download_var.get() == 1:
                self.download_entry['state'] = 'disabled'
            else:
                self.download_entry['state'] = 'normal'

        def set_upload_limit(self):
            if self.upload_var.get() == 1:
                self.parent.set_upload_limit(0)
                showinfo('Info', 'The global upload rate limit has been set successfully.',
                         parent=self.window)
                self.window.destroy()
            elif self.upload_entry.get().isdigit():
                self.parent.set_upload_limit(int(self.upload_entry.get()) * 1000)
                showinfo('Info', 'The global upload rate limit has been set successfully.',
                         parent=self.window)
                self.window.destroy()

        def set_download_limit(self):
            if self.download_var.get() == 1:
                self.parent.set_download_limit(0)
                showinfo('Info', 'The global download rate limit has been set successfully.',
                         parent=self.window)
                self.window.destroy()
            elif self.download_entry.get().isdigit():
                self.parent.set_download_limit(int(self.download_entry.get()) * 1000)
                showinfo('Info', 'The global download rate limit has been set successfully.',
                         parent=self.window)
                self.window.destroy()

        def __init__(self, parent):
            self.parent = parent
            self.window = Tk()
            folder_frame = LabelFrame(self.window, text='Downloads folder')
            folder_frame.pack(padx=10, pady=10, fill=BOTH)
            self.folder_lbl = Label(folder_frame, text=parent.save_path)
            self.folder_lbl.pack(side=LEFT, padx=10, pady=10)
            Button(folder_frame,
                   text='Update',
                   command=self.change_directory,
                   bg='#081947',
                   fg='#fff',
                   ).pack(side=RIGHT, padx=10, pady=10)

            if self.parent.get_upload_limit() == 0:
                upload_frame = LabelFrame(self.window, text='Upload rate limit: None')
            else:
                upload_limit = int(round(self.parent.get_upload_limit() / 1000))
                upload_frame = LabelFrame(self.window, text=f'Upload rate limit: {upload_limit} kb/s')
            upload_frame.pack(padx=10, pady=10, fill=BOTH)
            self.upload_var = IntVar(value=1)
            upload_check_btn = Checkbutton(upload_frame, variable=self.upload_var, text='None',
                                           command=self.enable_disable_upload)
            upload_check_btn.pack(side=LEFT, padx=10, pady=10)
            upload_check_btn.select()
            self.upload_entry = Entry(upload_frame, state='disabled')
            self.upload_entry.pack(side=LEFT, padx=10, pady=10)
            upload_lbl = Label(upload_frame, text='kb/s')
            upload_lbl.pack(side=LEFT, pady=10)
            Button(upload_frame,
                   text='Update',
                   command=self.set_upload_limit,
                   bg='#081947',
                   fg='#fff',
                   ).pack(side=RIGHT, padx=10, pady=10)

            if self.parent.get_download_limit() == 0:
                download_frame = LabelFrame(self.window, text='Download rate limit: None')
            else:
                download_limit = int(round(self.parent.get_download_limit() / 1000))
                download_frame = LabelFrame(self.window, text=f'Download rate limit: {download_limit} kb/s')
            download_frame.pack(padx=10, pady=10, fill=BOTH)
            self.download_var = IntVar(value=1)
            download_check_btn = Checkbutton(download_frame, variable=self.download_var, text='None',
                                             command=self.enable_disable_download)
            download_check_btn.pack(side=LEFT, padx=10, pady=10)
            download_check_btn.select()
            self.download_entry = Entry(download_frame, state='disabled')
            self.download_entry.pack(side=LEFT, padx=10, pady=10)
            download_lbl = Label(download_frame, text='kb/s')
            download_lbl.pack(side=LEFT, pady=10)
            Button(download_frame,
                   text='Update',
                   command=self.set_download_limit,
                   bg='#081947',
                   fg='#fff',
                   ).pack(side=RIGHT, padx=10, pady=10)

            self.window.title("Settings")
            self.window.resizable(False, False)

    def on_exit(self):
        if askokcancel("Quit", "Do you want to quit?"):
            for name, torrent in self.torrents.items():
                self.session.stop()
                self.db.save(name, torrent.magnet_link, torrent.filepath, torrent.get_file_priorities(),
                             torrent.sequential, torrent.get_upload_limit(), torrent.get_download_limit())
            self.root.destroy()
            sys.exit()

    def set_upload_limit(self, limit):
        self.session.set_upload_limit(limit)
        if limit == 0:
            self.db.set_global_upload_limit('NULL')
        else:
            self.db.set_global_upload_limit(limit)

    def set_download_limit(self, limit):
        self.session.set_download_limit(limit)
        if limit == 0:
            self.db.set_global_download_limit('NULL')
        else:
            self.db.set_global_download_limit(limit)

    def get_upload_limit(self):
        return self.session.get_upload_limit()

    def get_download_limit(self):
        return self.session.get_download_limit()

    def scrape(self, search, page):
        if search != '':
            self.previous_btn['state'] = 'disabled'
            self.next_btn['state'] = 'disabled'
            self.search_btn['state'] = 'disabled'

            self.page = page
            self.search = search
            self.scraper = Scraper(search)
            self.scraper.scrape(page)
            self.results = self.scraper.torrents

            self.tree.delete(*self.tree.get_children())
            for i, torrent in enumerate(self.results):
                self.tree.insert(parent='', index='end', iid=f'{i}',
                                 values=(torrent['name'], torrent['seeds'], torrent['leech'], torrent['size']))

            if self.page < self.scraper.pages:
                self.next_btn['state'] = 'normal'
            else:
                self.next_btn['state'] = 'disabled'

            if self.page > 1:
                self.previous_btn['state'] = 'normal'
            else:
                self.previous_btn['state'] = 'disabled'

            self.search_btn['state'] = 'normal'

    def previous(self):
        page = self.page - 1
        if 1 <= page <= self.scraper.pages:
            self.scrape(self.search, page)

    def next(self):
        page = self.page + 1
        if 1 <= page <= self.scraper.pages:
            self.scrape(self.search, page)

    def download(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            if not self.torrents.get(f"{self.results[int(item)]['name']}"):
                magnet_link = get_magnet_link(self.results[int(item)]['link'])
                if magnet_link != '':
                    torrent = self.session.add_magnet(magnet_link, torrent_name=self.results[int(item)]['name'])
                    if torrent is not None:
                        Thread(target=self.start_download, daemon=True, args=(torrent,)).start()
                    else:
                        showerror('Error', 'Invalid magnet link.')
                else:
                    showinfo("Info", "The page for the torrent you are trying to download is missing.")

    def remove_from_downloads(self, name):
        self.torrents.pop(name)

    def start_download(self, torrent, i=None):
        if i is not None:
            Thread(target=self.Download, daemon=True, args=(self, torrent, self.download_frame.scrollable_frame, i,
                                                            self.style)).start()
        else:
            Thread(target=self.Download, daemon=True,
                   args=(self, torrent, self.download_frame.scrollable_frame, self.download_count, self.style)).start()
        self.torrents[f"{torrent.name}"] = torrent

        self.download_count += 1

    def resume_previous_downloads(self):
        rows = self.db.get_torrents()
        for i, row in enumerate(rows):
            priorities = self.db.get_priorities(i + 1)
            if row[1] is not None:
                torrent = self.session.add_magnet(row[1], torrent_name=row[0], upload=row[3], download=row[4],
                                                  sequential=row[5], priorities=priorities)
                if torrent is not None:
                    Thread(target=self.start_download, daemon=True, args=(torrent, i)).start()
                else:
                    showerror('Error', 'Invalid magnet link.')
            else:
                torrent = self.session.add_torrent_file(row[2], row[2].split('/')[-1], upload=row[3], download=row[4],
                                                        sequential=row[5], priorities=priorities)
                if torrent is not None:
                    Thread(target=self.start_download, daemon=True, args=(torrent, i)).start()
                else:
                    showerror('Error', 'Invalid torrent file.')
        self.db.reset()

    def change_save_directory(self, directory):
        self.save_path = directory
        self.db.update_save_path(directory)
        self.session.change_save_directory(directory)

    def open_torrent(self):
        window = Tk()
        window.withdraw()
        filepath = askopenfilename(parent=window, filetypes=[('Torrent Files', '*.torrent')])
        if filepath:
            torrent = self.session.add_torrent_file(filepath, filepath.split('/')[-1])
            if torrent is not None:
                if not self.torrents.get(f"{torrent.name}"):
                    Thread(target=self.start_download, daemon=True, args=(torrent,)).start()
                else:
                    showerror('Error', 'Duplicate torrent.')
            else:
                showerror('Error', 'Invalid torrent file.')
        window.destroy()

    def track_node_count(self):
        while True:
            self.dht_lbl['text'] = f'DHT node count: {self.session.dht_node_count()}'
            time.sleep(1)

    def __init__(self):
        self.db = DB()
        self.save_path = self.db.get_save_path()
        self.scraper = None
        self.search = ""
        self.page = 1
        self.torrents = {}
        self.results = None
        self.session = Session(self.save_path, self.db.get_global_limits())
        self.session.start()

        self.download_count = 0

        self.root = Tk()

        frame1 = Frame(self.root)
        frame1.pack(pady=20)

        self.search_text = StringVar()
        search_entry = Entry(frame1, textvariable=self.search_text, width=112)
        search_entry.pack(side=LEFT)

        self.search_btn = Button(
            frame1,
            text='Search',
            command=lambda: Thread(target=self.scrape, args=(self.search_text.get(), 1), daemon=True).start(),
            bg='#081947',
            fg='#fff',
            font=('Times BOLD', 12)
        )
        self.search_btn.pack(side=RIGHT)

        frame2 = Frame(self.root)
        frame2.pack()

        self.tree = Treeview(frame2, selectmode='browse')

        self.tree['columns'] = ('Name', 'Se', 'Le', 'Size')
        self.tree.column('#0', width=0, minwidth=0)
        self.tree.column('Name', anchor=W, width=750)
        self.tree.column('Se', anchor=CENTER, width=75)
        self.tree.column('Le', anchor=CENTER, width=75)
        self.tree.column('Size', anchor=W, width=75)

        self.tree.heading('Name', text='Name', anchor=W)
        self.tree.heading('Se', text='Se', anchor=CENTER)
        self.tree.heading('Le', text='Le', anchor=CENTER)
        self.tree.heading('Size', text='Size', anchor=CENTER)
        self.tree.pack(side=LEFT, fill=Y, expand=True)

        self.tree.bind('<Double-Button-1>', self.download)

        scrollbar = Scrollbar(frame2, orient="vertical")
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.tree.yview)

        frame3 = Frame(self.root)
        frame3.pack(fill=X)
        self.previous_btn = Button(
            frame3,
            text='< Previous',
            command=lambda: Thread(target=self.previous, daemon=True).start(),
            bg='#081947',
            fg='#fff',
            state='disabled'
        )
        self.previous_btn.pack(side=LEFT)
        self.previous_btn.place(x=5)
        self.next_btn = Button(
            frame3,
            text='Next >',
            command=lambda: Thread(target=self.next, daemon=True).start(),
            bg='#081947',
            fg='#fff',
            state='disabled'
        )
        self.next_btn.pack(side=RIGHT, padx=5)

        label_frame = LabelFrame(self.root, text='Downloads')
        label_frame.pack(fill=BOTH, padx=5, pady=5)
        self.download_frame = ScrollableFrame(label_frame)
        self.download_frame.pack(fill=BOTH)

        self.dht_frame = Frame(self.root)
        self.dht_frame.pack(padx=5, fill=X)
        self.dht_lbl = Label(self.dht_frame, text="DHT Nodes: ")
        self.dht_lbl.pack(pady=10)

        Thread(target=self.track_node_count, daemon=True).start()

        self.menu = Menu(self.root)
        self.root.config(menu=self.menu)
        self.add_menu = Menu(self.menu)
        self.menu.add_cascade(label='Add', menu=self.add_menu)
        self.add_menu.add_command(label='Magnet', command=lambda: self.Magnet(self))
        self.add_menu.add_command(label='Torrent', command=lambda: self.open_torrent())
        self.menu.add_command(label='Settings', command=lambda: self.Settings(self))

        self.style = Style()
        self.style.theme_use("default")
        self.style.map("Treeview")
        self.style.layout('text.Horizontal.TProgressbar',
                          [('Horizontal.Progressbar.trough',
                            {'children': [('Horizontal.Progressbar.pbar', {'side': 'left', 'sticky': 'ns'})],
                             'sticky': 'nswe'}),
                           ('Horizontal.Progressbar.label', {'sticky': 'nswe'})])
        self.style.configure('text.Horizontal.TProgressbar', text='0 %', anchor=CENTER, background="green",
                             foreground="white", font=('Times BOLD', 12))

        Thread(target=self.resume_previous_downloads, daemon=True).start()

        self.root.attributes('-alpha', 0.95)
        self.root.title("Torrent App")
        self.root.geometry("1000x660")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.root.mainloop()
