import math
import time

from core.sumulation_runner import SimulationRunner


class FakeWorld:
    def __init__(self):
        self.update_calls = 0
        self.fixed_update_calls = 0

    def update(self, dt):
        self.update_calls += 1

    def fixed_update(self, dt):
        self.fixed_update_calls += 1


def wait_for_pending_steps_to_drain(runner, timeout=1.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with runner.lock:
            if runner.pending_steps == 0:
                return
        time.sleep(0.01)


def test_toggle_pause():
    runner = SimulationRunner(FakeWorld())
    assert runner.paused is False

    assert runner.toggle_pause() is True
    assert runner.paused is True

    assert runner.toggle_pause() is False
    assert runner.paused is False


def test_set_target_fps():
    runner = SimulationRunner(FakeWorld(), target_fps=60)
    runner.set_target_fps(math.inf)
    assert runner.target_fps == math.inf


def test_step_pauses_immediately_and_queues_steps():
    runner = SimulationRunner(FakeWorld(), target_fps=60, paused=False)
    runner.step(3)

    assert runner.paused is True
    assert runner.pending_steps == 3


def test_paused_runner_does_not_step():
    world = FakeWorld()
    runner = SimulationRunner(world, target_fps=math.inf, paused=True)
    runner.start()
    time.sleep(0.1)
    runner.stop()

    assert world.update_calls == 0
    assert world.fixed_update_calls == 0


def test_resume_allows_stepping_again():
    world = FakeWorld()
    runner = SimulationRunner(world, target_fps=math.inf, paused=True)
    runner.start()
    time.sleep(0.05)
    runner.resume()
    # Comfortably longer than IDLE_SLEEP so the background thread is
    # guaranteed to wake up and notice the unpause at least once.
    time.sleep(0.2)
    runner.stop()

    assert world.update_calls > 0


def test_step_runs_exact_count_then_stays_paused():
    world = FakeWorld()
    runner = SimulationRunner(world, target_fps=math.inf, paused=True)
    runner.start()

    runner.step(5)
    wait_for_pending_steps_to_drain(runner)
    runner.stop()

    assert world.update_calls == 5
    assert world.fixed_update_calls == 5
    assert runner.paused is True


def test_uncapped_speed_runs_many_steps_quickly():
    world = FakeWorld()
    runner = SimulationRunner(world, target_fps=math.inf)
    runner.start()
    time.sleep(0.05)
    runner.stop()

    # An empty-loop step is essentially free; uncapped should comfortably
    # clear a few hundred iterations in 50ms.
    assert world.update_calls > 100


def test_capped_speed_limits_steps():
    world = FakeWorld()
    runner = SimulationRunner(world, target_fps=20)  # ~50ms per step
    runner.start()
    time.sleep(0.12)
    runner.stop()

    assert 1 <= world.update_calls <= 4
