from datetime import datetime, timedelta

import requests
from django.db import connection
from django.shortcuts import render

from projektrouska.aktualnost.updatecheck import UpdateCheck
from projektrouska.functions import (
    return_as_dict,
    return_as_array,
    calcmd5,
    format_num,
    display_by_cath,
)
from projektrouska.models import UpdateLogs
from projektrouska.settings import DEV
from projektrouska.sqls import (
    last_check,
    last_modified_date,
    opatreni_stat,
    opatreni_kraj,
    opatreni_nuts,
    opatreni_okres,
    opatreni_om,
)
from projektrouska.models import *

import pytz

from django.views.generic import ListView
from projektrouska.models import City, State, Region, District, Nuts4

import json

update_controller = UpdateCheck()

"""
class SearchView(ListView):

    paginate_by = 20
    count = 0
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['count'] = self.count or 0
        context['count'] = self.request.GET.get('q')

        states = State.objects.filter(name__istartswith=query_string)
        regions = Region.objects.filter(name__istartswith=query_string)
        districts = District.objects.filter(name__istartswith=query_string)
        nuts4 = Nuts4.objects.filter(name__istartswith=query_string)
        cities = City.objects.filter(name__istartswith=query_string)

"""


# /aktualnost/
# TODO: Work in progress
def aktualnost(request):
    global update_controller
    last_db_check = UpdateLogs.objects.latest('date_updated').date_updated

    now = datetime.datetime.now().replace(tzinfo=pytz.UTC)
    if (now - last_db_check) < timedelta(minutes=2):
        print("Aktualnost kontrolovana pred mene nez 2 minutami")
    else:
        update_controller.run()

    up_to_date = update_controller.up_to_date
    to_be_modified = update_controller.to_be_modified
    to_be_removed = update_controller.to_be_removed
    to_be_changed_link = update_controller.to_be_changed_link
    to_be_reviewed = update_controller.to_be_reviewed
    to_be_added = update_controller.to_be_added

    missing = up_to_date + to_be_modified + to_be_changed_link + to_be_reviewed

    total = len(update_controller.all)
    total_changes = len(missing)

    try:
        up_to_date_percents = int(100 - (total_changes / total / 100))
    except Exception:
        up_to_date_percents = 100
    if DEV:
        try:
            print("SMAZALI")
            for i in to_be_removed:
                print(
                    "SMAZALI ID={}, nazev {}".format(
                        i["ID_OPATRENI"], i["NAZEV_OPATRENI"]
                    )
                )

            print("Zmena odkazu")
            for i in to_be_changed_link:
                print(
                    "ZMENA ID={}, nazev {}\nStary {}\nNovy: {}".format(
                        i["ID_OPATRENI"],
                        i["NAZEV_OPATRENI"],
                        i["STARY_ODKAZ"],
                        i["ZDROJ"],
                    )
                )
            print("CHYBI")
            for i in to_be_added:
                print(
                    "CHYBI ID {} nazev {} \nodkaz: {}".format(
                        i["ID_OPATRENI"],
                        i["NAZEV_OPATRENI"],
                        i["ZDROJ"]))

        except Exception:
            pass

    if len(missing) != 0:
        stat = "Data jsou z {}% kompletní a aktuální. \n"
    elif total == 0:
        stat = "Aktuálnost jsme nebyli schopni ověřit"
        print("ALERT neaktuální data")

    elif len(missing) == 0:
        stat = "Všechna data jsou aktuální!"

    str_for_checksum = (
            "" +
            str(up_to_date) +
            str(to_be_modified) +
            str(to_be_removed) +
            str(to_be_changed_link) +
            str(to_be_reviewed) +
            str(to_be_added))

    UpdateLogs(
        checksum=calcmd5(str_for_checksum),
        date_updated=datetime.datetime.now().replace(tzinfo=pytz.utc),
        comment=stat,
        up_to_date_percents=up_to_date_percents,
        missing_count=len(to_be_added),
        missing_json=to_be_added,
        change_link_count=len(to_be_changed_link),
        change_link_json=to_be_changed_link,
        outdated_count=len(to_be_removed),
        outdated_json=to_be_removed,
        total_changes=total_changes
    ).save()

    return render(
        request,
        "sites/aktualnost.html",
        {
            "procenta": up_to_date_percents,
            "pridat": to_be_added,
            "celkem": total,
            "ubrat": to_be_removed,
            "stejne": up_to_date,
            "zmena": to_be_changed_link,
            "statistika": stat,
            "celk_mame": total_changes,
            "last_check": last_check(),
            "last_modified": last_modified_date(),
        },
    )


# /opatreni/
def opatreni(request):
    # todo: paths to /precaution/city/5 inestead of /opatreni/?obecmesto_id=5
    # ?obecmesto_id=replace"
    # "?nuts3_id=replace"'.
    # "?kraj_id=replace"'
    args = request.GET.copy()
    id_obecmesto = args.get("obecmesto_id", "")
    nuts3_id = args.get("nuts3_id", "")
    okres_id = args.get("okres_id", "")
    kraj_id = args.get("kraj_id", "")
    # flag = "nic"

    # array = None
    location = None
    res = None

    # stat
    if id_obecmesto == "" and nuts3_id == "" and kraj_id == "" and okres_id == "":
        kraj_id = str(1)
        res = opatreni_stat()

    # kraj
    if id_obecmesto == "" and nuts3_id == "" and kraj_id != "" and okres_id == "":
        res = opatreni_kraj(kraj_id)
    # nuts
    elif nuts3_id != "" and id_obecmesto == "" and kraj_id == "" and okres_id == "":
        res = opatreni_nuts(nuts3_id)
    # okres
    elif id_obecmesto == "" and nuts3_id == "" and okres_id != "" and kraj_id == "":
        res = opatreni_okres(okres_id)

    # obecmesto
    elif id_obecmesto != "" and nuts3_id == "" and kraj_id == "":
        res = opatreni_om(id_obecmesto)

    by_cath = res[0]
    location = res[1]
    return render(
        request,
        "sites/opatreni.html",
        {
            "query_results": by_cath,
            "location": location,
            "posledni_databaze": last_modified_date(),
            "last_check": last_check(),
            "last_modified": last_modified_date(),
        },
    )


# /celostatni-opatreni
def opatreni_celoplosne(request):
    t = opatreni_stat()
    return render(
        request,
        "sites/celostatni_opatreni_Test.html",
        {
            "query_results": t,
            "last_check": last_check(),
            "last_modified": last_modified_date(),
        },
    )


# /o-projektu/
def about(request):
    return render(
        request,
        "sites/o_projektu.html",
        {
            "last_check": last_check(),
            "last_modified": last_modified_date()
        },
    )


# /
def home(request):
    try:
        r = requests.get(
            url="https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/zakladni-prehled.json")
        result = r.json()["data"]

        result = result[0]
        data_modified = datetime.fromisoformat(r.json()["modified"])
    except Exception:
        print("MZDR API inforkarta: Něco se pokazilo")

    """
        "datum": "2020-09-23",
        "provedene_testy_celkem": 1240417,
        "potvrzene_pripady_celkem": 54244,
        "aktivni_pripady": 26984,
        "vyleceni": 26709,
        "umrti": 551,
        "aktualne_hospitalizovani": 628,
        "provedene_testy_vcerejsi_den": 21403,
        "potvrzene_pripady_vcerejsi_den": 2392,
        "potvrzene_pripady_dnesni_den": 1091

    """
    vcera = int(result["potvrzene_pripady_vcerejsi_den"])
    testu_vcera = int(result["provedene_testy_vcerejsi_den"])
    pozitivnich = round(vcera / (testu_vcera / 100), 2)

    return render(
        request,
        "sites/home.html",
        {
            "kontrola": last_check(),
            "datum": result["datum"],
            "provedene_testy_celkem": format_num(result["provedene_testy_celkem"]),
            "potvrzene_pripady_celkem": format_num(result["potvrzene_pripady_celkem"]),
            "aktivni_pripady": format_num(result["aktivni_pripady"]),
            "vyleceni": format_num(result["vyleceni"]),
            "umrti": format_num(result["umrti"]),
            "aktualne_hospitalizovani": format_num(result["aktualne_hospitalizovani"]),
            "provedene_testy_vcerejsi_den": format_num(
                result["provedene_testy_vcerejsi_den"]
            ),
            "pozitivnich_procenta_vcera": pozitivnich,
            "potvrzene_pripady_vcerejsi_den": format_num(
                result["potvrzene_pripady_vcerejsi_den"]
            ),
            "potvrzene_pripady_dnesni_den": format_num(
                result["potvrzene_pripady_dnesni_den"]
            ),
            "posledni_update_dat": data_modified.strftime("%d.%m.%Y %H:%M"),
            "last_check": last_check(),
            "last_modified": last_modified_date(),
        },
    )


# /statistiky - INACTIVE
# def stats(request):
#     return render(request, "sites/statistiky.html")

# admin/kontrola-zadaneho/
def kontrola_zadaneho(request):
    args = request.GET.copy()
    try:
        id_opatreni = int(args.get("id_opatreni", 100))
    except ValueError:
        id_opatreni = 100

    pocet_prirazenych_mist = 0
    with connection.cursor() as cursor:

        cursor.execute(
            """select distinct ID_OPATRENI, 1 as ID_STAT, 'Česká Republika' as NAZEV_STAT  from(
                            select * from OPATRENI where ID_OPATRENI = :id_op
                            )  join OP_STAT using (ID_OPATRENI);""", {
                "id_op": id_opatreni}, )
        platnost_cr = return_as_array(cursor.fetchall(), cursor.description)
        pocet_prirazenych_mist += len(platnost_cr)

        cursor.execute(
            """ select distinct ID_OPATRENI, ID_KRAJ, NAZEV_KRAJ from (
                              select * from(
                                select * from OPATRENI where ID_OPATRENI = :id_op
                                )  join OP_KRAJ on OPATRENI_ID_OPATRENI = ID_OPATRENI
                            ) join KRAJ on KRAJ_ID_KRAJ=ID_KRAJ order by ID_KRAJ;""",
            {"id_op": id_opatreni},
        )

        platnost_kraj = return_as_array(cursor.fetchall(), cursor.description)
        pocet_prirazenych_mist += len(platnost_kraj)

        cursor.execute(
            """select distinct ID_OPATRENI, ID_OKRES, NAZEV_OKRES  from (
                              select * from(
                                select * from OPATRENI where ID_OPATRENI  = :id_op
                                )  join OP_OKRES on OPATRENI_ID_OPATRENI = ID_OPATRENI
                            ) join OKRES on OKRES_ID_OKRES=ID_OKRES order by ID_OKRES;""",
            {"id_op": id_opatreni},
        )

        platnost_okres = return_as_array(cursor.fetchall(), cursor.description)
        pocet_prirazenych_mist += len(platnost_okres)

        cursor.execute(
            """  select distinct ID_OPATRENI, ID_NUTS, NAZEV_NUTS  from (
                              select * from(
                                select * from OPATRENI where ID_OPATRENI = :id_op
                                )  join OP_NUTS on OPATRENI_ID_OPATRENI = ID_OPATRENI
                            ) join NUTS3 on NUTS3_ID_NUTS=ID_NUTS order by ID_NUTS;""",
            {"id_op": id_opatreni},
        )
        platnost_nuts = return_as_array(cursor.fetchall(), cursor.description)
        pocet_prirazenych_mist += len(platnost_nuts)

        cursor.execute(
            """  select distinct ID_OPATRENI, ID_OBECMESTO, NAZEV_OBECMESTO  from (
                              select * from(
                                select * from OPATRENI where ID_OPATRENI =  :id_op
                                )  join OP_OM on OPATRENI_ID_OPATRENI = ID_OPATRENI
                            ) join OBECMESTO on OBECMESTO_ID_OBECMESTO=ID_OBECMESTO
                            order by ID_OBECMESTO;""",
            {"id_op": id_opatreni},
        )
        platnost_om = return_as_array(cursor.fetchall(), cursor.description)
        pocet_prirazenych_mist += len(platnost_om)

        cursor.execute(
            """select * from(
                                select * from (
                                    select *  from opatreni where  ID_OPATRENI = :id_op
                                ) join POLOZKA on OPATRENI_ID_OPATRENI = ID_OPATRENI
                            ) join KATEGORIE on KATEGORIE_ID_KATEGORIE = ID_KATEGORIE
                        order by ID_KATEGORIE;""",
            {"id_op": id_opatreni},
        )
        polozky_opatreni = return_as_array(
            cursor.fetchall(), cursor.description)

        cursor.execute(
            """select *  from opatreni where  ID_OPATRENI = :id_op;""",
            {"id_op": id_opatreni},
        )
        opatreni = return_as_dict(cursor.fetchone(), cursor.description)

        by_cath = display_by_cath(polozky_opatreni)
        pocet_polozek = len(polozky_opatreni)

        return render(
            request,
            "sites/kontrola_zadavani_par1.html",
            {
                "query_results": by_cath,
                "posledni_databaze": last_modified_date(),
                "now": datetime.now(),
                "last_check": last_check(),
                "last_modified": last_modified_date(),
                "platnost_cr": platnost_cr,
                "platnost_kraj": platnost_kraj,
                "platnost_okres": platnost_okres,
                "platnost_nuts": platnost_nuts,
                "platnost_om": platnost_om,
                "pocet_polozek": pocet_polozek,
                "pocet_prirazenych_mist": pocet_prirazenych_mist,
                "opatreni_info": opatreni,
                "args": args,
            },
        )


def graphs(request):
    return render(
        request,
        "sites/graphs.html",
        {
            "posledni_databaze": last_modified_date(),
            "now": datetime.now(),
            "last_check": last_check(),
            "last_modified": last_modified_date(),
        },
    )
