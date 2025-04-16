from pathlib import Path


def tirex_tracker_mounts_or_none():
    tracker = find_tirex_tracker_executable_or_none()
    if tracker:
        return {str(tracker): {"bind": "/tracked", "mode": "ro"}}


def find_tirex_tracker_executable_or_none():
    # wget https://github.com/tira-io/tirex-tracker/releases/download/0.2.5/measure-0.2.5-linux -O 'tirex-tracker-0.2.5-linux'
    # chmod +x tirex-tracker-0.2.5-linux
    ret = Path(__file__).parent / "tirex-tracker-0.2.5-linux"
    ret = ret.resolve().absolute()

    return ret if ret.exists() else None
