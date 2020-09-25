from projektrouska.base_settings import *
import socket

BETA = True

if(socket.gethostname() == "inspiron-13-5368"):
    from projektrouska.local_settings import *
    DEV = True
else:
    from projektrouska.production_settings import *
    DEV = False