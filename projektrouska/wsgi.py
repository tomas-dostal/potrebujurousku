"""
WSGI config for projektrouska project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""
import sys
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projektrouska.settings')
sys.path.append('/home/django/oracle/instantclient_10_2')

application = get_wsgi_application()
