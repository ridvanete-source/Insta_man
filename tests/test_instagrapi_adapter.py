"""Verifies the challenge/2FA login wiring using a fake instagrapi Client -
no real network access, no real credentials involved."""

from pathlib import Path

import instagrapi
import pytest
from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired

from insta_man.config import Config
from insta_man.publishers.instagrapi_adapter import InstagrapiPublisher


def make_config(tmp_path: Path) -> Config:
    return Config(
        publisher="instagrapi",
        ig_username="tester",
        ig_password="secret",
        ig_session_file=tmp_path / "session.json",
    )


class FakeClientBase:
    """Minimal stand-in for instagrapi.Client's login-relevant surface."""

    def __init__(self) -> None:
        self.challenge_code_handler = None
        self.login_calls: list[dict] = []
        self.last_json: dict = {}
        self.dumped_to: Path | None = None

    def load_settings(self, path):
        pass

    def dump_settings(self, path):
        self.dumped_to = path

    def login(self, username, password, verification_code=""):
        self.login_calls.append({"username": username, "password": password, "verification_code": verification_code})


def test_authenticate_success_no_prompt(tmp_path, monkeypatch):
    class FakeClient(FakeClientBase):
        pass

    monkeypatch.setattr(instagrapi, "Client", FakeClient)
    monkeypatch.setattr("builtins.input", lambda *_: pytest.fail("should not prompt on a clean login"))

    publisher = InstagrapiPublisher(make_config(tmp_path))
    publisher.authenticate()

    assert publisher._client.login_calls == [
        {"username": "tester", "password": "secret", "verification_code": ""}
    ]
    assert publisher._client.dumped_to == make_config(tmp_path).ig_session_file


def test_authenticate_retries_with_2fa_code(tmp_path, monkeypatch):
    class FakeClient(FakeClientBase):
        def login(self, username, password, verification_code=""):
            self.login_calls.append(
                {"username": username, "password": password, "verification_code": verification_code}
            )
            if not verification_code:
                raise TwoFactorRequired("2FA required")

    monkeypatch.setattr(instagrapi, "Client", FakeClient)
    monkeypatch.setattr("builtins.input", lambda *_: "123456")

    publisher = InstagrapiPublisher(make_config(tmp_path))
    publisher.authenticate()

    assert [c["verification_code"] for c in publisher._client.login_calls] == ["", "123456"]


def test_authenticate_falls_back_to_challenge_resolve(tmp_path, monkeypatch):
    resolved = []

    class FakeClient(FakeClientBase):
        def login(self, username, password, verification_code=""):
            raise ChallengeRequired("challenge required")

        def challenge_resolve(self, last_json):
            resolved.append(last_json)

    monkeypatch.setattr(instagrapi, "Client", FakeClient)

    publisher = InstagrapiPublisher(make_config(tmp_path))
    publisher.authenticate()

    assert len(resolved) == 1


def test_authenticate_raises_clear_error_when_non_interactive(tmp_path, monkeypatch):
    class FakeClient(FakeClientBase):
        def login(self, username, password, verification_code=""):
            raise TwoFactorRequired("2FA required")

    monkeypatch.setattr(instagrapi, "Client", FakeClient)

    def no_stdin(*_):
        raise EOFError()

    monkeypatch.setattr("builtins.input", no_stdin)

    publisher = InstagrapiPublisher(make_config(tmp_path))
    with pytest.raises(RuntimeError, match="etkilesimli degil"):
        publisher.authenticate()


def test_authenticate_requires_credentials(tmp_path):
    config = Config(publisher="instagrapi", ig_username=None, ig_password=None)
    publisher = InstagrapiPublisher(config)

    with pytest.raises(RuntimeError, match="IG_USERNAME"):
        publisher.authenticate()
