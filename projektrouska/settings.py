from projektrouska.base_settings import *
import socket

if(socket.gethostname() == "inspiron-13-5368"):
    from projektrouska.local_settings import *
else:
    from projektrouska.production_settings import *

print(SECURE_SSL_REDIRECT)