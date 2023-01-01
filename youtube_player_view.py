'''
Gui YouTube player: based on question
https://codereview.stackexchange.com/questions/282051/a-gui-youtube-audio-player/282130#282130
'''
import datetime
from tkinter import (
    Tk, Menu, Frame, Label, Button, Scale, Entry, DISABLED, StringVar,
    filedialog
)

class TkGuiView(Tk):
    ''' Tkinter GUI view for the youtube player
    '''
    geometry_window = '610x160'
    window_title = 'Youtube Player'
    file_extensions = [('all types (*.*)', '*.*'), ('json type (*.json)', '*.json')]
    query_width = 30
    pl_width = 50
    length_progress_bar = 210
    progress_bar_resolution = 0.001
    length_volume_bar = 80
    max_volume_bar = 100
    poll_time = 500

    def __init__(self):
        super().__init__()
        self.geometry(self.geometry_window)
        self.protocol('WM_DELETE_WINDOW', self.quit)
        self.title(self.window_title)

        self.main_frame = Frame(self)
        self.main_frame.grid(row=1, column=1, padx=5, sticky='new')
        self.query_song_title = StringVar()
        self.query_song_title.set('')
        self.pl_current_title = StringVar()
        self.pl_current_title.set('')
        self.pl_next_title = StringVar()
        self.pl_next_title.set('')
        self.quality_text = StringVar()
        self.quality_text.set('')
        self.shuffle_text = StringVar()
        self.shuffle_text.set('')
        self.short_text = StringVar()
        self.short_text.set('')
        self.auto_text = StringVar()
        self.auto_text.set('')
        self.pl_song_time_text = StringVar()
        self.pl_song_time_text.set(' / '.join([str(datetime.timedelta(0)),
            str(datetime.timedelta(0))]))

        self.controller = None
        self.set_menubar()
        self.set_query_frame()
        self.set_pl_frame()
        self.set_status_frame()
        self.poll_song_status()

    def set_menubar(self):
        menubar = Menu(self)
        self.set_file_menu()
        menubar.add_cascade(label='File', menu=self.file_menu)
        self.set_quality_menu()
        menubar.add_cascade(label='Quality', menu=self.quality_menu)
        self.set_options_menu()
        menubar.add_cascade(label='Options', menu=self.options_menu)
        self.set_playlist_menu()
        menubar.add_cascade(label='Playlist', menu=self.playlist_menu)
        self.config(menu=menubar)

    def set_file_menu(self):
        self.file_menu = Menu(self, tearoff=0)
        self.file_menu.add_command(label='open playlist', command=self.open_playlist)
        self.file_menu.add_command(label='save playlist', command=self.save_playlist)
        self.file_menu.add_command(label='quit', command=self.quit)

    def set_quality_menu(self):
        self.quality_menu = Menu(self, tearoff=0)
        self.quality_menu.add_command(
            label='best quality', command=lambda: self.set_quality('max'))
        self.quality_menu.add_command(
            label='quality up', command=lambda: self.set_quality(1))
        self.quality_menu.add_command(
            label='quality down', command=lambda: self.set_quality(-1))
        self.quality_menu.add_command(
            label='least quality', command=lambda: self.set_quality(0))

    def set_options_menu(self):
        self.options_menu = Menu(self, tearoff=0)
        self.options_menu.add_command(label='toggle shuffle', command=self.toggle_shuffle)
        self.options_menu.add_command(label='toggle short song', command=self.toggle_short_song)
        self.options_menu.add_command(label='toggle autoplay', command=self.toggle_autoplay)

    def set_playlist_menu(self):
        self.playlist_menu = Menu(self, tearoff=0)
        self.playlist_menu.add_command(
            label='all results to playlist', command=self.import_all_to_playlist)
        self.playlist_menu.add_command(
            label='clear playlist', command=self.clear_playlist)

    def set_query_frame(self):
        query_frame = Frame(self.main_frame)
        query_frame.grid(row=1, column=1, sticky='new')
        title_label = Label(query_frame, text='Search your song ...', width=self.query_width)
        title_label.grid(row=1, column=1, sticky='nw')
        self.query_text_entry = Entry(query_frame, width=self.query_width)
        self.query_text_entry.grid(row=2, column=1, sticky='nw')
        self.query_text_entry.bind('<Return>', self.query_songs)
        self.song_text_entry = Entry(
            query_frame, textvariable=self.query_song_title, state=DISABLED, width=self.query_width)
        self.song_text_entry.grid(row=3, column=1, stick='nw')
        Label(query_frame, text=' ').grid(row=4, column=1)
        button_frame = Frame(query_frame)
        button_frame.grid(row=5, column=1, sticky='nw')
        Button(button_frame, text='<-', command=self.query_prev).pack(side='left')
        Button(button_frame, text='->', command=self.query_next).pack(side='left')
        Button(button_frame, text='|>', command=self.query_play).pack(side='left')
        Button(button_frame, text='Add', command=self.query_add_song).pack(side='left')

    def set_pl_frame(self):
        pl_frame = Frame(self.main_frame)
        pl_frame.grid(row=1, column=2, sticky='new')
        title_label = Label(pl_frame, text='Playlist ...', width=self.query_width)
        title_label.grid(row=1, column=1, columnspan=2, sticky='nw')
        self.pl_current_entry = Entry(pl_frame, textvariable=self.pl_current_title, state=DISABLED, width=self.pl_width)
        self.pl_current_entry.grid(row=2, column=1, sticky='nw')
        self.pl_next_entry = Entry(pl_frame, textvariable=self.pl_next_title, state=DISABLED, width=self.pl_width)
        self.pl_next_entry.grid(row=3, column=1, sticky='nw')
        progress_frame = Frame(pl_frame)
        progress_frame.grid(row=4, column=1, sticky='nw')
        Label(progress_frame, textvariable=self.pl_song_time_text, anchor='w').pack(side='left')
        self.progress_bar = Scale(progress_frame, from_=0, to_=int(1 / self.progress_bar_resolution),
            length=self.length_progress_bar, orient='horizontal', showvalue=0)
        self.progress_bar.pack(side='left')
        self.progress_bar.bind('<ButtonRelease-1>', self.set_song_time)
        button_frame = Frame(pl_frame)
        button_frame.grid(row=5, column=1, sticky='nw')
        Button(button_frame, text='<<', command=self.pl_play_prev).pack(side='left')
        Button(button_frame, text='<', command=self.pl_song_back).pack(side='left')
        self.pl_play_pause_button = Button(button_frame, text='|>', command=self.pl_play_or_pause)
        self.pl_play_pause_button.pack(side='left')
        Button(button_frame, text='>', command=self.pl_song_forward).pack(side='left')
        Button(button_frame, text='>>', command=self.pl_play_next).pack(side='left')
        Label(button_frame, text=' ').pack(side='left')
        Button(button_frame, text='<-', command=self.pl_prev).pack(side='left')
        Button(button_frame, text='->', command=self.pl_next).pack(side='left')
        Button(button_frame, text='Remove', command=self.pl_remove_song).pack(side='left')
        self.volume_bar = Scale(pl_frame, from_=self.max_volume_bar, to_=0,
            length=self.length_volume_bar, orient='vertical', showvalue=1, command=self.set_volume)
        self.volume_bar.grid(row=2, column=2, rowspan=4, sticky='nw', padx=30)

    def set_status_frame(self):
        main_status_frame = Frame(self.main_frame)
        main_status_frame.grid(row=2, column=1, columnspan=2, sticky='nw')
        Label(main_status_frame, text=' ').grid(row=1, column=1)
        status_frame = Frame(main_status_frame)
        status_frame.grid(row=2, column=1, sticky='nw')
        Label(status_frame, text='Shuffle:', anchor='w', width=6).pack(side='left')
        Label(status_frame, textvariable=self.shuffle_text, anchor='w', width=3).pack(side='left')
        Label(status_frame, text='Short:', anchor='w', width=6).pack(side='left')
        Label(status_frame, textvariable=self.short_text, anchor='w', width=3).pack(side='left')
        Label(status_frame, text='Auto:', anchor='w', width=6).pack(side='left')
        Label(status_frame, textvariable=self.auto_text, anchor='w', width=3).pack(side='left')
        Label(status_frame, text='Q:', anchor='w', width=2).pack(side='left')
        Label(status_frame, textvariable=self.quality_text, anchor='w', width=10).pack(side='left')

    def set_controller(self, controller):
        self.controller = controller
        self.set_initial_values()

    def set_initial_values(self):
        if self.controller:
            quality_level, shuffle, short_song, autoplay, volume = self.controller.set_initial_values()
            self.quality_text.set(quality_level)
            self.shuffle_text.set('Y' if shuffle else 'N')
            self.short_text.set('Y' if short_song else 'N')
            self.auto_text.set('Y' if autoplay else 'N')
            self.volume_bar.set(volume)

    def open_playlist(self):
        if self.controller:
            self.controller.open_playlist(
                filedialog.askopenfilename(title='Open a file', filetypes=self.file_extensions))

    def save_playlist(self):
        if self.controller:
            self.controller.save_playlist(filedialog.asksaveasfilename(
                filetypes=self.file_extensions, defaultextension=self.file_extensions))

    def quit(self):
        if self.controller:
            self.controller.quit()

    def set_quality(self, val):
        if self.controller:
            quality_text = self.controller.set_quality(val)
            self.quality_text.set(quality_text)

    def toggle_shuffle(self):
        if self.controller:
            shuffle = self.controller.toggle_shuffle()
            self.shuffle_text.set('Y' if shuffle else 'N')

    def toggle_short_song(self):
        if self.controller:
            short_song = self.controller.toggle_short_song()
            self.short_text.set('Y' if short_song else 'N')

    def toggle_autoplay(self):
        if self.controller:
            autoplay = self.controller.toggle_autoplay()
            self.auto_text.set('Y' if autoplay else 'N')

    def import_all_to_playlist(self):
        if self.controller:
            self.controller.import_all_to_playlist()

    def clear_playlist(self):
        if self.controller:
            self.controller.clear_playlist()

    def query_songs(self, _):
        if self.controller:
            title = self.controller.query_songs(str(self.query_text_entry.get()))
            title = title if title else ''
            self.query_song_title.set(title)

    def query_prev(self):
        if self.controller:
            title = self.controller.query_prev()
            title = title if title else ''
            self.query_song_title.set(title)

    def query_next(self):
        if self.controller:
            title = self.controller.query_next()
            title = title if title else ''
            self.query_song_title.set(title)

    def query_play(self):
        if self.controller:
            self.controller.query_play()

    def query_add_song(self):
        if self.controller:
            self.controller.query_add_song()

    def pl_play_prev(self):
        if self.controller:
            self.controller.pl_play_prev()

    def pl_play_next(self):
        if self.controller:
            self.controller.pl_play_next()

    def pl_play_or_pause(self):
        if self.controller:
            pause = self.controller.pl_play_or_pause()
            if pause:
                self.pl_play_pause_button.config(text='|>')

            else:
                self.pl_play_pause_button.config(text='||')

    def pl_song_back(self):
        if self.controller:
            self.controller.pl_song_back()

    def pl_song_forward(self):
        if self.controller:
            self.controller.pl_song_forward()

    def pl_prev(self):
        if self.controller:
            self.controller.pl_prev()

    def pl_next(self):
        if self.controller:
            self.controller.pl_next()

    def pl_remove_song(self):
        if self.controller:
            self.controller.pl_remove_song()

    def pl_show_title(self, title):
        if title:
            self.pl_next_title.set(title)

        else:
            self.pl_next_title.set('')

    def pl_show_current_title(self, title, quality):
        if title:
            self.pl_current_title.set(title)
            self.quality_text.set(quality)

        else:
            self.pl_current_title.set('')

    def set_song_time(self, _):
        if self.controller:
            self.controller.set_song_time(
                self.progress_bar.get()
            )

    def set_volume(self, _):
        if self.controller:
            self.controller.set_volume(
                self.volume_bar.get()
            )

    def poll_song_status(self):
        if self.controller:
            time, length = self.controller.update_song_status()
            self.pl_song_time_text.set(' / '.join([
                str(datetime.timedelta(seconds=int(time))),
                str(datetime.timedelta(seconds=int(length)))]))

            self.progress_bar.set(time / length / self.progress_bar_resolution
                if length > 0 else 0.0)

        self.after(self.poll_time, self.poll_song_status)

    def exit(self):
        self.after(500, self.destroy)


if __name__ == '__main__':
    view = TkGuiView()
    view.mainloop()
