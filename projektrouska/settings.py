from projektrouska.base_settings import *
import socket

cx_Oracle.init_oracle_client(lib_dir=r'/home/tomas-dostal/instantclient_19_8/')
BETA = True

if(socket.gethostname() == "inspiron-13-5368"):
    from projektrouska.local_settings import *
    DEV = True
else:
    from projektrouska.production_settings import *
    DEV = False