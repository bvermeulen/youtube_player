'''
Gui YouTube player: based on question
https://codereview.stackexchange.com/questions/282051/a-gui-youtube-audio-player/282130#282130
'''
from youtube_player_model import YouTubePlayerModel
from youtube_player_view import TkGuiView
from youtube_player_controller import Controller

class App:
    def __init__(self):
        model = YouTubePlayerModel()
        view = TkGuiView()
        controller = Controller(model, view)
        view.set_controller(controller)
        view.mainloop()

if __name__ == '__main__':
    app = App()
