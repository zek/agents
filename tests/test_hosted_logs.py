from __future__ import annotations

from pathlib import Path

import pytest

from livekit.agents.telemetry.hosted_logs import (
    HOSTED_LOGS_ENV,
    HOSTED_LOGS_HANDOFF_FILE_ENV,
    HOSTED_LOGS_SIDECAR,
    hand_off_logs_to_sidecar,
    logs_handled_by_sidecar,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def handoff_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    path = tmp_path / "sdk-handoff"
    monkeypatch.setenv(HOSTED_LOGS_ENV, HOSTED_LOGS_SIDECAR)
    monkeypatch.setenv(HOSTED_LOGS_HANDOFF_FILE_ENV, str(path))
    return path


def test_hand_off_creates_the_file(handoff_file: Path) -> None:
    assert not logs_handled_by_sidecar()
    hand_off_logs_to_sidecar()
    assert handoff_file.exists()
    assert logs_handled_by_sidecar()


def test_hand_off_keeps_an_existing_file(handoff_file: Path) -> None:
    handoff_file.write_text("x")
    hand_off_logs_to_sidecar()
    assert handoff_file.read_text() == "x"
    assert logs_handled_by_sidecar()


def test_no_hand_off_without_sidecar_mode(
    handoff_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(HOSTED_LOGS_ENV, "something-else")
    hand_off_logs_to_sidecar()
    assert not handoff_file.exists()
    assert not logs_handled_by_sidecar()


def test_no_hand_off_without_a_file_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(HOSTED_LOGS_ENV, HOSTED_LOGS_SIDECAR)
    monkeypatch.delenv(HOSTED_LOGS_HANDOFF_FILE_ENV, raising=False)
    hand_off_logs_to_sidecar()
    assert not logs_handled_by_sidecar()


def test_sdk_keeps_exporting_when_the_file_cannot_be_created(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(HOSTED_LOGS_ENV, HOSTED_LOGS_SIDECAR)
    monkeypatch.setenv(HOSTED_LOGS_HANDOFF_FILE_ENV, str(tmp_path / "missing-dir" / "sdk-handoff"))
    hand_off_logs_to_sidecar()
    assert not logs_handled_by_sidecar()


def test_startup_hand_off_creates_the_file(handoff_file: Path) -> None:
    from livekit import _agents_hosted_logs

    _agents_hosted_logs.hand_off()
    assert handoff_file.exists()


def test_startup_hand_off_is_silent_when_the_file_cannot_be_created(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from livekit import _agents_hosted_logs

    monkeypatch.setenv(HOSTED_LOGS_ENV, HOSTED_LOGS_SIDECAR)
    monkeypatch.setenv(HOSTED_LOGS_HANDOFF_FILE_ENV, str(tmp_path / "missing-dir" / "sdk-handoff"))
    _agents_hosted_logs.hand_off()
    assert capsys.readouterr() == ("", "")


def test_startup_files_call_the_hand_off(handoff_file: Path) -> None:
    import importlib

    root = Path(__file__).parent.parent / "livekit-agents"
    pth = (root / "livekit_agents_hosted_logs.pth").read_text().strip()
    start = (root / "livekit_agents_hosted_logs.start").read_text().strip()

    exec(pth)
    assert handoff_file.exists()

    handoff_file.unlink()
    module, _, attr = start.partition(":")
    getattr(importlib.import_module(module), attr)()
    assert handoff_file.exists()
