from datetime import datetime

import requests
from django.db import connection
from django.shortcuts import render

from projektrouska.updatecheck import UpdateCheck
from projektrouska.functions import (
    return_as_dict,
    return_as_array,
    calcmd5,
    format_num,
    display_by_cath,
)
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
    update_controller.run()

    up_to_date = update_controller.up_to_date
    to_be_modified = update_controller.to_be_modified
    to_be_removed = update_controller.to_be_removed
    to_be_changed_link = update_controller.to_be_changed_link
    to_be_reviewed = update_controller.to_be_reviewed
    to_be_added = update_controller.to_be_added

    missing = to_be_modified + to_be_changed_link + to_be_reviewed + to_be_added

    total = len(update_controller.all)
    total_changes = len(missing)

    try:
        up_to_date_percents = int(100 - (total_changes / total / 100))
    except Exception:
        up_to_date_percents = 100

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
        missing_count=len(to_be_added + to_be_reviewed),
        missing_json=to_be_added + to_be_reviewed,
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
            "pridat": to_be_reviewed,
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

    return render(request, "sites/wip_template.html")
    """
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
    """
    return render(request, "sites/wip_template.html")


# /celostatni-opatreni
def opatreni_celoplosne(request):
    # t = opatreni_stat()
    return render(request, "sites/wip_template.html")
    """return render(
        request,
        "sites/celostatni_opatreni.html",
        {
            "query_results": t,
            "last_check": last_check(),
            "last_modified": last_modified_date(),
        },
    )
    """


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
    except Exception:
        print("MZCR API inforkarta: Něco se pokazilo")

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

    infokarta = {
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
        "posledni_update_dat": datetime.datetime.fromisoformat(
            r.json()["modified"]).strftime("%d.%m.%Y %H:%M"),

    }

    return render(
        request,
        "sites/home.html",
        {
            "infokarta": infokarta,
            "last_check": last_check(),
            "last_modified": last_modified_date(),
        },
    )


# admin/kontrola-zadaneho/
def kontrola_zadaneho(request):
    args = request.GET.copy()
    try:
        id_opatreni = int(args.get("id_opatreni", 100))
    except ValueError:
        id_opatreni = 100

    return render(request, "sites/wip_template.html")


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
