"""Debug logging for glue-jupyter selection troubleshooting."""

import traceback
from datetime import datetime

# Global debug log
_debug_log = []


def log(message, **kwargs):
    """Add a debug entry with timestamp and optional data."""
    entry = {
        'time': datetime.now().isoformat(),
        'message': message,
        **kwargs
    }
    _debug_log.append(entry)
    # Also print for immediate feedback
    print(f"[DEBUG] {message}", kwargs if kwargs else "")


def log_exception(message):
    """Log an exception with full traceback."""
    entry = {
        'time': datetime.now().isoformat(),
        'message': message,
        'traceback': traceback.format_exc()
    }
    _debug_log.append(entry)
    print(f"[DEBUG ERROR] {message}")
    print(traceback.format_exc())


def get_log():
    """Return the debug log."""
    return _debug_log


def clear_log():
    """Clear the debug log."""
    _debug_log.clear()


def print_log():
    """Print all log entries."""
    for entry in _debug_log:
        print(f"[{entry['time']}] {entry['message']}")
        for k, v in entry.items():
            if k not in ('time', 'message'):
                print(f"  {k}: {v}")
