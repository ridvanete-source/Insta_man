from insta_man import health
from insta_man.config import Config


def make_config() -> Config:
    return Config(
        notify_email_enabled=False,  # send_email() no-ops immediately, safe for tests
    )


def test_first_failures_stay_below_threshold_and_dont_notify(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "HEALTH_FILE", tmp_path / "health_state.json")
    config = make_config()

    for _ in range(health.FAILURE_THRESHOLD - 1):
        health.record_failure(config, "boom")

    assert health.should_skip_run() is None


def test_reaching_threshold_notifies_once_then_skips(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "HEALTH_FILE", tmp_path / "health_state.json")
    config = make_config()

    calls = []
    monkeypatch.setattr(health.notifier, "send_email", lambda cfg, subject, body: calls.append(subject))

    for _ in range(health.FAILURE_THRESHOLD):
        health.record_failure(config, "boom")
    assert len(calls) == 1
    assert health.should_skip_run() is not None

    # Further failures past the threshold must not send a second email.
    health.record_failure(config, "boom again")
    assert len(calls) == 1
    assert health.should_skip_run() is not None


def test_success_resets_state_so_a_future_outage_can_notify_again(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "HEALTH_FILE", tmp_path / "health_state.json")
    config = make_config()

    calls = []
    monkeypatch.setattr(health.notifier, "send_email", lambda cfg, subject, body: calls.append(subject))

    for _ in range(health.FAILURE_THRESHOLD):
        health.record_failure(config, "boom")
    assert health.should_skip_run() is not None

    health.record_success()
    assert health.should_skip_run() is None

    for _ in range(health.FAILURE_THRESHOLD):
        health.record_failure(config, "boom")
    assert len(calls) == 2
