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

from projektrouska.api.search import find_place_by_name
from projektrouska.api.update_stats import get_update_stats
from projektrouska.api.update_stats import get_all_update_stats

from projektrouska.api.celostatni_opatreni import celostatni_opatreni
from projektrouska.settings import BETA, DEV

# Please forgive me. I did not wanted to do it this way...
# import time
from timeloop import Timeloop
from datetime import timedelta


from projektrouska.views import kontrola_zadaneho, graphs

from projektrouska.view.errors import (
    custom_error_view,
    custom_page_not_found_view,
    custom_permission_denied_view,
    custom_bad_request_view,
)

urlpatterns = [
    # path('admin/', admin.site.urls),
    path("", views.opatreni_celoplosne, name="home"),
    path("home/", views.home, name="home"),
    path("o-projektu/", views.about, name="about"),
    path("FAQ/", views.about, name="about"),
    path("opatreni/", views.opatreni, name="opatreni"),
    path("celostatni-opatreni/", views.opatreni_celoplosne, name="celostatni-opatreni"),
    path("aktualnost/", views.aktualnost, name="aktualnost"),
    # path('statistiky/', views.stats, name='statistiky'),
    path("api/search", find_place_by_name, name="najdi_mesto"),
    path("api/update_stats", get_update_stats, name="update_stats"),
    path("api/all_update_stats", get_all_update_stats, name="update_stats"),
    path("api/celostatni_opatreni", celostatni_opatreni, name="celostatni_opatreni"),

     path("admin/kontrola-zadaneho/", kontrola_zadaneho, name="admin_kontrola_zadaneho"),
     path("admin/grafiky/", graphs, name="admin_kontrola_zadaneho"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = custom_page_not_found_view
handler500 = custom_error_view
handler403 = custom_permission_denied_view
handler400 = custom_bad_request_view


tl = Timeloop()

@tl.job(interval=timedelta(seconds=300))
def sample_job_every_300s():
    if not BETA and not DEV:
        requests.get("https://potrebujurousku.cz/aktualnost/")


tl.start(block=False)
