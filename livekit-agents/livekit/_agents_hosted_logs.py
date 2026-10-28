import os


def hand_off() -> None:
    if os.environ.get("LIVEKIT_HOSTED_LOGS") != "sidecar":
        return
    path = os.environ.get("LIVEKIT_HOSTED_LOGS_HANDOFF_FILE")
    if not path:
        return
    try:
        with open(path, "a"):
            pass
    except OSError:
        pass
