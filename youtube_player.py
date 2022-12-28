'''
Gui YouTube player: based on question
https://codereview.stackexchange.com/questions/282051/a-gui-youtube-audio-player/282130#282130
'''
import re
import random
import datetime
import json
from tkinter import (
    Tk, Menu, Frame, Label, Button, Scale, Entry, DISABLED, StringVar,
    filedialog
)
from youtube_search import YoutubeSearch
import vlc
import yt_dlp

MAX_SEARCH_RESULTS = 40
MAX_SONG_LENGTH = 300
YOUTUBE_BASE_URL = 'https://www.youtube.com'
NON_CHARS = r'[^a-zA-Z0-9 .,:;+-=!?/()öäßü]'


def song_is_short(duration: str) -> bool:
    try:
        hms = duration.split(':')
        if len(hms) == 3:
            seconds = int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])

        elif len(hms) == 2:
            seconds = int(hms[0]) * 60 + int(hms[1])

        else:
            return False

        if seconds < MAX_SONG_LENGTH:
            return True

        else:
            return False

    except ValueError:
        return False


class YouTubePlayer:
    ''' Class with methods to search songs on YouTube, get
        audio urls, play song with a vlc player and provide
        API
    '''
    def __init__(self, short_song: bool=False):
        self.short_song_ = short_song
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

    def search(self, search_query):
        results = YoutubeSearch(
            search_query, max_results=MAX_SEARCH_RESULTS
        ).to_dict()

        song_list = []
        for result in results:
            if self.short_song_ and song_is_short(result['duration']):
                continue

            song_list.append({
                'url': ''.join([YOUTUBE_BASE_URL, result['url_suffix']]),
                'title': re.sub(NON_CHARS, '', result['title']),
                'duration': result['duration']
            })

        return song_list

    def get_audio_urls(self, url):
        audio_urls = []
        with yt_dlp.YoutubeDL({}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info['title']

            # get the audio urls different quality resolutions
            for format in info['formats']:
                if format['resolution'] == 'audio only':
                    audio_urls.append(format['url'])
        return audio_urls, title

    def get_player(self, url):
        media = self.instance.media_new(url)
        media.get_mrl()
        self.player.set_media(media)

    def play(self):
        self.player.play()

    def pause(self, pause):
        self.player.set_pause(pause)

    @property
    def short_song(self) -> bool:
        return self.short_song_

    @short_song.setter
    def short_song(self, val: bool) -> None:
        self.short_song_ = val

    @property
    def length(self):
        return self.player.get_length()

    @property
    def time(self):
        return self.player.get_time()

    @time.setter
    def time(self, val):
        self.player.set_time(val)

    @property
    def volume(self):
        self.player.audio_get_volume()

    @volume.setter
    def volume(self, val):
        self.player.audio_set_volume(int(val))

    def download(self, url, title):
        ''' download method is not implemented
        '''
        output_template = f'{title}.%(ext)s'
        ydl_options = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [
                {'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',
                   'preferredquality': '192',
                },
                {'key': 'FFmpegMetadata'},
            ],
        }
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            _ = ydl.extract_info(YOUTUBE_BASE_URL + url, download=True)


class TkGuiPlayer:
    ''' Tkinter GUI for the youtube player. It connects with the YouTubePlayer by setting
        an instance self.ytp.
    '''
    geometry_window = '610x160'
    window_title = 'Youtube Player'
    file_extensions = [('all types (*.*)', '*.*'), ('json type (*.json)', '*.json')]
    query_width = 30
    pl_width = 50
    poll_time = 1000
    length_progress_bar = 210
    progress_bar_resolution = 0.001
    skip_time = 10000
    length_volume_bar = 80
    max_volume_bar = 100
    init_volume = 30

    def __init__(self):
        self.ytp = YouTubePlayer()
        self.window = Tk()
        self.main_frame = Frame(self.window)
        self.main_frame.grid(row=1, column=1, padx=5, sticky='new')
        self.window.geometry(self.geometry_window)
        self.window.protocol('WM_DELETE_WINDOW', self.quit)
        self.window.title(self.window_title)
        self.query_song_title = StringVar()
        self.query_song_title.set('')
        self.pl_current_title = StringVar()
        self.pl_current_title.set('')
        self.pl_next_title = StringVar()
        self.pl_next_title.set('')
        self.quality_text = StringVar()
        self.shuffle_text = StringVar()
        self.short_text = StringVar()
        self.auto_text = StringVar()
        self.pl_song_time_text = StringVar()
        self.pl_song_time_text.set(' / '.join([str(datetime.timedelta(0)),
            str(datetime.timedelta(0))]))
        self.playlist = []
        self.pl_index = 0
        self.pl_not_played_index_set = set()
        self.querylist = []
        self.query_index = 0
        self.current_song = None
        self.prev_song = None
        self.quality_level = 1
        self.quality_text.set(str(self.quality_level))
        self.shuffle = False
        self.shuffle_text.set('Y' if self.shuffle else 'N')
        self.ytp.short_song = False
        self.short_text.set('Y' if self.ytp.short_song else 'N')
        self.autoplay = True
        self.auto_text.set('Y' if self.autoplay else 'N')
        self.pause = False

        self.set_menubar()
        self.set_query_frame()
        self.set_pl_frame()
        self.pl_show_title()
        self.set_status_frame()
        self.poll_song_status()
        self.window.mainloop()

    def set_menubar(self):
        menubar = Menu(self.window)
        self.set_file_menu()
        menubar.add_cascade(label='File', menu=self.file_menu)
        self.set_quality_menu()
        menubar.add_cascade(label='Quality', menu=self.quality_menu)
        self.set_options_menu()
        menubar.add_cascade(label='Options', menu=self.options_menu)
        self.set_playlist_menu()
        menubar.add_cascade(label='Playlist', menu=self.playlist_menu)
        self.window.config(menu=menubar)

    def set_file_menu(self):
        self.file_menu = Menu(self.window, tearoff=0)
        self.file_menu.add_command(label='open playlist', command=self.open_playlist)
        self.file_menu.add_command(label='save playlist', command=self.save_playlist)

    def set_quality_menu(self):
        self.quality_menu = Menu(self.window, tearoff=0)
        self.quality_menu.add_command(
            label='best quality', command=lambda: self.set_quality('max'))
        self.quality_menu.add_command(
            label='quality up', command=lambda: self.set_quality(1))
        self.quality_menu.add_command(
            label='quality down', command=lambda: self.set_quality(-1))
        self.quality_menu.add_command(
            label='least quality', command=lambda: self.set_quality(0))

    def set_options_menu(self):
        self.options_menu = Menu(self.window, tearoff=0)
        self.options_menu.add_command(label='toggle shuffle', command=self.toggle_shuffle)
        self.options_menu.add_command(label='toggle short song', command=self.toggle_short_song)
        self.options_menu.add_command(label='toggle autoplay', command=self.toggle_autoplay)

    def set_playlist_menu(self):
        self.playlist_menu = Menu(self.window, tearoff=0)
        self.playlist_menu.add_command(
            label='all results to playlist', command=self.import_all_to_playlist)
        self.playlist_menu.add_command(
            label='clear playlist', command=self.clear_playlist)

    def open_playlist(self):
        filename = filedialog.askopenfilename(title='Open a file', filetypes=self.file_extensions)
        with open(filename, 'r') as jsonfile:
            self.playlist = json.load(jsonfile)

    def save_playlist(self):
        filename = filedialog.asksaveasfilename(filetypes=self.file_extensions,
            defaultextension=self.file_extensions)
        with open(filename, 'w') as jsonfile:
            json.dump(self.playlist, jsonfile)

    def set_quality(self, val):
        match val:
            case 'max':
                self.quality_level = 'max'
            case 1:
                self.quality_level = self.quality_level + 1 if self.quality_level != 'max' else 1
            case -1:
                self.quality_level = self.quality_level - 1 if self.quality_level != 'max' else 1
                if self.quality_level < 0: self.quality_level = 0
            case 0:
                self.quality_level = 0
            case _:
                self.quality_level = 1
        self.quality_text.set(str(self.quality_level))

    def toggle_autoplay(self):
        self.autoplay = not self.autoplay
        self.auto_text.set('Y' if self.autoplay else 'N')

    def toggle_short_song(self):
        self.ytp.short_song = not self.ytp.short_song
        self.short_text.set('Y' if self.ytp.short_song else 'N')

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.shuffle_text.set('Y' if self.shuffle else 'N')

    def import_all_to_playlist(self):
        self.playlist += self.querylist

    def clear_playlist(self):
        self.playlist = []
        self.pl_show_title()

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

    def query_songs(self, _):
        self.querylist = self.ytp.search(str(self.query_text_entry.get()))
        if self.querylist:
            self.query_index = 0
            self.query_song_title.set(self.querylist[self.query_index]['title'])

    def query_prev(self):
        if self.querylist:
            self.query_index = (
                self.query_index - 1 if self.query_index > 0
                else len(self.querylist) - 1
            )
            self.query_song_title.set(self.querylist[self.query_index]['title'])

    def query_next(self):
        if self.querylist:
            self.query_index = (
                self.query_index + 1 if self.query_index < len(self.querylist) - 1
                else 0
            )
            self.query_song_title.set(self.querylist[self.query_index]['title'])

    def query_play(self):
        if self.querylist:
            self.play_song(self.querylist[self.query_index])

    def query_add_song(self):
        if self.querylist:
            self.playlist.append(self.querylist[self.query_index])
            self.pl_not_played_index_set = {i for i in range(len(self.playlist))}
            self.pl_index = 0
            self.pl_show_title()

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
            length=self.length_volume_bar, orient='vertical', showvalue=1)
        self.volume_bar.grid(row=2, column=2, rowspan=4, sticky='nw', padx=30)
        self.volume_bar.bind('<ButtonRelease-1>', self.set_volume)
        self.volume_bar.set(self.init_volume)

    def pl_play_prev(self):
        if self.prev_song:
            self.play_song(self.prev_song)

    def pl_play_next(self):
        if self.playlist:

            # find a next short song, if any
            count = 0
            while (self.ytp.short_song
                and not song_is_short(self.playlist[self.pl_index]['duration'])):
                self.pl_next()
                count += 1
                if count > len(self.playlist):
                    self.autoplay = False
                    return

            self.prev_song = self.current_song
            self.play_song(self.playlist[self.pl_index])
            self.pl_not_played_index_set.discard(self.pl_index)
            self.pl_next()

    def pl_play_or_pause(self):
        self.pause = not self.pause
        self.ytp.pause(self.pause)
        if self.pause:
            self.pl_play_pause_button.config(text='|>')

        else:
            self.pl_play_pause_button.config(text='||')

    def pl_song_back(self):
        if self.ytp.length > 0:
            self.ytp.time = self.ytp.time - self.skip_time if self.ytp.time > self.skip_time else 0.0

    def pl_song_forward(self):
        if (length := self.ytp.length) > 0:
            self.ytp.time = (
                self.ytp.time + self.skip_time
                if self.ytp.time + self.skip_time < length else length
            )

    def pl_prev(self):
        if self.playlist:
            if not self.shuffle:
                self.pl_index = divmod(self.pl_index - 1, len(self.playlist))[1]
                self.pl_show_title()

            else:
                self.pl_next()

    def pl_next(self):
        if self.playlist:
            if not self.shuffle:
                self.pl_index = divmod(self.pl_index + 1, len(self.playlist))[1]

            else:
                if not self.pl_not_played_index_set:
                    self.pl_not_played_index_set = {i for i in range(len(self.playlist))}
                self.pl_index = random.choice(list(self.pl_not_played_index_set))

        self.pl_show_title()

    def pl_remove_song(self):
        if self.playlist:
            del self.playlist[self.pl_index]
            self.pl_not_played_index_set = {i for i in range(len(self.playlist))}
            self.pl_index = self.pl_index - 1 if self.playlist else 0
            self.pl_next()

    def pl_show_title(self):
        if self.playlist:
            self.pl_next_title.set(self.playlist[self.pl_index]['title'])

        else:
            self.pl_next_title.set('')

    def set_song_time(self, _):
        self.ytp.time = int(self.progress_bar.get() * self.progress_bar_resolution * self.ytp.length )

    def set_volume(self, _):
        self.ytp.volume = self.volume_bar.get()

    def select_stream(self, song_url):
        if song_url:
            audio_urls, _ = self.ytp.get_audio_urls(song_url)
            if (self.quality_level == 'max' or
                    self.quality_level + 1 > len(audio_urls)):
                self.stream = audio_urls[-1]
                quality_text =  f'max ({len(audio_urls)})'

            else:
                self.stream = audio_urls[self.quality_level]
                quality_text = f'{self.quality_level}'
            self.quality_text.set(quality_text)

    def play_song(self, song_dict):
        self.select_stream(song_dict['url'])
        self.ytp.get_player(self.stream)
        self.ytp.play()
        self.pl_play_pause_button.config(text='||')
        self.pl_current_title.set(song_dict['title'])
        self.current_song = song_dict
        self.pause = False

    def poll_song_status(self):
        time = self.ytp.time * 0.001
        length = self.ytp.length * 0.001
        self.pl_song_time_text.set(' / '.join([
            str(datetime.timedelta(seconds=int(time))),
            str(datetime.timedelta(seconds=int(length)))]))
        self.progress_bar.set(time / length / self.progress_bar_resolution
            if length > 0 else 0.0)

        # fetch the song again if completed; if autoplay then play next song
        if length > 0 and abs(time - length) < 1:
            if self.autoplay:
                self.pl_play_next()

            else:
                self.ytp.get_player(self.stream)
                self.ytp.play()
                self.pause = False
                self.pl_play_or_pause()

        self.window.after(self.poll_time, self.poll_song_status)

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

    def quit(self):
        self.window.after(500, self.window.destroy)


def main():
    TkGuiPlayer()


if __name__ == '__main__':
    main()