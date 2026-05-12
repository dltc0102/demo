class LevelManager:
    def __init__(self, game):
        self.game = game
        self.current_level = "bedroom_night"
        self.fade_alpha = 0
        self.transitioning = False
        self.next_level = None

    def change_level(self, next_level):
        self.next_level = next_level
        self.transitioning = True
        self.fade_alpha = 0