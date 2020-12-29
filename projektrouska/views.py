# import json
from datetime import datetime, timedelta

import requests
from django.db import connection
from django.shortcuts import render

from projektrouska.aktualnost.kontrola import Update_check
# from projektrouska.functions import *
from projektrouska.functions import (
    return_as_dict,
    return_as_array,
    calcmd5,
    format_num,
    # strfdelta,
    display_by_cath,
)
from projektrouska.models import UpdateLogs, State
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

update_controller = Update_check()

# /aktualnost/
# TODO: Work in progress
def aktualnost(request):
    info_last = {}
    dict2 = {}
    global update_controller

    last_check = UpdateLogs.objects.latest('date_updated').date_updated

    if (datetime.now() - last_check.date_updated) < timedelta(minutes=2):
        print("Aktualnost kontrolovana pred mene nez 2 minutami")
        if (update_controller.db_localcopy == None):
            update_controller.run()
    else:
        update_controller.run()

    aktualni = update_controller.up_to_date
    smazali_je = update_controller.to_be_removed
    zmena_odkazu = update_controller.to_be_changed_link
    chybi = update_controller.to_be_added + update_controller.to_be_modified + update_controller.to_be_reviewed

    celkem = len(update_controller.all)
    celkem_upravit = int(len(chybi) + len(smazali_je) + len(zmena_odkazu))
    try:
        procenta = int(100 - (celkem_upravit / (celkem / 100)))
    except Exception:
        procenta = 100
    if DEV:
        try:
            print("SMAZALI")
            for i in smazali_je:
                print(
                    "SMAZALI ID={}, nazev {}".format(
                        i["ID_OPATRENI"], i["NAZEV_OPATRENI"]
                    )
                )

            print("Zmena odkazu")
            for i in zmena_odkazu:
                print(
                    "ZMENA ID={}, nazev {}\nStary {}\nNovy: {}".format(
                        i["ID_OPATRENI"],
                        i["NAZEV_OPATRENI"],
                        i["STARY_ODKAZ"],
                        i["ZDROJ"],
                    )
                )
            print("CHYBI")
            for i in chybi:
                print("CHYBI ID {} nazev {} \nodkaz: {}".format(i["ID_OPATRENI"], i["NAZEV_OPATRENI"], i["ZDROJ"]))

        except Exception:
            print(
                "Nezkontroloval jsem spravne parametry vypisu a uz se mi to nechce opravovat"
            )

    if len(chybi) > 0 or len(zmena_odkazu) > 0 or len(smazali_je) > 0:
        stat = "Data jsou z {}% kompletní a aktuální. \nCelkem máme v databázi {} záznamů, {} je třeba odstranit, u {} došlo ke změně odkazu a {} chybí a je třeba přidat. ".format(
            procenta, celkem,
            len(smazali_je),
            len(zmena_odkazu),
            len(chybi),
        )
        print("ALERT ne všechny data jsou aktuální")
    elif celkem == 0:
        stat = "Aktuálnost jsme nebyli schopni ověřit. Může to být způsobeno neustálými změnami na webu ministerstva zdravotnictví. Pokusíme se pro to udělat co nejvíce. "
        print("ALERT neaktuální data")
    elif len(smazali_je) == 0 and len(zmena_odkazu) == 0 and len(chybi) == 0:
        stat = "Všechna data jsou aktuální!"

    str_for_checksum = (
            "" + str(aktualni) + str(smazali_je) + str(zmena_odkazu) + str(chybi) + stat
    )

    # m = md5("./projektrouska/aktualnost/v_databazi.txt")
    with connection.cursor() as cursor:
        # query_results = cursor.fetchall()
        # desc = cursor.description

        # todo: migrate to ORM
        cursor.execute(
            """insert into INFO (checksum,  date_updated, poznamka, 
            AKTUALNOST, CHYBI_POCET, CHYBI_POLE, ZMENA_LINK_POCET, 
            ZMENA_LINK_POLE, ODSTRANIT_POCET, ODSTRANIT_POLE , CELK_ZMEN) values   (
            :checksum,
            trunc(sysdate, 'MI'), 
            :pozn, 
            :akt, 
            :chybi_pocet, 
            :chybi_pole, 
            :zmena_link_pocet,
            :zmena_link_pole, 
            :odstranit_pocet, 
            :odstranit_pole, 
            :celk_zmen)
            """,
            {
                "pozn": stat,
                "checksum": calcmd5(str_for_checksum),
                "akt": procenta,
                "chybi_pocet": len(chybi),
                "chybi_pole": c,
                "zmena_link_pocet": len(zmena_odkazu),
                "zmena_link_pole": z,
                "odstranit_pocet": len(smazali_je),
                "odstranit_pole": s,
                "celk_zmen": int(celkem_upravit),
            },
        )

    return render(
        request,
        "sites/aktualnost.html",
        {
            "procenta": procenta,
            "pridat": chybi,
            "celkem": celkem,
            "ubrat": smazali_je,
            "stejne": aktualni,
            "zmena": zmena_odkazu,
            "statistika": stat,
            "cas": datetime.now(),
            "celk_mame": celkem,
            "last_check": last_check(),
            "last_modified": last_modified_date(),
        },
    )


# /opatreni/
def opatreni(request):
    # todo: change paths to something like /precaution/city/123 instead of /opatreni/?obecmesto_id=123
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

    if (
            id_obecmesto == "" and nuts3_id == "" and kraj_id == "" and okres_id == ""
    ):  # stat
        kraj_id = str(1)
        res = opatreni_stat()

    if (
            id_obecmesto == "" and nuts3_id == "" and kraj_id != "" and okres_id == ""
    ):  # kraj
        res = opatreni_kraj(kraj_id)

    elif (
            (nuts3_id != "") and (id_obecmesto == "") and (kraj_id == "") and okres_id == ""
    ):  # nuts
        res = opatreni_nuts(nuts3_id)

    elif id_obecmesto == "" and nuts3_id == "" and okres_id != "" and kraj_id == "":
        res = opatreni_okres(okres_id)

    elif id_obecmesto != "" and nuts3_id == "" and kraj_id == "":  # obecmesto
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
            "now": datetime.now(),
            "last_check": last_check(),
            "last_modified": last_modified_date(),
        },
    )


# /celostatni-opatreni
def opatreni_celoplosne(request):
    array = State.objects.all()[0].precaution_set.all()
    array = opatreni_stat()

    # oder by cathegory
    """by_cath = []
    existing = []
    for col in array:
        if ("NAZEV_KAT" in col):  # fajn, ted zkontroluju, jestli uz jsem to vypsal, nebo ne
            if (col["NAZEV_KAT"] in existing):
                by_cath[len(by_cath) - 1]["narizeni"].append(col)
            else:
                existing.append(col["NAZEV_KAT"])
                tmp = {"kategorie": col["NAZEV_KAT"], "narizeni": [col]}
                by_cath.append(tmp)
    """

    return render(
        request,
        "sites/celostatni_opatreni.html",
        {
            "query_results": array,
            "posledni_databaze": last_modified_date(),
            "now": datetime.now(),
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
            url="https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/zakladni-prehled.json"
        )
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
                            )  join OP_STAT using (ID_OPATRENI);""",
            {"id_op": id_opatreni},
        )
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
                            ) join OBECMESTO on OBECMESTO_ID_OBECMESTO=ID_OBECMESTO order by ID_OBECMESTO;""",
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
        polozky_opatreni = return_as_array(cursor.fetchall(), cursor.description)

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
