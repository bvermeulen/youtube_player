'''
Gui YouTube player: based on question
https://codereview.stackexchange.com/questions/282051/a-gui-youtube-audio-player/282130#282130
'''
import re
from collections import deque
from youtube_search import YoutubeSearch
import vlc
import yt_dlp

MAX_SEARCH_RESULTS = 40
MAX_SONG_LENGTH = 300
YOUTUBE_BASE_URL = 'https://www.youtube.com'
INVALID_CHARS = re.compile(r'[^a-zA-Z0-9 .,:;+-=!?/()öäßü]')


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


class YouTubePlayerModel:
    ''' Class with methods to search songs on YouTube, get
        audio urls, play song with a vlc player and provide
        API
    '''
    def __init__(self, short_song: bool=False):
        self.short_song_ = short_song
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()

    def search(self, search_query):
        results = YoutubeSearch(
            search_query, max_results=MAX_SEARCH_RESULTS
        ).to_dict()

        song_list = []
        for result in results:
            if self.short_song_ and not song_is_short(result['duration']):
                continue

            song_list.append({
                'url': ''.join([YOUTUBE_BASE_URL, result['url_suffix']]),
                'title': re.sub(INVALID_CHARS, '', result['title']),
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
        media = self.vlc_instance.media_new(url)
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

