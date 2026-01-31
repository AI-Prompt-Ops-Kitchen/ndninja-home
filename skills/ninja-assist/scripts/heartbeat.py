#!/usr/bin/env python3
"""
Check for heartbeat triggers.
Returns alerts if something needs attention, or "Nothing to report".
"""

import sys

# Add ninja-assist src to path
sys.path.insert(0, "/home/ndninja/clawd/projects/ninja-assist")

from src.auto_triggers import check_heartbeat


def main():
    result = check_heartbeat()
    
    if result:
        print(result)
    else:
        print("Nothing to report.")


if __name__ == "__main__":
    main()
