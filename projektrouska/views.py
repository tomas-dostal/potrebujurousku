import json
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from datetime import datetime, timedelta

# Create your views here.
from django.shortcuts import render
from django.db import connection
from projektrouska.aktualnost import kontrola

import hashlib

from projektrouska.settings import DEV


def calcmd5(string):
    # initializing string
    str2hash = string
    # encoding GeeksforGeeks using encode()
    # then sending to md5()
    result = hashlib.md5(str2hash.encode())

    # printing the equivalent hexadecimal value.
    return (result.hexdigest())

#@require_GET
def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /private/",
        "Disallow: /junk/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def custom_page_not_found_view(request, exception):
    return render(request, "errors/404.html",
                  { "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola()})



def custom_error_view(request, exception=None):
    return render(request, "errors/500.html", { "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola()})

def custom_permission_denied_view(request, exception=None):
    return render(request, "errors/403.html", { "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola()})

def custom_bad_request_view(request, exception=None):
    return render(request, "errors/400.html", { "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola()})


def about(request):
    return render(request, 'o_projektu.html', {"kontrola": posledni_kontrola()})
def faq(request):
    return render(request, 'faq.html', {"kontrola": posledni_kontrola()})

def indikator_aktualnost():
    with connection.cursor() as cursor:
        # query_results = cursor.fetchall()
        # desc = cursor.description

        cursor.execute('''select *
                        from
                        (select * from info order by DATE_UPDATED desc)
                        where
                        ROWNUM <= 1''')

        response = cursor.fetchone()

        desc = cursor.description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
        columns = []
        for col in desc:
            columns.append(col[0])

        dict = {}
        i = 0
        for row in response:
            dict[columns[i]] = row
            i += 1
        if(DEV == True):
            print(dict)

        if((datetime.now() - dict['DATE_UPDATED']) < timedelta(minutes=10)):
            if (DEV == True):
                print("Aktualnost aktualizovana pred mene nez 10 minutami")

#TODO Dokoncit seznam narizeni a polozek
def seznam_opatreni(request):
    
    with connection.cursor() as cursor:


        cursor.execute('''select * from (select * from opatreni ) join polozka on ID_OPATRENI=OPATRENI_ID_OPATRENI join KATEGORIE K on K.ID_KATEGORIE = POLOZKA.KATEGORIE_ID_KATEGORIE order by je_platne desc, PLATNOST_OD desc)''')

        query_results = cursor.fetchall()

        desc = cursor.description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
        ### MAGIC ###
        columns = []
        for col in desc:
            columns.append(col[0])


        a = []

        for line in query_results:
            temp = {}
            for i in range(0, len(line)):
                temp[columns[i]] = line[i]
            a.append(temp)

        location = {}
        i = 0
        # setrizene podle kategorie
        by_cath = []

        existing = []
        for col in a:
            if ("NAZEV_KAT" in col):  # fajn, ted zkontroluju, jestli uz jsem to vypsal, nebo ne
                if (col["NAZEV_KAT"] in existing):
                    by_cath[len(by_cath) - 1]["narizeni"].append(col)
                else:
                    existing.append(col["NAZEV_KAT"])
                    tmp = {"kategorie": col["NAZEV_KAT"], "narizeni": [col]}
                    by_cath.append(tmp)
        return render(request, 'opatreni.html',
                      {'query_results': by_cath,
                       "location": location,
                       "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola()})

def vrat_seznam(data, description):
    desc = description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
    columns = []
    for col in desc:
        columns.append(col[0])

    dict = {}
    i = 0
    for row in data:
        dict[columns[i]] = row
        i += 1
    print(dict)
    return dict


def aktualnost(request):
    dict = {}
    dict2 = {}

    with connection.cursor() as cursor:
        cursor.execute('''select *
                        from
                        (select * from info order by DATE_UPDATED desc)
                        where
                        ROWNUM <= 1''')
        dict = vrat_seznam(cursor.fetchone(), cursor.description)
        print(dict)

        cursor.execute('''select count(*) as celk_mame from opatreni;''')
        dict2 = vrat_seznam(cursor.fetchone(), cursor.description)

        if((datetime.now() - dict['DATE_UPDATED']) < timedelta(minutes=10)):
            print("Aktualnost kontrolovana pred mene nez 10 minutami")


    res = kontrola.start()
    aktualni = res["aktualni"]
    celkem_mame = dict2["CELK_MAME"]
    smazali_je = res['smazali']
    zmena_odkazu = res['zmena']
    chybi = res['chybi']
    celkem = len(aktualni) + len(smazali_je) + len (zmena_odkazu)+ len (chybi)
    celkem_upravit = int(len(chybi) + len(smazali_je) + len(zmena_odkazu))
    procenta = int(100-((celkem_upravit)/(celkem / 100)))



    if(len(chybi) > 0 or len(zmena_odkazu) > 0 or len(smazali_je) > 0):
        stat = "Data jsou z {}% kompletní a aktuální. \nCelkem máme v databázi {} opatření, {} z nich je aktivních, {} je třeba odstranit, u {} došlo ke změně odkazu a {} chybí a je třeba přidat. ".format(
            procenta,
            celkem_mame,
            celkem,
            len(smazali_je),
            len(zmena_odkazu),
            len(chybi))
        print("ALERT ne všechny data jsou aktuální")
    elif (celkem == 0):
        stat = "Aktuálnost jsme nebyli schopni ověřit. Může to být způsobeno neustálými změnami na webu ministerstva zdravotnictví. Pokusíme se pro to udělat co nejvíce. "
        print("ALERT neaktuální data")
    elif (len(smazali_je) == 0 and len(zmena_odkazu) == 0 and  len(chybi) == 0):
        stat = "Všechna data jsou aktuální!"

    str_for_checksum = "" + str(aktualni) + str(smazali_je) + str(zmena_odkazu) + str(chybi) + stat




    #m = md5("./projektrouska/aktualnost/v_databazi.txt")
    with connection.cursor() as cursor:
            #query_results = cursor.fetchall()
            #desc = cursor.description

            cursor.execute('''insert into INFO (checksum,  date_updated, poznamka, 
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
            ''', {"pozn": stat,
             "checksum":  calcmd5(str_for_checksum),
             "akt": procenta,
             "chybi_pocet": len(chybi),
             "chybi_pole": str(chybi),
             "zmena_link_pocet": len(zmena_odkazu),
             "zmena_link_pole": str(zmena_odkazu),
             "odstranit_pocet": len(smazali_je),
             "odstranit_pole": str(smazali_je),
             "celk_zmen":   celkem_upravit,

                             })


    return render(request, 'aktualnost.html', {'procenta': procenta,
                                               'pridat': chybi,
                                               'celkem': celkem,
                                               'ubrat': smazali_je,
                                               'stejne': aktualni,
                                               'zmena': zmena_odkazu,
                                               'statistika': stat,
                                               "cas": datetime.now(),
                                               "kontrola": posledni_kontrola(),
                                               "posledni_databaze": posledni_databaze(),
                                                "celk_mame": celkem_mame
                                               })


def home(request):
    posledni_kontrola()
    return render(request, 'uvod.html', {"kontrola": posledni_kontrola(),
                                         "posledni_databaze":  posledni_databaze()})


def stats(request):
    return render(request, 'statistiky.html')
def posledni_kontrola():
     with connection.cursor() as cursor:
        # query_results = cursor.fetchall()
        # desc = cursor.description

        cursor.execute('''select * from (select * from INFO order by DATE_UPDATED desc ) where rownum <= 1;''')
        response = cursor.fetchone()


        desc = cursor.description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
        columns = []
        for col in desc:
            columns.append(col[0])

        dict = {}

        i = 0
        for row in response:
            dict[columns[i]] = row
            i += 1
        print(dict)
        return dict
def posledni_databaze():
    with connection.cursor() as cursor:
        last_qu = """select max(posledni_uprava) from(
                       SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from polozka
                       union 
                       SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from opatreni)"""
        cursor.execute(last_qu)
        last_update = cursor.fetchone()
        return last_update[0]
def aktualnost_v_case(request):
    """select min(DATE_UPDATED) as DATE_UPDATED, POZNAMKA, AKTUALNOST, CHYBI_POCET, CHYBI_POLE, ZMENA_LINK_POCET, ZMENA_LINK_POLE, ODSTRANIT_POCET, ODSTRANIT_POLE, CELK_ZMEN from info
group by CHECKSUM, POZNAMKA, AKTUALNOST, CHYBI_POCET, CHYBI_POLE, ZMENA_LINK_POCET, ZMENA_LINK_POLE, ODSTRANIT_POCET, ODSTRANIT_POLE, CELK_ZMEN
order by  DATE_UPDATED"""
def opatreni(request):
    # ?obecmesto_id=replace"
    # "?nuts3_id=replace"'.
    # "?kraj_id=replace"'
    args = request.GET.copy()
    id_obecmesto = (args.get("obecmesto_id", ""))
    nuts3_id = (args.get("nuts3_id", ""))
    okres_id = (args.get("okres_id", ""))
    kraj_id = (args.get("kraj_id", ""))
    flag = "nic"

    with connection.cursor() as cursor:

        qu = ""
        if (id_obecmesto == "" and nuts3_id == "" and kraj_id == "" and  okres_id == ""):  # kraj
            kraj_id = str(1)

        if (id_obecmesto == "" and nuts3_id == "" and kraj_id != "" and okres_id == ""):  # kraj
            flag = "kraj"
            qu = """ select * from (
                    select * from 
                    (
                        select * from
                        (
                            -- kraj 
                            select null as nazev_obecmesto, null as nazev_nuts, null as  nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava  from 
                            (
                                select * from 
                                (
                                    select * from 
                                    (
                                        select id_kraj as kraj_id_kraj, nazev_kraj from kraj where id_kraj=:id_k 
                                    ) join op_kraj using(kraj_id_kraj)
                                ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni   where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                            )
                            union 
                            -- stat 
                            select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava  from (
                            select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                            )


                        ) join polozka on id_opatreni=opatreni_id_opatreni
                    ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie) order by  PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc"""
            misto_qu = """select null as nazev_obecmesto, null as nazev_nuts, null as nazev_okres, nazev_kraj from (
                      select * from kraj  where id_kraj=:id_k) """

        elif (nuts3_id != '') and (id_obecmesto  == '') and (kraj_id == '') and okres_id == "":  # nuts
            flag = "nuts"
            qu = """
                    select * from
                    (
                        select * from (


                        -- nuts3
                        select  null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni,nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava from (
                           select *
                           from (
                                    select *
                                    from (
                                             select *
                                             from (
                                                      select *
                                                      from (
                                                               select ID_NUTS as NUTS3_ID_NUTS, NAZEV_NUTS, KRAJ_ID_KRAJ as ID_KRAJ
                                                               from nuts3
                                                               where id_nuts = :id_nuts
                                                           )
                                                               join OKRES using (NUTS3_ID_NUTS)
                                                  )
                                                      join kraj using (ID_KRAJ)
                                         )
                                )join op_nuts using(nuts3_id_nuts)
                        )join opatreni on opatreni_id_opatreni=opatreni.id_opatreni where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                        union

                        -- okres
                        select  null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava   from
                        (
                            select * from
                            (
                                select * from (
                                    select * from
                                    (
                                       select * from nuts3 where id_nuts=:id_nuts

                                    ) join OKRES on ID_NUTS=OKRES.NUTS3_ID_NUTS
                                ) join kraj on KRAJ.ID_KRAJ = NUTS3_ID_NUTS
                            )
                            join OP_OKRES on OP_OKRES.OKRES_ID_OKRES=ID_OKRES)
                        join opatreni on opatreni_id_opatreni=opatreni.id_opatreni where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                        union
                        -- kraj
                        select null as nazev_obecmesto, nazev_nuts, nazev_okres,  nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava from
                        (
                            select * from
                            (
                                select * from
                                (
                                    select * from
                                    (
                                       select KRAJ_ID_KRAJ as id_kraj, id_nuts, NAZEV_NUTS, kod_nuts from nuts3 where id_nuts=:id_nuts

                                    ) join OKRES on ID_NUTS=OKRES.NUTS3_ID_NUTS
                                ) join op_kraj on op_kraj.kraj_id_kraj=id_kraj
                            ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                        ) join kraj using(id_kraj)
                        -- stat
                        union

                        select null as nazev_obecmesto, null as nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava from (
                        select * from OP_STAT join OPATRENI using(id_opatreni) where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                            )

                    ) join polozka on opatreni_id_opatreni = id_opatreni
                ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by  PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc"""

            misto_qu = """select null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj from (
              select * from (
                           select ID_NUTS, NAZEV_NUTS, KRAJ_ID_KRAJ as id_kraj from nuts3 where ID_NUTS=:id_nuts
                  )join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS
                ) join kraj using(id_kraj);"""
        elif (id_obecmesto == "" and nuts3_id == "" and okres_id != ""  and kraj_id == "") :
            flag = "okres"
            qu= """select * from (
                select * from (
                       -- okres
                        select  null as nazev_obecmesto, null as  nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni,nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava  from (

                            select * from
                            (
                                select * from OKRES  where ID_OKRES = :id_okr
                            ) join kraj on kraj.id_kraj=KRAJ_ID_KRAJ
                            join op_okres on op_okres.okres_id_okres=id_okres
                            )
                        join opatreni on opatreni_id_opatreni=opatreni.id_opatreni   where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                        union
                        -- kraj

                        select null as nazev_obecmesto, null as  nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava from (
                        select * from (
                                select * from
                                (
                                    select * from OKRES  where ID_OKRES = :id_okr
                                ) join op_kraj using(KRAJ_ID_KRAJ)
                            ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                            ) join kraj on KRAJ_ID_KRAJ=kraj.id_kraj

                        union

                        select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,  ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava from
                       (
                        select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                       )

                        ) join polozka on id_opatreni=opatreni_id_opatreni
                    ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by  PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc"""
            misto_qu = """select distinct null as nazev_obecmesto, null as nazev_nuts, nazev_okres, nazev_kraj from (
                             select * from (
                                      select *
                                      from okres
                                      where ID_OKRES = :id_okr
                                  )join kraj on kraj.id_kraj = KRAJ_ID_KRAJ
                            );"""

        elif (id_obecmesto != "" and nuts3_id == "" and kraj_id == ""):  # obecmesto
            flag = "obecmesto"
            qu = """select * from (
        select * from (
                              -- lokalni
                              select nazev_obecmesto,
                                     nazev_nuts,
                                     nazev_okres,
                                     nazev_kraj,
                                     id_opatreni,
                                     nazev_opatreni,
                                     nazev_zkr,
                                     zdroj,
                                     ROZSAH,
                                     platnost_od,
                                     platnost_do, 
                                     platnost_autooprava, 
                                     zdroj_autooprava,
                                     nazev_autooprava
                              from (
                                       select *
                                       from (
                                                select *
                                                from (
                                                         select *
                                                         from (
                                                                  select *
                                                                  from (
                                                                           select *
                                                                           from (select * from obecmesto where id_obecmesto = :id_ob)
                                                                       )
                                                                           join nuts3 on nuts3_id_nuts = nuts3.id_nuts
                                                              )
                                                                  join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS
                                                     )
                                                         join kraj on kraj.id_kraj = nuts3_kraj_id_kraj
                                            )
                                                join op_om on id_obecmesto = op_om.obecmesto_id_obecmesto
                                   )
                                       join opatreni on opatreni_id_opatreni = opatreni.id_opatreni
                              where (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null)
                                and trunc(sysdate) >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1

                              union
                              -- nuts3
                              select nazev_obecmesto,
                                     nazev_nuts,
                                     nazev_okres,
                                     nazev_kraj,
                                     id_opatreni,
                                     nazev_opatreni,
                                     nazev_zkr,
                                     zdroj,
                                     ROZSAH,
                                     platnost_od,
                                     platnost_do,
                                     platnost_autooprava, 
                                     zdroj_autooprava, 
                                     nazev_autooprava
                              from (
                                       select *
                                       from (
                                                select *
                                                from (
                                                         select *
                                                         from (
                                                                  select *
                                                                  from (select * from obecmesto where id_obecmesto = :id_ob)
                                                                           join nuts3 on nuts3_id_nuts = nuts3.id_nuts
                                                              )
                                                     )
                                                         join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS
                                            )
                                                join kraj on kraj.id_kraj = nuts3_kraj_id_kraj
                                                join op_nuts on op_nuts.nuts3_id_nuts = id_nuts)
                                       join opatreni on opatreni_id_opatreni = opatreni.id_opatreni
                              where (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null)
                                and trunc(sysdate) >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1

                              union
                              -- okres
                              select nazev_obecmesto,
                                     nazev_nuts,
                                     nazev_okres,
                                     nazev_kraj,
                                     id_opatreni,
                                     nazev_opatreni,
                                     nazev_zkr,
                                     zdroj,
                                     ROZSAH,
                                     platnost_od,
                                     platnost_do,
                                     platnost_autooprava, 
                                     zdroj_autooprava, 
                                     nazev_autooprava
                              from (
                                       select *
                                       from (
                                                select *
                                                from (
                                                         select *
                                                         from (
                                                                  select *
                                                                  from (select * from obecmesto where id_obecmesto = :id_ob)
                                                                           join nuts3 on nuts3_id_nuts = nuts3.id_nuts)
                                                     )
                                                         join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS
                                            )
                                                join kraj on kraj.id_kraj = nuts3_kraj_id_kraj
                                                join op_okres on op_okres.okres_id_okres = id_okres
                                   )
                                       join opatreni on opatreni_id_opatreni = opatreni.id_opatreni
                              where (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null)
                                and trunc(sysdate) >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1

                              union
                              -- kraj

                              select nazev_obecmesto,
                                     nazev_nuts,
                                     nazev_okres,
                                     nazev_kraj,
                                     id_opatreni,
                                     nazev_opatreni,
                                     nazev_zkr,
                                     zdroj,
                                     ROZSAH,
                                     platnost_od,
                                     platnost_do,
                                     platnost_autooprava, 
                                     zdroj_autooprava, 
                                     nazev_autooprava
                              from (
                                       select *
                                       from (
                                                select *
                                                from (
                                                         select *
                                                         from (
                                                                  select *
                                                                  from (select * from obecmesto where id_obecmesto = :id_ob)
                                                                           join nuts3 on nuts3_id_nuts = nuts3.id_nuts
                                                              )
                                                                  join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS
                                                     )
                                                         join op_kraj on op_kraj.kraj_id_kraj = nuts3_kraj_id_kraj
                                            )
                                                join opatreni on opatreni_id_opatreni = opatreni.id_opatreni
                                       where (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null)
                                         and trunc(sysdate) >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                                   )
                                       join kraj on nuts3_kraj_id_kraj = kraj.id_kraj

                                   -- stat
                              union

                              select null as nazev_obecmesto,
                                     null as nazev_nuts,
                                     null as nazev_okres,
                                     null as nazev_kraj,
                                     id_opatreni,
                                     nazev_opatreni,
                                     nazev_zkr,
                                     zdroj,
                                     ROZSAH,
                                     platnost_od,
                                     platnost_do,
                                     platnost_autooprava, 
                                     zdroj_autooprava, 
                                     nazev_autooprava
                              from (
                                       select *
                                       from OP_STAT
                                                join OPATRENI using (id_opatreni)
                                       where (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null)
                                         and trunc(sysdate) >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                                   )
                          )
              )join polozka on id_opatreni=opatreni_id_opatreni
             join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc"""
            misto_qu = """select nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj from (
              select * from (
                       select * from (
                           select * from obecmesto where id_obecmesto=:id_ob
                           ) join nuts3 on nuts3_id_nuts = nuts3.id_nuts
                  )join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS
                ) join kraj on kraj.id_kraj=nuts3_kraj_id_kraj;"""

        dni_dopredu = 7 # urcuje v horizontu kolika dni se maji zobrazovat nadchazející opatreni
        if (flag == "obecmesto"):
            cursor.execute(qu, {"id_ob": id_obecmesto, "zobrazit_dopredu": dni_dopredu})
        elif (flag == "nuts"):
            cursor.execute(qu, {"id_nuts": nuts3_id, "zobrazit_dopredu": dni_dopredu})
        elif (flag == "okres"):
            cursor.execute(qu, {"id_okr": okres_id, "zobrazit_dopredu": dni_dopredu})
        elif (flag == "kraj"):
            cursor.execute(qu, {"id_k": kraj_id, "zobrazit_dopredu": dni_dopredu})
        # vysledek bude plus minus
        # <class 'tuple'>: ('NAZEV_OBECMESTO', 'NAZEV_NUTS', 'NAZEV_KRAJ', 'ID_OPATRENI', 'NAZEV_OPATRENI', 'NAZEV_ZKR', 'ZDROJ', 'PLATNOST_OD', 'ID_POLOZKA', 'NAZEV', 'KOMENTAR', 'KATEGORIE_ID_KATEGORIE', 'TYP', 'OPATRENI_ID_OPATRENI', 'ID_KATEGORIE', 'NAZEV_KAT', 'KOMENT_KATEGORIE')

        query_results = cursor.fetchall()
        desc = cursor.description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
        # nezavisle na tom chci vedet, ktere misto uzivatel zadal
        if (flag == "obecmesto"):
            cursor.execute(misto_qu, {"id_ob": id_obecmesto})
        elif (flag == "nuts"):
            cursor.execute(misto_qu, {"id_nuts": nuts3_id})
        elif (flag == "okres"):
            cursor.execute(misto_qu, {"id_okr": okres_id})
        elif (flag == "kraj"):
            cursor.execute(misto_qu, {"id_k": kraj_id})

        location_results = cursor.fetchone()
        location_desc = cursor.description



        ### MAGIC ###
        columns = []
        for col in desc:
            columns.append(col[0])

        location_columns = []
        for col in location_desc:
            location_columns.append(col[0])

        a = []

        for line in query_results:
            temp = {}
            for i in range(0, len(line)):
                temp[columns[i]] = line[i]
            a.append(temp)

        location = {}
        i = 0
        for line in location_results:
            # {'key': 'value', 'mynewkey': 'mynewvalue'}
            location[location_columns[i]]=line
            i += 1


        # setrizene podle kategorie
        by_cath = []

        existing = []
        for col in a:
            if ("NAZEV_KAT" in col):  # fajn, ted zkontroluju, jestli uz jsem to vypsal, nebo ne
                if (col["NAZEV_KAT"] in existing):
                    by_cath[len(by_cath) - 1]["narizeni"].append(col)
                else:
                    existing.append(col["NAZEV_KAT"])
                    tmp = {"kategorie": col["NAZEV_KAT"], "narizeni": [col]}
                    by_cath.append(tmp)
        return render(request, 'opatreni.html',
                      {'query_results': by_cath,
                       "location": location,
                       "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola()})



# TODO fix javascript to use dicts
def najdi_mesto(request):
    # misto, ktere hledam je ulozene v args
    args = request.GET.copy()
    mojemisto = str(args.get("misto", "Praha"))
    zobraz = len(mojemisto*5)

    if (len(mojemisto) < 2):
        return

    qu = '''select * from (
        SELECT distinct null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, null as id_okres, null as nazev_okres,  nazev_kraj, id_kraj 
        from kraj WHERE lower(nazev_kraj) LIKE lower('Pra%')

        union 
        (
            SELECT distinct null as id_obecmesto, null as nazev_obecmesto, id_nuts, nazev_nuts, id_okres, nazev_okres,  nazev_kraj, id_kraj from nuts3
            join okres on NUTS3_ID_NUTS=ID_NUTS
            join kraj on nuts3.kraj_id_kraj=kraj.id_kraj WHERE lower(nazev_nuts) LIKE lower('Pra%') -- fuck you, oracle and security.

        )
        union 
        (
            SELECT distinct null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, id_okres, nazev_okres,  nazev_kraj, id_kraj from okres
            join kraj on kraj_id_kraj=kraj.id_kraj WHERE lower(nazev_okres) LIKE lower('Pra%') -- fuck you, oracle and security.
        )
        union
        (
            select distinct * from
            (
                select id_obecmesto, nazev_obecmesto, id_nuts, nazev_nuts,  id_okres, nazev_okres, nazev_kraj, id_kraj from
                (
                    select * from (SELECT ID_NUTS, ID_OBECMESTO, KRAJ_ID_KRAJ as ID_KRAJ, NAZEV_NUTS, NAZEV_OBECMESTO, NUTS3_ID_NUTS
                                   FROM obecmesto
                                            join nuts3 on nuts3_id_nuts = nuts3.id_nuts
                                   WHERE lower(nazev_obecmesto) LIKE lower('Pra%')
                    ) join OKRES on OKRES.NUTS3_ID_NUTS=ID_NUTS

                ) join kraj using (id_kraj)
            )
        ) order by  nazev_obecmesto asc nulls first,  id_nuts asc nulls first, id_okres asc nulls first) '''# WHERE ROWNUM <= :zraz
    result = all(c.isalnum() or c.isspace() for c in mojemisto)

    if (not result):
        return JsonResponse({'data': 'empty', 'invalid': 'Invalid character! Please stop injecting. Thank you'},
                            safe=False)

    with connection.cursor() as cursor:

            # try:
        cursor.execute(qu.replace("Pra", str(mojemisto)))
        query_results = cursor.fetchall()
        desc = cursor.description
        # nt_result = namedtuple('Result', [col[0] for col in desc])
        columns = []
        for col in desc:
            columns.append(col[0])
        out_dict_array = []

        for line in query_results:
            temp = {}
            for i in range(0, len(line)):
                temp[columns[i]] = line[i]
            out_dict_array.append(temp)


        jsonStr = json.dumps(out_dict_array)

        if (jsonStr == []):
            return JsonResponse({'data': 'empty'}, safe=False)
        return JsonResponse(jsonStr, safe=False)
        # except:
        #    print("Error occured")



# TODO Pokud bude ve výsledku query dva řádky, které se budou lišit pouze v tom, že jeden je nuts a obecmesto je null a druhý že je nuts a obecmesto není null (pro uživatele vypadá jako dva stejné výsledky), tak smaž jeden z nich (asi ten NUTS)
def najdi_mesto(request):
    # misto, ktere hledam je ulozene v args
    args = request.GET.copy()
    mojemisto = str(args.get("misto", "Praha"))
    zobraz = len(mojemisto*5)

    if (len(mojemisto) < 2):
        return

    qu = '''select * from (
        SELECT null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, null as id_okres, null as nazev_okres,  nazev_kraj, id_kraj 
        from kraj WHERE lower(nazev_kraj) LIKE lower('Pra%')

        union 
        (
            SELECT null as id_obecmesto, null as nazev_obecmesto, id_nuts, nazev_nuts, id_okres, nazev_okres,  nazev_kraj, id_kraj from nuts3
            join okres on NUTS3_ID_NUTS=ID_NUTS
            join kraj on nuts3.kraj_id_kraj=kraj.id_kraj WHERE lower(nazev_nuts) LIKE lower('Pra%') -- fuck you, oracle and security.

        )
        union 
        (
            SELECT null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, id_okres, nazev_okres,  nazev_kraj, id_kraj from okres
            join kraj on kraj_id_kraj=kraj.id_kraj WHERE lower(nazev_okres) LIKE lower('Pra%') -- fuck you, oracle and security.
        )
        union
        (
            select  * from
            (
                select id_obecmesto, nazev_obecmesto, id_nuts, nazev_nuts,  id_okres, nazev_okres, nazev_kraj, id_kraj from
                (
                    select * from (SELECT ID_NUTS, ID_OBECMESTO, KRAJ_ID_KRAJ as ID_KRAJ, NAZEV_NUTS, NAZEV_OBECMESTO, NUTS3_ID_NUTS
                                   FROM obecmesto
                                            join nuts3 on nuts3_id_nuts = nuts3.id_nuts
                                   WHERE lower(nazev_obecmesto) LIKE lower('Pra%')
                    ) join OKRES on OKRES.NUTS3_ID_NUTS=ID_NUTS

                ) join kraj using (id_kraj)
            )
        ) order by  nazev_obecmesto asc nulls first,  id_nuts asc nulls first, id_okres asc nulls first) where rownum < 10 '''# WHERE ROWNUM <= :zraz
    result = all(c.isalnum() or c.isspace() for c in mojemisto)

    if (not result):
        return JsonResponse({'data': 'empty', 'invalid': 'Invalid character! Please stop injecting. Thank you'},
                            safe=False)

    with connection.cursor() as cursor:

            # try:
        cursor.execute(qu.replace("Pra", str(mojemisto)))
        query_results = cursor.fetchall()
        desc = cursor.description
        # nt_result = namedtuple('Result', [col[0] for col in desc])
        columns = []
        for col in desc:
            columns.append(col[0])
        out_dict_array = []

        for line in query_results:
            temp = {}
            for i in range(0, len(line)):
                temp[columns[i]] = line[i]
            out_dict_array.append(temp)


        jsonStr = json.dumps(out_dict_array)

        if (jsonStr == []):
            return JsonResponse({'data': 'empty'}, safe=False)
        return JsonResponse(jsonStr, safe=False)
        # except:
        #    print("Error occured")
