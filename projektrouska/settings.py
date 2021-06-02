from projektrouska.base_settings import *
import socket

BETA = True

if "DEV" in locals() and DEV is True:
    from projektrouska.local_settings import *
else:
    DEV = False
    from projektrouska.production_settings import *
