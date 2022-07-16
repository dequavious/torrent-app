import sys
import time
from _tkinter import TclError
from threading import Thread
from tkinter import *
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showerror, showinfo, askokcancel
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Progressbar, Treeview, Style, Notebook

from db import DB
from scraper import Scraper, get_magnet_link
from session import Session

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
                    while not (self.root.torrent.seeding() and self.root.stopped):
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
                                                      f'{round(status.download_rate / 1000, 1)} kb/s upload: '
                                                      f'{round(status.upload_rate / 1000, 1)} kb/s peers: '
                                                      f'{status.num_peers}) '
                                                      'paused ')
                    else:
                        if not self.stopped:
                            self.style.configure(f'{self.pid}.text.Horizontal.TProgressbar',
                                                 text=f'{int(round(percentage))} % complete (download: '
                                                      f'{round(status.download_rate / 1000, 1)} kb/s upload: '
                                                      f'{round(status.upload_rate / 1000, 1)} kb/s peers: '
                                                      f'{status.num_peers}) '
                                                      f'{self.torrent.state[status.state]} ')
                    if not self.stopped:
                        self.frame.update_idletasks()
            except TclError:
                pass

        def track_progress(self):
            Thread(target=self.check_metadata, daemon=True).start()
            while not (self.torrent.seeding() and self.stopped):
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

            self.PAUSE_IMG = PhotoImage(file='images/pause.jpg').subsample(30, 35)
            self.PLAY_IMG = PhotoImage(file='images/play.jpg').subsample(15, 18)
            self.DELETE_IMG = PhotoImage(file='images/delete.jpg').subsample(17, 20)
            self.SETTINGS_IMG = PhotoImage(file='images/settings.jpg').subsample(55, 67)

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
                        Thread(target=self.parent.start_download, daemon=True, args=(torrent, )).start()
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
                self.label.__setitem__('text', directory)
                self.parent.change_save_directory(directory)
                showinfo('Info', 'The download directory has been changed successfully')
                self.window.destroy()

        def __init__(self, parent):
            self.parent = parent
            self.save_path = self.parent.save_path
            self.window = Tk()
            self.label_frame = LabelFrame(self.window, text='Downloads folder')
            self.label_frame.pack(padx=10, pady=10, fill=BOTH)
            self.label = Label(self.label_frame, text=self.save_path)
            self.label.pack(side=LEFT, padx=10, pady=10)
            self.button = Button(self.label_frame,
                                 text='Update',
                                 command=self.change_directory,
                                 bg='#081947',
                                 fg='#fff',
                                 )
            self.button.pack(side=RIGHT, padx=10, pady=10)

            self.window.title("Settings")
            self.window.resizable(False, False)

    def on_exit(self):
        if askokcancel("Quit", "Do you want to quit?"):
            for name, torrent in self.torrents.items():
                self.session.stop()
                self.db.save(name, torrent.magnet_link, torrent.filepath, torrent.get_file_priorities(),
                             torrent.sequential)
            self.root.destroy()
            sys.exit()

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
                    torrent = self.session.add_magnet(magnet_link, self.results[int(item)]['name'])
                    if torrent is not None:
                        Thread(target=self.start_download, daemon=True, args=(torrent, )).start()
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
            sequential = self.db.get_sequential(i + 1)
            priorities = self.db.get_priorities(i + 1)
            if row[1] is not None:
                if len(priorities) >= 1 and len(sequential) >= 1:
                    torrent = self.session.add_magnet(row[1], row[0], priorities, True)
                elif len(priorities) >= 1:
                    torrent = self.session.add_magnet(row[1], row[0], priorities=priorities)
                elif len(sequential) >= 1:
                    torrent = self.session.add_magnet(row[1], row[0], sequential=True)
                else:
                    torrent = self.session.add_magnet(row[1], row[0])
                if torrent is not None:
                    Thread(target=self.start_download, daemon=True, args=(torrent, i)).start()
                else:
                    showerror('Error', 'Invalid magnet link.')
            else:
                if len(priorities) >= 1 and len(sequential) >= 1:
                    torrent = self.session.add_torrent_file(row[2], row[2].split('/')[-1], priorities, True)
                elif len(priorities) >= 1:
                    torrent = self.session.add_torrent_file(row[2], row[2].split('/')[-1], priorities=priorities)
                elif len(sequential) >= 1:
                    torrent = self.session.add_torrent_file(row[2], row[2].split('/')[-1], sequential=True)
                else:
                    torrent = self.session.add_torrent_file(row[2], row[2].split('/')[-1])
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
                    Thread(target=self.start_download, daemon=True, args=(torrent, )).start()
                else:
                    showerror('Error', 'Duplicate torrent.')
            else:
                showerror('Error', 'Invalid torrent file.')
        window.destroy()

    def __init__(self):
        self.db = DB()
        self.save_path = self.db.get_save_path()
        self.scraper = None
        self.search = ""
        self.page = 1
        self.torrents = {}
        self.results = None
        self.session = Session(self.save_path)
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
        label_frame.pack(fill=BOTH, expand=True, padx=5, pady=10)
        self.download_frame = ScrollableFrame(label_frame)
        self.download_frame.pack(fill=BOTH)

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
        self.root.geometry("1000x575")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.root.mainloop()
