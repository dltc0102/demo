import pygame, math, random

Point = tuple[float, float]

class GhostMoveArea:
    def __init__(self, name: str, room: str, points: list[Point], *, holes: list[list[Point]] | None = None, weight: float = 1.0):
        self.name = name
        self.room = room
        self.points = points
        self.holes = holes or []
        self.weight = weight
        self.kind = "polygon" if len(points) >= 4 else "path"

    def bounds(self) -> tuple[float, float, float, float]:
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return min(xs), min(ys), max(xs), max(ys)

    def center_y(self) -> float:
        return sum(p[1] for p in self.points) / max(1, len(self.points))

class AmbientGhost:
    BASE_SIZE = (76, 92)

    def __init__(self, game, anchor_pos: Point, area_name: str | None = None):
        self.game = game
        self.area_name = area_name
        self.pending_area_name: str | None = None
        self.pos = [0.0, 0.0]
        self.set_anchor(float(anchor_pos[0]), float(anchor_pos[1]))
        self.spawn_y = float(self.pos[1])
        self.target_anchor = list(anchor_pos)

        self.alpha = 0.0
        self.max_alpha = random.randint(80, 145)
        self.speed = random.uniform(35, 75)
        self.wobble_seed = random.uniform(0, 1000)
        self.next_speak_time = pygame.time.get_ticks() + random.randint(1200, 4500)
        self.dead = False
        self.mode = "room"

    @property
    def ghost_w(self) -> int:
        return self.BASE_SIZE[0]

    @property
    def ghost_h(self) -> int:
        return self.BASE_SIZE[1]

    def anchor(self) -> list[float]:
        return [self.pos[0] - self.ghost_w / 2, self.pos[1] + self.ghost_h / 2]

    def set_anchor(self, x: float, y: float) -> None:
        self.pos[0] = x + self.BASE_SIZE[0] / 2
        self.pos[1] = y - self.BASE_SIZE[1] / 2

    def rect(self) -> pygame.Rect:
        x, y = self.anchor()
        return pygame.Rect(int(x), int(y - self.ghost_h), self.ghost_w, self.ghost_h)

    def _scale_factor(self) -> float:
        rise = self.spawn_y - self.pos[1]
        rise = max(0.0, min(rise, 90.0))
        return 1.0 - rise / 90.0 * 0.5

    def pick_new_target(self, room_left: int = 0, room_right: int | None = None, fridge_rect: pygame.Rect | None = None) -> None:
        if hasattr(self.game, "ghost_manager"):
            self.game.ghost_manager.pick_target_for_ghost(self, room_left, room_right)

    def update(self, dt: float, manager, room_left: int, room_right: int, fridge_rect: pygame.Rect | None = None) -> None:
        if self.mode == "fading":
            self.alpha = max(0, self.alpha - 130 * dt)
        else:
            self.alpha = min(self.max_alpha, self.alpha + 120 * dt)

        if self.mode != "fading":
            ax, ay = self.anchor()
            tx, ty = self.target_anchor
            dx = tx - ax
            dy = ty - ay
            dist = math.hypot(dx, dy)

            if dist <= 2:
                self.set_anchor(tx, ty)
                if self.pending_area_name:
                    self.area_name = self.pending_area_name
                    self.pending_area_name = None
                    self.spawn_y = self.pos[1]
                manager.pick_target_for_ghost(self, room_left, room_right)
            else:
                step = min(dist, self.speed * dt)
                nx = ax + dx / dist * step
                ny = ay + dy / dist * step
                nx, ny = manager.clamp_anchor_to_room(nx, ny, room_left, room_right)
                self.set_anchor(nx, ny)

        self.try_speak(manager)

    def try_speak(self, manager) -> None:
        now = pygame.time.get_ticks()
        if now < self.next_speak_time: return
        if random.random() > 0.45:
            self.next_speak_time = now + random.randint(2500, 6500)
            return
        manager.make_ghost_say(self)
        self.next_speak_time = now + random.randint(5500, 12000)

    def start_fade(self) -> None:
        self.mode = "fading"
        self.max_alpha = 0

    def render(self, surface: pygame.Surface, offset=(0, 0)) -> None:
        if self.alpha <= 0: return
        x = int(self.pos[0] - offset[0])
        y = int(self.pos[1] - offset[1])

        if x < -120 or x > surface.get_width() + 120: return
        alpha = max(0, min(255, int(self.alpha)))

        scale = self._scale_factor()
        bw = max(4, int(self.BASE_SIZE[0] * scale))
        bh = max(4, int(self.BASE_SIZE[1] * scale))

        ghost_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)

        pygame.draw.ellipse(ghost_surf, (190, 205, 255, int(alpha * 0.10)), (int(5*scale), int(4*scale), int(66*scale), int(78*scale)))
        pygame.draw.ellipse(ghost_surf, (210, 220, 255, int(alpha * 0.22)), (int(15*scale), int(12*scale), int(46*scale), int(60*scale)))
        pygame.draw.ellipse(ghost_surf, (245, 248, 255, int(alpha * 0.10)), (int(22*scale), int(28*scale), int(32*scale), int(34*scale)))

        eye_r = max(1, int(2 * scale))
        pygame.draw.circle(ghost_surf, (255, 255, 255, int(alpha * 0.38)), (int(31*scale), int(35*scale)), eye_r)
        pygame.draw.circle(ghost_surf, (255, 255, 255, int(alpha * 0.38)), (int(45*scale), int(35*scale)), eye_r)

        for i in range(4):
            wx = int((20 + i * 9) * scale)
            wy = int(68 * scale) + int(math.sin(pygame.time.get_ticks() * 0.006 + i) * 4 * scale)
            pygame.draw.circle(ghost_surf, (210, 220, 255, int(alpha * 0.15)), (wx, wy), max(2, int(8 * scale)))

        surface.blit(ghost_surf, (x - bw // 2, y - bh // 2))

class GhostManager:
    PADDING = 2

    def __init__(self, game):
        self.game = game
        self.ghosts: list[AmbientGhost] = []
        self.enabled = True
        self.max_ghosts = 5
        self.next_spawn_time = pygame.time.get_ticks() + random.randint(4000, 9000)
        self.current_room: str | None = None
        self.areas_by_room: dict[str, list[GhostMoveArea]] = {}
        self.areas_by_name: dict[str, GhostMoveArea] = {}
        self.build_movement_areas()

    @property
    def ghost_w(self) -> int:
        return AmbientGhost.BASE_SIZE[0]

    @property
    def ghost_h(self) -> int:
        return AmbientGhost.BASE_SIZE[1]

    def add_area(self, area: GhostMoveArea) -> None:
        self.areas_by_room.setdefault(area.room, []).append(area)
        self.areas_by_name[area.name] = area

    def sx(self, x: float) -> float:
        return x - self.ghost_w

    def world_points(self, points: list[Point], world_x: float = 0) -> list[Point]:
        return [(x + world_x, y) for x, y in points]

    def build_movement_areas(self) -> None:
        kx = self.game.internal_w

        self.add_area(GhostMoveArea("bedroom_floor", "bedroom", [(1, 438), (364, 434), (420, 423), (563, 423), (718, 423), (718, 533), (1, 533)], weight=5.0))
        self.add_area(GhostMoveArea("bedroom_bed", "bedroom", [(151, 363), (190, 351), (409, 357), (363, 370)], weight=2.0))
        self.add_area(GhostMoveArea("shelf_1", "bedroom", [(54, 142), (204, 142)], weight=1.2))
        self.add_area(GhostMoveArea("shelf_2", "bedroom", [(557, 295), (706, 296)], weight=1.0))
        self.add_area(GhostMoveArea("shelf_3", "bedroom", [(623, 238), (702, 237)], weight=1.0))

        kitchen_floor = self.world_points([(2, 357), (self.sx(119), 361), (self.sx(130), 366), (self.sx(433), 360), (self.sx(642), 457), (718, 450), (718, 545), (2, 545)], kx)
        island_hole = self.world_points([(154, 363), (self.sx(411), 360), (self.sx(413), 471), (184, 471), (155, 437)], kx)
        self.add_area(GhostMoveArea("kitchen_floor", "kitchen", kitchen_floor, holes=[island_hole], weight=5.0))
        self.add_area(GhostMoveArea("above_the_fridge", "kitchen", self.world_points([(565, 136), (641, 132), (self.sx(718), 129)], kx), weight=0.9))
        self.add_area(GhostMoveArea("cupboard1", "kitchen", self.world_points([(129, 98), (self.sx(212), 105)], kx), weight=0.9))
        self.add_area(GhostMoveArea("cupboard2", "kitchen", self.world_points([(338, 96), (467, 98), (self.sx(608), 85)], kx), weight=0.9))
        self.add_area(GhostMoveArea("island_top", "kitchen", self.world_points([(155, 303), (self.sx(367), 301), (self.sx(412), 331), (185, 334)], kx), weight=1.8))
        self.add_area(GhostMoveArea("sink_top", "kitchen", self.world_points([(128, 270), (self.sx(495), 264)], kx), weight=1.2))
        self.add_area(GhostMoveArea("sink_top2", "kitchen", self.world_points([(self.sx(495), 264), (self.sx(554), 287)], kx), weight=0.9))

    def clear(self) -> None:
        self.ghosts.clear()
        self.next_spawn_time = pygame.time.get_ticks() + random.randint(4000, 9000)

    def point_in_polygon(self, point: Point, polygon: list[Point]) -> bool:
        x, y = point
        inside = False
        j = len(polygon) - 1
        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if ((yi > y) != (yj > y)) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1) + xi:
                inside = not inside
            j = i
        return inside

    def clamp_anchor_to_room(self, x: float, y: float, room_left: int, room_right: int) -> Point:
        min_x = room_left + self.PADDING
        max_x = room_right - self.ghost_w - self.PADDING
        return max(min_x, min(max_x, x)), y

    def random_point_in_area(self, area: GhostMoveArea, room_left: int, room_right: int) -> Point:
        if area.kind == "path":
            point = self.random_point_on_path(area.points)
            return self.clamp_anchor_to_room(point[0], point[1], room_left, room_right)

        min_x, min_y, max_x, max_y = area.bounds()
        min_x = max(min_x, room_left + self.PADDING)
        max_x = min(max_x, room_right - self.ghost_w - self.PADDING)
        if max_x < min_x:
            max_x = min_x

        for _ in range(180):
            x = random.uniform(min_x, max_x)
            y = random.uniform(min_y, max_y)
            if not self.point_in_polygon((x, y), area.points):
                continue
            if any(self.point_in_polygon((x, y), hole) for hole in area.holes):
                continue
            return x, y

        point = random.choice(area.points)
        return self.clamp_anchor_to_room(point[0], point[1], room_left, room_right)

    def random_point_on_path(self, points: list[Point]) -> Point:
        if len(points) == 1:
            return points[0]

        segments = list(zip(points, points[1:]))
        lengths = [max(1.0, math.dist(a, b)) for a, b in segments]
        pick = random.uniform(0, sum(lengths))
        running = 0.0

        for (a, b), length in zip(segments, lengths):
            running += length
            if pick <= running:
                t = random.random()
                return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t

        return points[-1]

    def room_from_bounds(self, room_left: int) -> str:
        return "kitchen" if room_left >= self.game.internal_w else "bedroom"

    def pick_spawn_area(self, room_name: str) -> GhostMoveArea | None:
        areas = self.areas_by_room.get(room_name, [])
        if not areas: return None
        return random.choices(areas, weights=[area.weight for area in areas], k=1)[0]

    def get_lower_areas(self, ghost: AmbientGhost, room_name: str) -> list[GhostMoveArea]:
        current = self.areas_by_name.get(ghost.area_name or "")
        if not current: return []
        current_y = current.center_y()
        return [area for area in self.areas_by_room.get(room_name, []) if area.name != current.name and area.center_y() > current_y + 28]

    def pick_target_for_ghost(self, ghost: AmbientGhost, room_left: int, room_right: int) -> None:
        room_name = self.current_room or self.room_from_bounds(room_left)
        current_area = self.areas_by_name.get(ghost.area_name or "")

        if not current_area or current_area.room != room_name:
            current_area = self.pick_spawn_area(room_name)
            if not current_area: return
            ghost.area_name = current_area.name

        lower_areas = self.get_lower_areas(ghost, room_name)
        should_drop = bool(lower_areas) and random.random() < 0.22

        if should_drop:
            next_area = random.choice(lower_areas)
            ghost.pending_area_name = next_area.name
            ghost.target_anchor = list(self.random_point_in_area(next_area, room_left, room_right))
            ghost.speed = random.uniform(70, 120)
        else:
            ghost.pending_area_name = None
            ghost.target_anchor = list(self.random_point_in_area(current_area, room_left, room_right))
            ghost.speed = random.uniform(30, 75)

    def spawn(self, room_left: int, room_right: int, room_name: str | None = None) -> None:
        room_name = room_name or self.room_from_bounds(room_left)
        area = self.pick_spawn_area(room_name)
        if not area: return

        player_rect = self.game.player.rect()
        anchor = self.random_point_in_area(area, room_left, room_right)

        for _ in range(40):
            candidate = self.random_point_in_area(area, room_left, room_right)
            if math.dist(candidate, player_rect.midbottom) >= 90:
                anchor = candidate
                break

        ghost = AmbientGhost(self.game, anchor, area.name)
        self.pick_target_for_ghost(ghost, room_left, room_right)
        self.ghosts.append(ghost)

    def make_ghost_say(self, ghost: AmbientGhost) -> None:
        kind = random.choices(["positive", "neutral", "negative"], weights=[1, 3, 4], k=1)[0]
        if kind == "positive":
            pool = getattr(self.game, "ghost_positive_dialogues", ["keep breathing"])
        elif kind == "neutral":
            pool = getattr(self.game, "ghost_neutral_dialogues", ["look around"])
        else:
            pool = getattr(self.game, "ghost_negative_dialogues", ["they are watching"])
            if hasattr(self.game, "heart_rate"):
                self.game.heart_rate.add_stress_unit(random.uniform(0.15, 0.45))
        line = random.choice(pool)
        self.game.dialogue_manager.dialogue_object(text=line, target=ghost, stall=900, interval=38, speech_sfx=False)

    def update(self, dt: float, room_left: int = 0, room_right: int | None = None, fridge_rect: pygame.Rect | None = None, active: bool = True, room_name: str | None = None) -> None:
        if room_right is None:
            room_right = self.game.internal_w
        room_name = room_name or self.room_from_bounds(room_left)

        if self.current_room != room_name:
            self.current_room = room_name
            self.clear()

        if not self.enabled or not active: return

        now = pygame.time.get_ticks()
        if now >= self.next_spawn_time and len(self.ghosts) < self.max_ghosts:
            self.spawn(room_left, room_right, room_name)
            self.next_spawn_time = now + random.randint(5500, 14000)

        for ghost in self.ghosts[:]:
            ghost.update(dt, self, room_left, room_right, fridge_rect)
            if ghost.dead or (ghost.mode == "fading" and ghost.alpha <= 0):
                self.ghosts.remove(ghost)

    def render(self, surface: pygame.Surface, offset=(0, 0)) -> None:
        if not self.enabled: return
        for ghost in self.ghosts:
            ghost.render(surface, offset=offset)

    def is_player_observed(self) -> bool:
        player_x = self.game.player.rect().centerx
        for ghost in self.ghosts:
            if abs(ghost.pos[0] - player_x) < 140 and ghost.alpha > 50:
                return True
        return False
