import json
from pathlib import Path
from scripts.core.interact import InteractZone
from scripts.core.walkable_zone import WalkableZone


class InteractableDef:
    def __init__(self, zone: InteractZone, flags_true: list[str], flags_false: list[str], interaction_condition: list[str], not_flags: list[str]):
        self.zone = zone
        self.flags_true = flags_true
        self.flags_false = flags_false
        self.interaction_condition = interaction_condition
        self.not_flags = not_flags

    def can_interact(self, flags: dict) -> bool:
        if not all(flags.get(k, False) for k in self.interaction_condition):
            return False
        if any(flags.get(k, False) for k in self.not_flags):
            return False
        return True

    def apply_flags(self, flags: dict) -> None:
        for k in self.flags_true: flags[k] = True
        for k in self.flags_false: flags[k] = False

def _resolve_offset(scene, cfg: dict) -> int:
    attr = cfg.get("world_offset")
    if not attr: return 0
    return int(getattr(scene, attr))

def _ensure_flags(scene, *flag_lists: list[str]) -> None:
    for lst in flag_lists:
        for key in lst:
            if key not in scene.flags:
                scene.flags[key] = False


def load_interactables(json_path: str | Path, scene, font, glow_surf) -> tuple[dict[str, "InteractableDef"], dict[str, WalkableZone]]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    interactables: dict[str, InteractableDef] = {}
    walkables: dict[str, WalkableZone] = {}

    for zone_id, cfg in data.items():
        offset_x = _resolve_offset(scene, cfg)
        points = [(x + offset_x, y) for x, y in cfg["points"]]
        kind = cfg.get("kind", "interactable")
        if kind == "walkable":
            prohibited = [
                [(x + offset_x, y) for x, y in poly]
                for poly in cfg.get("prohibited_points", [])
            ]
            condition = cfg.get("interaction_condition", [])
            _ensure_flags(scene, condition)

            walkables[zone_id] = WalkableZone(
                points=points,
                prohibited_polygons=prohibited,
                min_scale=float(cfg.get("min_scale", 0.6)),
                interaction_condition=condition,
            )
        else:
            flags_true = cfg.get("flags_true", [])
            flags_false = cfg.get("flags_false", [])
            condition = cfg.get("interaction_condition", [])
            not_flags = cfg.get("not_flags", [])
            _ensure_flags(scene, flags_true, flags_false, condition, not_flags)

            zone = InteractZone(
                points=points,
                prompt=cfg["prompt"],
                font=font,
                glow_surf=glow_surf,
                proximity_inflate=cfg.get("proximity_inflate", 40),
                fade_speed=cfg.get("fade_speed", 650),
            )
            interactables[zone_id] = InteractableDef(
                zone=zone,
                flags_true=flags_true,
                flags_false=flags_false,
                interaction_condition=condition,
                not_flags=not_flags,
            )

    return interactables, walkables