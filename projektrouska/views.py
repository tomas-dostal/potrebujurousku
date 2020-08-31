import datetime
import json

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.db import connection
from collections import namedtuple


def about(request):
    print("o projektu")
    return render(request, 'o_projektu.html')


def home(request):
    print("home")
    return render(request, 'uvod.html')


def stats(request):
    return render(request, 'statistiky.html')


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
        last_qu = """select max(posledni_uprava) from(
                      SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from polozka
                      union 
                      SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from opatreni)"""

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
                            select null as nazev_obecmesto, null as nazev_nuts, null as  nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do  from 
                            (
                                select * from 
                                (
                                    select * from 
                                    (
                                        select id_kraj as kraj_id_kraj, nazev_kraj from kraj where id_kraj=:id_k 
                                    ) join op_kraj using(kraj_id_kraj)
                                ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni   where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
                            )
                            union 
                            -- stat 
                            select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do  from (
                            select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
                            )


                        ) join polozka on id_opatreni=opatreni_id_opatreni
                    ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie) order by id_kategorie asc, PLATNOST_OD asc;"""
            misto_qu = """select null as nazev_obecmesto, null as nazev_nuts, null as nazev_okres, nazev_kraj from (
                      select * from kraj  where id_kraj=:id_k) """

        elif (nuts3_id != '') and (id_obecmesto is '') and (kraj_id is '') and okres_id == "":  # nuts
            flag = "nuts"
            qu = """
                    select * from
                    (
                        select * from (


                        -- nuts3
                        select  null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni,nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do  from (
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
                        )join opatreni on opatreni_id_opatreni=opatreni.id_opatreni where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
                        union

                        -- okres
                        select  null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do   from
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
                        join opatreni on opatreni_id_opatreni=opatreni.id_opatreni where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
                        union
                        -- kraj
                        select null as nazev_obecmesto, nazev_nuts, nazev_okres,  nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do  from
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
                            ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
                        ) join kraj using(id_kraj)
                        -- stat
                        union

                        select null as nazev_obecmesto, null as nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do  from (
                        select * from OP_STAT join OPATRENI using(id_opatreni) where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
                            )

                    ) join polozka on opatreni_id_opatreni = id_opatreni
                ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by id_kategorie asc, PLATNOST_OD asc;"""

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
                        select  null as nazev_obecmesto, null as  nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni,nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do   from (
            
                            select * from
                            (
                                select * from OKRES  where ID_OKRES = :id_okr
                            ) join kraj on kraj.id_kraj=KRAJ_ID_KRAJ
                            join op_okres on op_okres.okres_id_okres=id_okres
                            )
                        join opatreni on opatreni_id_opatreni=opatreni.id_opatreni   where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
                        union
                        -- kraj
            
                        select null as nazev_obecmesto, null as  nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do from (
                        select * from (
                                select * from
                                (
                                    select * from OKRES  where ID_OKRES = :id_okr
                                ) join op_kraj using(KRAJ_ID_KRAJ)
                            ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
                            ) join kraj on KRAJ_ID_KRAJ=kraj.id_kraj
                            
                        union 
                         
                        select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,  ROZSAH,  platnost_od , platnost_do from (
                        select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2

            
            
                        ) join polozka on id_opatreni=opatreni_id_opatreni
                    ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by id_kategorie asc, PLATNOST_OD asc;"""
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
            select nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj, ROZSAH,  platnost_od , platnost_do   from (
                select  *  from (
                   select * from (
                        select * from (
                           select * from (
                                select * from ( select * from obecmesto where id_obecmesto=:id_ob)
                           ) join nuts3 on nuts3_id_nuts=nuts3.id_nuts
                       ) join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS

                   ) join kraj on kraj.id_kraj=nuts3_kraj_id_kraj

                   ) join op_om on id_obecmesto=op_om.obecmesto_id_obecmesto

                ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2

            union
            -- nuts3
            select  nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj, ROZSAH,  platnost_od , platnost_do   from (

                select * from
                (
                    select * from
                    (
                        select * from
                        (

                        select * from (select * from obecmesto where id_obecmesto=:id_ob )
                        join nuts3 on nuts3_id_nuts=nuts3.id_nuts
                        )
                    ) join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS

                ) join kraj on kraj.id_kraj=nuts3_kraj_id_kraj
                join op_nuts on op_nuts.nuts3_id_nuts=id_nuts)
            join opatreni on opatreni_id_opatreni=opatreni.id_opatreni   where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
            union
            -- okres
            select  nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,  ROZSAH,  platnost_od , platnost_do   from
           (

                select * from
                (
                    select * from
                       (
                          select *
                          from (
                                   select *
                                   from (select * from obecmesto where id_obecmesto = :id_ob)
                                            join nuts3 on nuts3_id_nuts = nuts3.id_nuts)
                      ) join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS
                ) join kraj on kraj.id_kraj=nuts3_kraj_id_kraj
                join op_okres on op_okres.okres_id_okres=id_okres
                )
            join opatreni on opatreni_id_opatreni=opatreni.id_opatreni   where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
            union
            -- kraj

            select nazev_obecmesto,  nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr,   zdroj,  ROZSAH, platnost_od , platnost_do from (
            select * from (
                    select * from
                    (
                        select * from
                        (
                        select * from (select * from obecmesto where id_obecmesto=:id_ob )
                        join nuts3 on nuts3_id_nuts=nuts3.id_nuts
                        ) join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS

                    ) join op_kraj on op_kraj.kraj_id_kraj=nuts3_kraj_id_kraj
                ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2
                ) join kraj on nuts3_kraj_id_kraj=kraj.id_kraj

            -- stat
            union

            select null as nazev_obecmesto, null as nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do from (
            select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) <= PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD -2


            ) join polozka on id_opatreni=opatreni_id_opatreni
            ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by id_kategorie asc, PLATNOST_OD asc;"""
            misto_qu = """select nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj from (
              select * from (
                       select * from (
                           select * from obecmesto where id_obecmesto=:id_ob
                           ) join nuts3 on nuts3_id_nuts = nuts3.id_nuts
                  )join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS
                ) join kraj on kraj.id_kraj=nuts3_kraj_id_kraj;"""

        if (flag == "obecmesto"):
            cursor.execute(qu, {"id_ob": id_obecmesto})
        elif (flag == "nuts"):
            cursor.execute(qu, {"id_nuts": nuts3_id})
        elif (flag == "okres"):
            cursor.execute(qu, {"id_okr": okres_id})
        elif (flag == "kraj"):
            cursor.execute(qu, {"id_k": kraj_id})
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

        cursor.execute(last_qu)
        last_update = cursor.fetchone()

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
                      {'query_results': by_cath, "location": location, "last_update": last_update,'now': datetime.datetime.now()})


def najdi_mesto(request):
    # misto, ktere hledam je ulozene v args
    args = request.GET.copy()
    mojemisto = str(args.get("misto", "Praha"))

    if (len(mojemisto) < 2):
        return

    qu = """select * from (
        SELECT null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, nazev_kraj, id_kraj 
        from kraj WHERE lower(nazev_kraj) LIKE lower('%Pra%')

        union 
        (
            SELECT null as id_obecmesto, null as nazev_obecmesto, id_nuts, nazev_nuts, nazev_kraj, id_kraj from nuts3   
            join kraj on nuts3.kraj_id_kraj=kraj.id_kraj WHERE lower(nazev_nuts) LIKE lower('%Pra%') -- fuck you, oracle and security. 

        )
        union
        (
            select  * from 
            (
                select id_obecmesto, nazev_obecmesto, id_nuts, nazev_nuts, nazev_kraj, id_kraj from 
                (
                    SELECT * FROM obecmesto join nuts3 on nuts3_id_nuts=nuts3.id_nuts WHERE  lower(nazev_obecmesto) LIKE lower('%Pra%')


                ) join kraj on kraj_id_kraj=kraj.id_kraj  
            )
        ) order by  nazev_obecmesto asc nulls first,  id_nuts asc nulls first)  WHERE ROWNUM <= 10 """
    result = all(c.isalnum() or c.isspace() for c in mojemisto)

    if (not result):
        return JsonResponse({'data': 'empty', 'invalid': 'Invalid character! Please stop injecting. Thank you'},
                            safe=False)

    with connection.cursor() as cursor:

        qu = qu.replace("Pra", str(mojemisto))

        # try:
        cursor.execute(qu)
        query_results = cursor.fetchall()
        desc = cursor.description
        # nt_result = namedtuple('Result', [col[0] for col in desc])

        jsonStr = json.dumps(query_results)

        if (jsonStr == []):
            return JsonResponse({'data': 'empty'}, safe=False)
        return JsonResponse(jsonStr, safe=False)
        # except:
        #    print("Error occured")