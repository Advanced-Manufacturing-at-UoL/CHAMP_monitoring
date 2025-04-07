from utils.monitoring.process_monitor import ProcessMonitor
from utils.interfaces import load_config

# Usage example (to be placed in main.py):
def main():
    config = load_config('config.yaml')
    monitor = ProcessMonitor(config)
    # monitor.setup()
    try:
        print("the monitor is running")
        monitor.run()
    finally:
        monitor.cleanup()

if __name__ == "__main__":
    main()