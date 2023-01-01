'''
Gui YouTube player: based on question
https://codereview.stackexchange.com/questions/282051/a-gui-youtube-audio-player/282130#282130
'''
import random
import json
from collections import deque
from youtube_player_model import song_is_short


class Controller:
    ''' Tkinter GUI controller for the youtube player. It connects with the YouTubePlayerModel and TkGuiView by
        passing model and view
    '''
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.playlist = deque()
        self.playlist_rotations = 0
        self.pl_not_played_set = set()
        self.querylist = deque()
        self.querylist_rotations = 0
        self.current_song = None
        self.prev_song = None
        self.pause = False
        self.skip_time = 10000

    def set_initial_values(self):
        self.quality_level = 1
        self.shuffle = False
        self.model.short_song = False
        self.autoplay = True
        volume = 60
        return self.quality_level, self.shuffle, self.model.short_song, self.autoplay, volume

    def open_playlist(self, filename):
        with open(filename, 'r') as jsonfile:
            self.playlist = deque(json.load(jsonfile))
        self.pl_not_played_set = {v['url'] for v in self.playlist}
        self.view.pl_show_title(self.playlist[0]['title'])

    def save_playlist(self, filename):
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

        return self.quality_level

    def toggle_autoplay(self):
        self.autoplay = not self.autoplay
        return self.autoplay

    def toggle_short_song(self):
        self.model.short_song = not self.model.short_song
        return self.model.short_song

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        return self.shuffle

    def import_all_to_playlist(self):
        if self.querylist:
            self.playlist.rotate(-self.playlist_rotations)
            self.playlist.extend(self.querylist)
            self.pl_not_played_set |= {v['url'] for v in self.querylist}
            self.playlist_rotations += len(self.querylist) if self.playlist_rotations > 0 else 0
            self.playlist.rotate(+self.playlist_rotations)
            self.pl_show_title()

    def clear_playlist(self):
        self.playlist = deque()
        self.pl_not_played_set = set()
        self.playlist_rotations = 0
        self.view.pl_show_title('')

    def query_songs(self, query_text):
        self.querylist = deque(self.model.search(query_text))
        return self.querylist[0]['title'] if self.querylist else None

    def query_prev(self):
        if self.querylist:
            # shift right (+1) moves the previous element into position
            self.querylist.rotate(+1)
            return self.querylist[0]['title']

    def query_next(self):
        if self.querylist:
            # shift left (-1) moves the next element into position
            self.querylist.rotate(-1)
            return self.querylist[0]['title']

    def query_play(self):
        if self.querylist:
            self.play_song(self.querylist[0])

    def query_add_song(self):
        if self.querylist:
            self.playlist.rotate(-self.playlist_rotations)
            self.playlist.append(self.querylist[0])
            self.pl_not_played_set.add(self.querylist[0]['url'])
            self.playlist_rotations += 1 if self.playlist_rotations > 0 else 0
            self.playlist.rotate(+self.playlist_rotations)
            self.pl_show_title()

    def pl_play_prev(self):
        if self.prev_song:
            previous_song = self.current_song
            self.play_song(self.prev_song)
            self.prev_song = previous_song

    def pl_play_next(self):
        title = None
        quality_text = None
        if self.playlist:
            # find a next short song, if any
            count = 0
            while (self.model.short_song
                and not song_is_short(self.playlist[0]['duration'])):
                self.pl_next()
                count += 1
                if count > len(self.playlist):
                    if self.autoplay: self.toggle_autoplay()
                    return

            self.prev_song = self.current_song
            self.play_song(self.playlist[0])
            if (url := self.playlist[0]['url']) in self.pl_not_played_set:
                self.pl_not_played_set.remove(url)
            self.pl_next()
            print(f'remaining song not yet played: {len(self.pl_not_played_set)}')

        return title, quality_text

    def pl_play_or_pause(self):
        self.pause = not self.pause
        self.model.pause(self.pause)
        return self.pause

    def pl_song_back(self):
        if self.model.length > 0:
            self.model.time = self.model.time - self.skip_time if self.model.time > self.skip_time else 0.0

    def pl_song_forward(self):
        if (length := self.model.length) > 0:
            self.model.time = (self.model.time + self.skip_time
                if self.model.time + self.skip_time < length else length)

    def pl_prev(self):
        if self.playlist:
            # shift right (+1) moves the previous element into position
            if not self.shuffle:
                self.playlist_rotate(+1)
                self.pl_show_title()

            else:
                self.pl_next()

    def pl_next(self):
        if self.playlist:
            if not self.pl_not_played_set:
                self.pl_not_played_set = {v['url'] for v in self.playlist}

            # shift left (-1) moves the next element into position
            if not self.shuffle:
                self.playlist_rotate(-1)

            else:
                url = random.choice(list(self.pl_not_played_set))
                index = next((i for i, v in enumerate(self.playlist) if v['url'] == url), 0)
                self.playlist_rotate(-index)

        self.pl_show_title()

    def pl_remove_song(self):
        if self.playlist:
            if (url := self.playlist[0]['url']) in self.pl_not_played_set:
                self.pl_not_played_set.remove(url)
            del self.playlist[0]
            self.playlist_rotations -= 1
            self.playlist_rotate(1)
            self.pl_next()

    def pl_show_title(self):
        title = None
        if self.playlist:
            title = self.playlist[0]['title']
        self.view.pl_show_title(title)

    def set_song_time(self, time_):
        self.model.time = int(time_ * self.view.progress_bar_resolution * self.model.length)

    def set_volume(self, volume):
        self.model.volume = volume

    def select_stream(self, song_url):
        if song_url:
            audio_urls, _ = self.model.get_audio_urls(song_url)
            if not audio_urls:
                return None

            if (self.quality_level == 'max' or
                    self.quality_level + 1 > len(audio_urls)):
                self.stream = audio_urls[-1]
                quality_text =  f'max ({len(audio_urls)})'

            else:
                self.stream = audio_urls[self.quality_level]
                quality_text = f'{self.quality_level}'
            return quality_text

    def play_song(self, song_dict):
        quality_text = self.select_stream(song_dict['url'])
        if quality_text is None:
            return

        self.model.get_player(self.stream)
        self.model.play()
        self.current_song = song_dict
        self.pause = True
        self.pl_play_or_pause()
        self.view.pl_show_current_title(song_dict['title'], quality_text)

    def update_song_status(self):
        time = self.model.time * 0.001
        length = self.model.length * 0.001

        # fetch the song again if completed; if autoplay then play next song
        if length > 0 and abs(time - length) < 1:
            if self.autoplay:
                self.pl_play_next()

            else:
                self.model.get_player(self.stream)
                self.model.play()
                self.pause = False
                self.pl_play_or_pause()

        return time, length

    def playlist_rotate(self, val):
        self.playlist.rotate(val)
        self.playlist_rotations = (
            (self.playlist_rotations + val) % len(self.playlist) if len(self.playlist) else 0
        )

    def quit(self):
        self.view.exit()
