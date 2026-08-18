import math
import threading
import time

FIXED_DT = 1.0 / 60
IDLE_SLEEP = 0.05  # while paused with nothing queued, avoid busy-spinning


class SimulationRunner:
    def __init__(self, world, target_fps=60, paused=False):
        self.world = world
        self.target_fps = target_fps
        self.paused = paused
        self.pending_steps = 0

        self.thread = None
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.simulation_thread, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def set_target_fps(self, target_fps):
        self.target_fps = target_fps

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def toggle_pause(self):
        self.paused = not self.paused
        return self.paused

    def step(self, count: int):
        """Force `count` simulation steps to run even while paused (pausing
        first, if not already), regardless of the current speed setting."""
        self.paused = True
        with self.lock:
            self.pending_steps += max(0, count)

    def simulation_thread(self):
        while self.running:
            start_time = time.time()

            did_step = False
            with self.lock:
                if self.pending_steps > 0:
                    self.pending_steps -= 1
                    did_step = True
                elif not self.paused:
                    did_step = True

                if did_step:
                    self.world.update(FIXED_DT)
                    self.world.fixed_update(FIXED_DT)

            if not did_step:
                time.sleep(IDLE_SLEEP)
                continue

            if self.target_fps == math.inf:
                continue

            frame_duration = 1.0 / self.target_fps
            elapsed = time.time() - start_time
            time.sleep(max(0.0, frame_duration - elapsed))
