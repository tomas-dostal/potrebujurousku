"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from projektrouska import views
from django.urls import path
from django.conf import settings
import requests

from django.conf.urls.static import static
from django.contrib import admin

from projektrouska.aktualnost import main2
from django.db import connection

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('o-projektu/', views.about, name='about'),
    #path('FAQ/', views.faq, name='FAQ'),

    path('opatreni/', views.opatreni, name='opatreni'),
    path('aktualnost/', views.aktualnost, name='aktualnost'),
    path("robots.txt", views.robots_txt),

                  #path('statistiky/', views.stats, name='statistiky'),
    path('api/search', views.najdi_mesto, name='najdi_mesto'),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# Please forgive me. I did not wanted to do it this way...
import time
from timeloop import Timeloop
from datetime import timedelta

tl = Timeloop()
@tl.job(interval=timedelta(seconds=300))
def sample_job_every_240s():
    page = requests.get("https://potrebujurousku.cz/aktualnost/")
    print("Update")
tl.start(block=False)