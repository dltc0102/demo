import math
import random


class GhostManager:
    def __init__(self, game):
        self.game = game
        self.ghosts = []
        self.enabled = False
        self.fade_alpha = 0

    def point_too_close(self, x, y, min_dist=80):
        for ghost in self.ghosts:
            gx, gy = ghost.pos

            dist = math.dist((x, y), (gx, gy))

            if dist < min_dist:
                return True

        return False

    def activate(self, amount=5):
        self.ghosts.clear()

        for _ in range(amount):
            while True:
                x = random.randint(50, self.game.internal_w - 50)
                y = random.randint(50, self.game.internal_h - 120)

                if not self.point_too_close(x, y):
                    break

            ghost = self.game.Ghost(self.game, pos=[x, y])

            self.ghosts.append(ghost)

        self.enabled = True

    def deactivate(self):
        self.enabled = False

    def fade_out(self, speed=5):
        for ghost in self.ghosts:
            ghost.alpha = max(0, ghost.alpha - speed)

    def update_random_trigger(self):
        if random.random() < 0.002:
            self.activate()

    def is_player_observed(self):
        player_x = self.game.player.pos[0]

        for ghost in self.ghosts:
            gx = ghost.pos[0]

            if abs(gx - player_x) < 120:
                return True

        return False

    def update(self, dt):
        if not self.enabled:
            return

        for ghost in self.ghosts:
            ghost.update(dt)

    def render(self, surface, offset=(0, 0)):
        if not self.enabled:
            return

        for ghost in self.ghosts:
            ghost.render(surface, offset=offset)