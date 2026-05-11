import math, pygame, random

class HeartRateSystem:
    def __init__(self):
        self.resting_bpm = 70
        self.max_bpm = 180
        self.bpm = self.resting_bpm

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

    def add_stress_unit(self, amount=1):
        self.stress_units += amount
        self.stress_units = min(self.stress_units, self.max_stress_units)

    def force_bpm(self, bpm, sync_stress=True):
        self.bpm = max(self.resting_bpm, min(float(bpm), self.max_bpm))

        if sync_stress:
            stress_ratio = self.stress_amount()
            self.stress_units = max(0, min(self.max_stress_units, stress_ratio * self.max_stress_units))

    def coping_state_text(self):
        if self.is_grounding and self.panic_active and not self.coping_worked:
            return "it is not working... keep trying"
        if self.is_grounding:
            return "keep breathing..."
        if self.get_state() in ("panic attack", "psychosis"):
            return "hold B to breathe"
        return ""

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

        if self.bpm >= 145 and not self.panic_active:
            coping_worked = random.random() < 0.75
            self.start_panic_attack(coping_worked)

        if self.panic_active:
            self.panic_timer += dt

            if self.panic_timer < self.panic_duration:
                if self.coping_worked:
                    self.bpm += 6 * dt
                else:
                    self.bpm += 18 * dt
                    self.stress_units += 0.8 * dt
            else:
                self.panic_active = False

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

        if not breathe_pressed:
            stress_ratio = self.stress_amount()
            stress_unit_gain = self.stress_unit_min_gain + (
                stress_ratio * (self.stress_unit_max_gain - self.stress_unit_min_gain)
            )
            self.bpm += self.stress_units * stress_unit_gain * 1.5 * dt

        self.bpm = max(self.resting_bpm, min(self.bpm, self.max_bpm))
        self.stress_units = max(0, min(self.stress_units, self.max_stress_units))

        beats_per_second = self.bpm / 60
        self.pulse_timer += dt * beats_per_second * math.pi * 2

    def stress_amount(self):
        return (self.bpm - self.resting_bpm) / (self.max_bpm - self.resting_bpm)

    def get_state(self):
        if self.bpm < 100:
            return "steady heartbeat"
        elif self.bpm < 125:
            return "irregular"
        elif self.bpm < 145:
            return "something is coming"
        elif self.bpm < 165:
            return "panic attack"
        return "psychosis"

    def render(self, surf):
        stress = self.stress_amount()
        if stress <= 0:
            return

        pulse = (math.sin(self.pulse_timer) + 1) / 2
        alpha = int(8 + stress * 75 * pulse)

        red_overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        red_overlay.fill((255, 0, 0, alpha))
        surf.blit(red_overlay, (0, 0))