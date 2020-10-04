import json
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from datetime import datetime, timedelta

from django.shortcuts import render
from django.db import connection
from projektrouska.aktualnost import kontrola
from projektrouska.settings import DEV
from projektrouska.functions import *
from projektrouska.api import *

#@require_GET
def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /private/",
        "Disallow: /junk/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def about(request):
    return render(request, 'sites/o_projektu.html', {"kontrola": posledni_kontrola(),
                                                     "zastarala_data": zastarala_data()})


def home(request):
    import requests
    r = requests.get(url='https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/zakladni-prehled.json')
    result = r.json()["data"][0]
    data_modified=datetime.fromisoformat(r.json()["modified"])

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
    vcera = int( result["potvrzene_pripady_vcerejsi_den"])
    testu_vcera = int( result["provedene_testy_vcerejsi_den"])
    pozitivnich = round(vcera / (testu_vcera / 100),2)



    return render(request, 'sites/home.html', {"kontrola": posledni_kontrola(),
                                               "datum": result["datum"],
                                               "provedene_testy_celkem": format_num(result["provedene_testy_celkem"]),
                                               "potvrzene_pripady_celkem": format_num(result["potvrzene_pripady_celkem"]),
                                               "aktivni_pripady": format_num(result["aktivni_pripady"]),
                                               "vyleceni": format_num(result["vyleceni"]),
                                               "umrti": format_num(result["umrti"]),
                                               "aktualne_hospitalizovani": format_num(result["aktualne_hospitalizovani"]),
                                               "provedene_testy_vcerejsi_den": format_num(result["provedene_testy_vcerejsi_den"]),
                                               "pozitivnich_procenta_vcera": pozitivnich,
                                               "potvrzene_pripady_vcerejsi_den": format_num(result["potvrzene_pripady_vcerejsi_den"]),
                                               "potvrzene_pripady_dnesni_den": format_num(result["potvrzene_pripady_dnesni_den"]),
                                                "posledni_update_dat": data_modified.strftime("%d.%m.%Y %H:%M"),
                                                "posledni_databaze":  posledni_databaze(),
                                                "zastarala_data": zastarala_data()})
def stats(request):
    return render(request, 'sites/statistiky.html')


def indikator_aktualnost():
    with connection.cursor() as cursor:
        # query_results = cursor.fetchall()
        # desc = cursor.description

        cursor.execute('''select *
                        from
                        (select * from info order by DATE_UPDATED desc)
                        where
                        ROWNUM <= 1''')

        dict = return_as_dict(cursor.fetchone(), cursor.description)

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
        return render(request, 'sites/opatreni.html',
                      {'query_results': by_cath,
                       "location": location,
                       "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola(),
                       "zastarala_data": zastarala_data()})

def aktualnost(request):
    dict = {}
    dict2 = {}

    with connection.cursor() as cursor:
        cursor.execute('''select *
                        from
                        (select * from info order by DATE_UPDATED desc)
                        where
                        ROWNUM <= 1''')
        dict = return_as_dict(cursor.fetchone(), cursor.description)
        print(dict)

        cursor.execute('''select count(*) as celk_mame from opatreni;''')
        dict2 = return_as_dict(cursor.fetchone(), cursor.description)

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
    try:
        procenta = int(100-((celkem_upravit)/(celkem / 100)))
    except:
        procenta = 100
    if(DEV):
        try:
            print("SMAZALI")
            for i in smazali_je:
                print("SMAZALI ID={}, nazev {}".format(i['ID_OPATRENI'], i['NAZEV_OPATRENI']))

            print("Zmena odkazu")
            for i in zmena_odkazu:
                print("ZMENA ID={}, nazev {}\nStary {}\nNovy: {}".format(i['ID_OPATRENI'], i['NAZEV_OPATRENI'],  i['STARY_ODKAZ'],  i['ZDROJ']))
            print("CHYBI")
            for i in chybi:
                print("CHYBI  nazev {} \nodkaz: {}".format(i['nazev'],i['odkaz']))

        except:
            print("Nezkontroloval jsem spravne parametry vypisu a uz se mi to nechce opravovat")

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

            z = str(zmena_odkazu)[:3000]
            s = str(smazali_je)[:3000]
            c = str(chybi)[:3000]

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
             "chybi_pole": c,
             "zmena_link_pocet": len(zmena_odkazu),
             "zmena_link_pole": z,
             "odstranit_pocet": len(smazali_je),
             "odstranit_pole": s,
             "celk_zmen":   int(celkem_upravit) })


    return render(request, 'sites/aktualnost.html', {'procenta': procenta,
                                               'pridat': chybi,
                                               'celkem': celkem,
                                               'ubrat': smazali_je,
                                               'stejne': aktualni,
                                               'zmena': zmena_odkazu,
                                               'statistika': stat,
                                               "cas": datetime.now(),
                                               "kontrola": posledni_kontrola(),
                                               "posledni_databaze": posledni_databaze(),
                                               "celk_mame": celkem_mame,
                                               "zastarala_data": zastarala_data()
                                                     })


def posledni_kontrola():
     with connection.cursor() as cursor:
        # query_results = cursor.fetchall()
        # desc = cursor.description

        cursor.execute('''select * from (select * from INFO order by DATE_UPDATED desc ) where rownum <= 1;''')
        dict = return_as_dict(cursor.fetchone(), cursor.description)
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
# source: https://stackoverflow.com/questions/8906926/formatting-timedelta-objects
def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)

def zastarala_data():
    posledni_datetime = posledni_kontrola()["DATE_UPDATED"]
    naposledy_povedeno = ( datetime.now() - posledni_datetime)
    str_naposledy = strfdelta(naposledy_povedeno, "{days} dny, {hours} hodinami {minutes} minutami") #  {seconds} vteřinami
    if((datetime.now() - posledni_datetime) < timedelta(minutes=60)):
        return {"zastarala_data": False,  "posledni_uspesna_kontrola_timespan": str_naposledy}
    return {"zastarala_data": True, "posledni_uspesna_kontrola_timespan": str_naposledy}


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
                                ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni   where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                            )
                            union 
                            -- stat 
                            select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava  from (
                            select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
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
                        )join opatreni on opatreni_id_opatreni=opatreni.id_opatreni where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                        union

                        -- okres
                        select  null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava   from
                        (
                            select * from
                            (
                                select * from (
                                    select * from
                                    (
                                       select id_nuts, nazev_nuts, kod_nuts, kraj_id_kraj as id_kraj from nuts3 where id_nuts=:id_nuts

                                    ) join OKRES on ID_NUTS=OKRES.NUTS3_ID_NUTS
                                ) join kraj using(ID_KRAJ)
                            )
                            join OP_OKRES on OP_OKRES.OKRES_ID_OKRES=ID_OKRES)
                        join opatreni on opatreni_id_opatreni=opatreni.id_opatreni where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
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
                            ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                        ) join kraj using(id_kraj)
                        -- stat
                        union

                        select null as nazev_obecmesto, null as nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava from (
                        select * from OP_STAT join OPATRENI using(id_opatreni) where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
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
                        join opatreni on opatreni_id_opatreni=opatreni.id_opatreni   where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                        union
                        -- kraj

                        select null as nazev_obecmesto, null as  nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava from (
                        select * from (
                                select * from
                                (
                                    select * from OKRES  where ID_OKRES = :id_okr
                                ) join op_kraj using(KRAJ_ID_KRAJ)
                            ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                            ) join kraj on KRAJ_ID_KRAJ=kraj.id_kraj

                        union

                        select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,  ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava from
                       (
                        select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
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
            qu = """
            select * from (
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
                              where (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null)
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
                              where (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null)
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
                              where (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null)
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
                                       where (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null)
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
                                       where (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null)
                                         and trunc(sysdate) >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                                   )
                          )
              )join polozka on id_opatreni=opatreni_id_opatreni
             join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc 
             """
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

        location = return_as_dict(cursor.fetchone(), cursor.description)
        array = return_as_array(query_results, desc)

        # oder by cathegory
        by_cath = []
        existing = []
        for col in array:
            if ("NAZEV_KAT" in col):  # fajn, ted zkontroluju, jestli uz jsem to vypsal, nebo ne
                if (col["NAZEV_KAT"] in existing):
                    by_cath[len(by_cath) - 1]["narizeni"].append(col)
                else:
                    existing.append(col["NAZEV_KAT"])
                    tmp = {"kategorie": col["NAZEV_KAT"], "narizeni": [col]}
                    by_cath.append(tmp)

        return render(request, 'sites/opatreni.html',
                      {'query_results': by_cath,
                       "location": location,
                       "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola(),
                       "zastarala_data": zastarala_data()
                       })

def opaterni_celoplosne(request):
    qu = """
        select * from (
    select * from (
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
                                   where (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null)
                                     and trunc(sysdate) >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                               )
                      )
          )join polozka on id_opatreni=opatreni_id_opatreni
         join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc 
         """

    with connection.cursor() as cursor:

        cursor.execute(qu, {"zobrazit_dopredu": 7})
        # vysledek bude plus minus
        # <class 'tuple'>: ('NAZEV_OBECMESTO', 'NAZEV_NUTS', 'NAZEV_KRAJ', 'ID_OPATRENI', 'NAZEV_OPATRENI', 'NAZEV_ZKR', 'ZDROJ', 'PLATNOST_OD', 'ID_POLOZKA', 'NAZEV', 'KOMENTAR', 'KATEGORIE_ID_KATEGORIE', 'TYP', 'OPATRENI_ID_OPATRENI', 'ID_KATEGORIE', 'NAZEV_KAT', 'KOMENT_KATEGORIE')

        query_results = cursor.fetchall()
        desc = cursor.description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
        array = return_as_array(query_results, desc)

        # oder by cathegory
        by_cath = []
        existing = []
        for col in array:
            if ("NAZEV_KAT" in col):  # fajn, ted zkontroluju, jestli uz jsem to vypsal, nebo ne
                if (col["NAZEV_KAT"] in existing):
                    by_cath[len(by_cath) - 1]["narizeni"].append(col)
                else:
                    existing.append(col["NAZEV_KAT"])
                    tmp = {"kategorie": col["NAZEV_KAT"], "narizeni": [col]}
                    by_cath.append(tmp)

        return render(request, 'sites/celostatni_opatreni.html',
                      {'query_results': by_cath,
                       "posledni_databaze": posledni_databaze(),
                       'now': datetime.now(),
                       "kontrola": posledni_kontrola(),
                       "zastarala_data": zastarala_data()
                       })



