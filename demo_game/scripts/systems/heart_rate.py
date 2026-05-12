import math, pygame, random

class HeartRateSystem:
    def __init__(self):
        self.resting_bpm = 80
        self.max_bpm = 160
        self.bpm = self.resting_bpm
        self._bpm_wobble_phase = 0.0

        self._target_bpm: float | None = None
        self._bpm_ramp_rate: float = 1.5

        self.observed_gain = 7
        self.normal_recovery = 3
        self.breath_recovery = 18
        self.breath_timer = 0
        self.breath_required_time = 0.8

        self.is_grounding = False
        self.pulse_timer = 0
        self.stress_units = 0
        self.max_stress_units = 20
        self.stress_unit_min_gain = 0.2
        self.stress_unit_max_gain = 1.0
        self.panic_active = False
        self.panic_timer = 0
        self.panic_duration = 0
        self.coping_worked = True

        """ grounding tap mechanic """
        self.grounding_progress = 0.0
        self.grounding_decay = 7.0
        self.grounding_normal_gain_min = 3.5
        self.grounding_normal_gain_max = 5.0
        self.grounding_overwhelmed_gain_min = 2.0
        self.grounding_overwhelmed_gain_max = 3.5
        self.grounding_overwhelmed_chance = 0.35
        self.grounding_total_bpm_drop = 45.0
        self.grounding_total_stress_drop = 8.0
        self.grounding_flash_timer = 0.0
        self.grounding_success_timer = 0.0
        self.grounding_recovery_active = False
        self.grounding_recovery_target_bpm = 90.0
        self.grounding_recovery_bpm_rate = 18.0
        self.grounding_recovery_stress_rate = 6.0

    def clamp_values(self) -> None:
        self.bpm = max(self.resting_bpm, min(float(self.bpm), self.max_bpm))
        self.stress_units = max(0, min(self.stress_units, self.max_stress_units))
        
    def set_target_bpm(self, bpm: float, ramp_rate: float = 1.5) -> None:
        self._target_bpm = max(self.resting_bpm, min(float(bpm), self.max_bpm))
        self._bpm_ramp_rate = max(0.1, ramp_rate)

    def add_stress_unit(self, amount=1):
        self.stress_units += amount
        self.stress_units = min(self.stress_units, self.max_stress_units)

    def force_bpm(self, bpm, sync_stress=True):
        self.bpm = max(self.resting_bpm, min(float(bpm), self.max_bpm))

        if sync_stress:
            stress_ratio = self.stress_amount()
            self.stress_units = max(0, min(self.max_stress_units, stress_ratio * self.max_stress_units))

    def bump_bpm(self, amount: float) -> None:
        self.bpm = max(self.resting_bpm, min(float(self.bpm + amount), self.max_bpm))

    def is_psychosis(self) -> bool:
        return self.bpm >= 145 and not self.grounding_recovery_active
    
    def coping_state_text(self):
        if self.grounding_recovery_active or self.grounding_progress >= 100:
            return "trying to stay grounded."
        if self.should_show_grounding():
            return "Tap [B]\nHELP ME STAY GROUNDED"
        return ""

    """ grounding mechanic """
    def should_show_grounding(self) -> bool:
        return (
            self.bpm >= 145
            or self.grounding_progress > 0
            or self.grounding_success_timer > 0
            or self.grounding_recovery_active
        )

    def tap_grounding(self) -> None:
        if not self.should_show_grounding(): return
        if self.grounding_recovery_active or self.grounding_progress >= 100: return

        self.is_grounding = True
        self._target_bpm = None

        old_progress = self.grounding_progress
        overwhelmed = self.bpm >= 145 and random.random() < self.grounding_overwhelmed_chance

        if overwhelmed:
            gain = random.uniform(self.grounding_overwhelmed_gain_min, self.grounding_overwhelmed_gain_max)
        else:
            gain = random.uniform(self.grounding_normal_gain_min, self.grounding_normal_gain_max)

        self.grounding_progress = min(100.0, self.grounding_progress + gain)
        actual_gain = self.grounding_progress - old_progress

        bpm_drop = (actual_gain / 100.0) * self.grounding_total_bpm_drop
        stress_drop = (actual_gain / 100.0) * self.grounding_total_stress_drop

        self.bpm = max(self.resting_bpm, self.bpm - bpm_drop)
        self.stress_units = max(0, self.stress_units - stress_drop)
        self.clamp_values()

        if self.grounding_progress >= 100:
            self.complete_grounding()

    def complete_grounding(self) -> None:
        self.panic_active = False
        self.coping_worked = True
        self._target_bpm = None

        self.grounding_progress = 100.0
        self.grounding_success_timer = 0.8
        self.grounding_flash_timer = 0.45
        self.grounding_recovery_active = True

    def start_panic_attack(self, coping_worked=True):
        if self.panic_active:
            return

        self.panic_active = True
        self.coping_worked = coping_worked
        self.panic_timer = 0

        if coping_worked:
            self.panic_duration = random.uniform(2, 4)
        else:
            self.panic_duration = random.uniform(5, 8)

    def update(self, dt, is_observed, breathe_pressed):
        self.is_grounding = breathe_pressed
        has_target = self._target_bpm is not None

        if not has_target and self.bpm >= 145 and not self.panic_active and not self.grounding_recovery_active:
            coping_worked = random.random() < 0.75
            self.start_panic_attack(coping_worked)

        if self.panic_active and not has_target:
            self.panic_timer += dt

            if self.panic_timer < self.panic_duration:
                if self.coping_worked:
                    self.bpm += 6 * dt
                else:
                    self.bpm += 18 * dt
                    self.stress_units += 0.8 * dt
            else:
                self.panic_active = False

        if not has_target:
            if breathe_pressed:
                self.breath_timer += dt

                if self.breath_timer >= self.breath_required_time:
                    if not self.panic_active or self.coping_worked:
                        self.bpm -= self.breath_recovery * dt
                        self.stress_units -= 2.5 * dt
                    else:
                        self.bpm += 4 * dt

                    self.stress_units = max(0, self.stress_units)

            else:
                self.breath_timer = 0
                if is_observed:
                    self.bpm += self.observed_gain * dt
                else:
                    self.bpm -= self.normal_recovery * dt

            if not breathe_pressed and not self.grounding_recovery_active:
                stress_ratio = self.stress_amount()
                stress_unit_gain = self.stress_unit_min_gain + (
                    stress_ratio * (self.stress_unit_max_gain - self.stress_unit_min_gain)
                )
                self.bpm += self.stress_units * stress_unit_gain * 1.5 * dt

        if self._target_bpm is not None:
            step = self._bpm_ramp_rate * dt
            if abs(self._target_bpm - self.bpm) <= step:
                self.bpm = self._target_bpm
                self._target_bpm = None
            elif self._target_bpm > self.bpm:
                self.bpm += step
            else:
                self.bpm -= step

        self._bpm_wobble_phase += dt * 0.9
        elevation = max(0.0, min(1.0, (self.bpm - 100.0) / 60.0))
        wobble_amp = 1.0 + elevation * 5.0
        wobble = math.sin(self._bpm_wobble_phase) * wobble_amp
        self._wobble_offset = wobble

        if self.grounding_flash_timer > 0:
            self.grounding_flash_timer = max(0, self.grounding_flash_timer - dt)

        if self.grounding_success_timer > 0:
            self.grounding_success_timer = max(0, self.grounding_success_timer - dt)
        else:
            if self.grounding_progress > 0 and not self.grounding_recovery_active and self.grounding_progress < 100:
                self.grounding_progress = max(0, self.grounding_progress - self.grounding_decay * dt)

        self.is_grounding = self.grounding_progress > 0
        if self.grounding_recovery_active:
            self.panic_active = False
            self._target_bpm = None

            self.bpm -= self.grounding_recovery_bpm_rate * dt
            self.stress_units -= self.grounding_recovery_stress_rate * dt

            self.bpm = max(self.grounding_recovery_target_bpm, self.bpm)
            self.stress_units = max(0, self.stress_units)
            if self.bpm <= self.grounding_recovery_target_bpm + 0.01:
                self.grounding_recovery_active = False
                self.grounding_progress = 0

        self.clamp_values()

        beats_per_second = self.bpm / 60
        self.pulse_timer += dt * beats_per_second * math.pi * 2

    def stress_amount(self):
        return (self.bpm - self.resting_bpm) / (self.max_bpm - self.resting_bpm)

    @property
    def displayed_bpm(self) -> float:
        offset = getattr(self, "_wobble_offset", 0.0)
        return max(self.resting_bpm, min(self.max_bpm, self.bpm + offset))

    def get_state(self):
        if self.bpm < 100: return "steady heartbeat"
        elif self.bpm < 125: return "irregular"
        elif self.bpm < 145: return "something is coming"
        return "psychosis"

    def render(self, surf):
        if self.bpm < 120 and self.grounding_flash_timer <= 0:
            return
        stress = self.stress_amount()
        pulse = (math.sin(self.pulse_timer) + 1) / 2
        if self.bpm < 135: alpha = int(16 + 28 * pulse)
        elif self.bpm < 145: alpha = int(22 + 45 * pulse)
        elif self.bpm < 165: alpha = int(30 + 70 * pulse)
        else: alpha = int(45 + 100 * pulse)

        if self.grounding_flash_timer > 0: alpha = max(alpha, 90)
        alpha = max(0, min(155, alpha))
        red_overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        red_overlay.fill((255, 0, 0, alpha))
        surf.blit(red_overlay, (0, 0))