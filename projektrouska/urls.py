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

from django.conf.urls.static import static

from projektrouska.aktualnost import main2
from django.db import connection

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('o-projektu/', views.about, name='about'),
    path('FAQ/', views.faq, name='FAQ'),

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

@tl.job(interval=timedelta(seconds=240))
def sample_job_every_240s():
    print("running update")
    res = main2.main()
    aktualni = res["aktualni"]
    smazali_je = res['smazali']
    zmena_odkazu = res['zmena']
    chybi = res['chybi']
    celkem = len(aktualni) + len(smazali_je) + len(zmena_odkazu) + len(chybi)
    procenta = int(100 - ((len(chybi) + len(smazali_je) + len(zmena_odkazu)) / (celkem / 100)))

    if (len(chybi) > 0 or len(zmena_odkazu) > 0 or len(smazali_je) > 0):
        stat = "Data jsou z {}% kompletní a aktuální. \nCelkem máme v databázi {} opatření, {} je třeba odstranit, u {} došlo ke změně odkazu a {} chybí a je třeba přidat. ".format(
            procenta,
            celkem,
            len(smazali_je),
            len(zmena_odkazu),
            len(chybi))
        print("ALERT ne všechny data jsou aktuální")
    elif (celkem == 0):
        stat = "Aktuálnost jsme nebyli schopni ověřit. Může to být způsobeno neustálými změnami na webu ministerstva zdravotnictví. Pokusíme se pro to udělat co nejvíce. "
        print("ALERT neaktuální data")
    elif (len(smazali_je) == 0 and len(zmena_odkazu) == 0 and len(chybi) == 0):
        stat = "Všechna data jsou aktuální!"

    # m = md5("./projektrouska/aktualnost/v_databazi.txt")
    with connection.cursor() as cursor:
        # query_results = cursor.fetchall()
        # desc = cursor.description

        cursor.execute('''insert into INFO (checksum, date_updated, poznamka, AKTUALNOST) values   (
                  null,
                  trunc(sysdate, 'Mi'), 
                  :pozn, 
                  :akt)''',
                       {"pozn": stat, "akt": procenta})
tl.start(block=False)