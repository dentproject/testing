"""__init.py__

Module init for testbed.discovery
"""

REPORTS_DIR = "/var/lib/testbed/discovery"

REPORTS_SAVE_MIN = 3
# save at least three of each report

REPORTS_SAVE_MAX = 10
##import sys
##REPORTS_SAVE_MAX = sys.maxsize
# save at most 10 of each report

REPORTS_HORIZON = 30 * 24 * 3600
# same a month of reports
