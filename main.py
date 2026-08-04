import argparse
import signal
import sys
import time
from pathlib import Path

from recorder import Recorder


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Screen & Input Recorder — collect multimodal data for ML training"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Root data directory (default: data)",
    )
    parser.add_argument(
        "--tick-interval",
        type=float,
        default=1.0,
        help="Seconds between screenshots (default: 1.0)",
    )
    args = parser.parse_args()

    recorder = Recorder(data_dir=args.data_dir, tick_interval=args.tick_interval)
    session_dir = recorder.start()

    print(f"Recording started. Session: {session_dir}")
    print("Press Ctrl+C to stop.")

    def shutdown(signum, frame):
        print("\nStopping recorder...")
        recorder.stop()
        print("Done.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()
