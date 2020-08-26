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
    return render(request, 'hello_world.html')

def opatreni(request):
    #?obecmesto_id=replace"
    #"?nuts3_id=replace"'.
    #"?kraj_id=replace"'
    args = request.GET.copy()

    obecmesto_id = args.get("obecmesto_id", "")
    nuts3_id = args.get("nuts3_id", "")
    kraj_id = args.get("kraj_id", "")
    last_qu = """select max(posledni_uprava) from(
                  SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from polozka
                  union 
                  SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from opatreni);"""

    qu = ""
    if(obecmesto_id == "" and nuts3_id == "" and kraj_id == ""): # kraj
        kraj_id = str(1)

    if(obecmesto_id == "" and nuts3_id == "" and kraj_id != ""): # kraj
        qu = ""

        qu=""" select * from 
                (
                    select * from
                    (
                        -- kraj 
                        select null as nazev_obecmesto, null as nazev_nuts, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr,  zdroj, platnost_od  from 
                        (
                            select * from 
                            (
                                select * from 
                                (
                                    select id_kraj as kraj_id_kraj, nazev_kraj from kraj where id_kraj=IDKRAJ 
                                ) join op_kraj using(kraj_id_kraj)
                            ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where je_platne = 1
                        )
                        
                    ) join polozka on id_opatreni=opatreni_id_opatreni
                ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by id_kategorie asc;"""
        qu=qu.replace("IDKRAJ", kraj_id)
        misto_qu = """select ' ' as misto, nazev_kraj as kraj from (
                  select * from kraj  where id_kraj=IDKRAJ  )
"""
        misto_qu = misto_qu.replace("IDKRAJ ", kraj_id)

    if (nuts3_id != '') and (obecmesto_id is '') and (kraj_id is ''): # nuts3
        qu = ""

        qu= """select * from 
                (
                    select * from 
                    (
                        -- nuts3 
                        select  null as nazev_obecmesto, nazev_nuts, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr,  zdroj, platnost_od   from 
                        (
                            select * from 
                            (
                                select * from ( select * from nuts3 where id_nuts=IDNUTS)
                                join kraj on kraj.id_kraj=kraj_id_kraj
                            )
                            join op_nuts on op_nuts.nuts3_id_nuts=id_nuts)
                        join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where je_platne = 1
                        union 
                        -- kraj 
                        select null as nazev_obecmesto, nazev_nuts, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr,  zdroj, platnost_od  from 
                        (
                            select * from 
                            (
                                select * from 
                                (
                                    select * from nuts3 where id_nuts=IDNUTS 
                                ) join op_kraj using(kraj_id_kraj)
                            ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where je_platne = 1
                        ) join kraj on kraj_id_kraj=kraj.id_kraj
                        
                    ) join polozka on id_opatreni=opatreni_id_opatreni
                ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by id_kategorie asc;"""
        qu=qu.replace("IDNUTS", nuts3_id)

        misto_qu = """select nazev_nuts as misto, nazev_kraj as kraj from (
                select * from (select * from nuts3 where id_nuts=IDNUTS  )
          
            ) join kraj on kraj.id_kraj=kraj_id_kraj"""
        misto_qu = misto_qu.replace("IDNUTS ", nuts3_id)

    if (obecmesto_id != "" and nuts3_id == "" and kraj_id == ""): # obecmesto
        qu = ""
        qu="""select * from (
        select * from (
        -- lokalni
        select nazev_obecmesto, nazev_nuts, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr,  zdroj, platnost_od   from (
            select  *  from (
               select * from (
                   select * from (
                        select * from ( select * from obecmesto where id_obecmesto=IDOBECMESTO)
                   ) join nuts3 on nuts3_id_nuts=nuts3.id_nuts
               ) join kraj on kraj.id_kraj=nuts3_kraj_id_kraj
            
               ) join op_om on id_obecmesto=op_om.obecmesto_id_obecmesto
                
            ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni where je_platne = 1
        
        union
        -- nuts3 
        select  nazev_obecmesto, nazev_nuts, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr,  zdroj, platnost_od   from (
           
            select * from (
                select * from (
                select * from (select * from obecmesto where id_obecmesto=IDOBECMESTO )
                join nuts3 on nuts3_id_nuts=nuts3.id_nuts)
            ) join kraj on kraj.id_kraj=nuts3_kraj_id_kraj
            join op_nuts on op_nuts.nuts3_id_nuts=id_nuts)
        join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where je_platne = 1
        union 
        -- kraj 
        
        select nazev_obecmesto, nazev_nuts, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr,  zdroj, platnost_od from (
        select * from (
                select * from 
                (
                    select * from (select * from obecmesto where id_obecmesto=IDOBECMESTO )
                    join nuts3 on nuts3_id_nuts=nuts3.id_nuts
                ) join op_kraj on op_kraj.kraj_id_kraj=nuts3_kraj_id_kraj
            ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where je_platne = 1
            ) join kraj on nuts3_kraj_id_kraj=kraj.id_kraj
        
        
        ) join polozka on id_opatreni=opatreni_id_opatreni
        ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by id_kategorie asc;"""
        qu = qu.replace("IDOBECMESTO", obecmesto_id)

        misto_qu = """select nazev_obecmesto as misto, nazev_kraj as kraj from (
                select * from (
                select * from (select * from obecmesto where id_obecmesto=IDOBECMESTO )
                join nuts3 on nuts3_id_nuts=nuts3.id_nuts)
            ) join kraj on kraj.id_kraj=nuts3_kraj_id_kraj"""
        misto_qu = misto_qu.replace("IDOBECMESTO", obecmesto_id)


    with connection.cursor() as cursor:
        cursor.execute(qu)
        query_results = cursor.fetchall()
        desc = cursor.description

        cursor.execute(misto_qu)
        location_results =  cursor.fetchone()
        location_desc = cursor.description

        nt_result = namedtuple('Result', [col[0] for col in desc])


        cursor.execute(last_qu)
        last_update = cursor.fetchone()



        columns = []
        for col in desc:
            columns.append(col[0])

        location_columns = []
        for col in location_desc:
            location_columns.append(col[0])

        # <class 'tuple'>: ('NAZEV_OBECMESTO', 'NAZEV_NUTS', 'NAZEV_KRAJ', 'ID_OPATRENI', 'NAZEV_OPATRENI', 'NAZEV_ZKR', 'ZDROJ', 'PLATNOST_OD', 'ID_POLOZKA', 'NAZEV', 'KOMENTAR', 'KATEGORIE_ID_KATEGORIE', 'TYP', 'OPATRENI_ID_OPATRENI', 'ID_KATEGORIE', 'NAZEV_KAT', 'KOMENT_KATEGORIE')
        a = []

        for line in query_results:
            temp = []
            for i in range(0, len(line)):
                temp.append({columns[i]: line[i]})
            a.append(temp)

        location = []
        i = 0
        for line in location_results:
            location.append({location_columns[i]: line})
            i+= 1

        by_cath = []

        existing = []
        for record in a:
            for col in record:
                if("NAZEV_KAT" in col): # fajn, ted zkontroluju, jestli uz jsem to vypsal, nebo ne
                    if(col["NAZEV_KAT"] in existing):
                        by_cath[len(by_cath)-1]["narizeni"].append(record)
                    else:
                        existing.append(col["NAZEV_KAT"])
                        tmp = {"kategorie": col["NAZEV_KAT"], "narizeni": [record]}
                        by_cath.append(tmp)



        return render(request, 'opatreni.html', {'query_results': by_cath, "location": location, "last_update": last_update})

    """
        columns = []
        for col in desc:
            columns.append(col[0])

        # <class 'tuple'>: ('NAZEV_OBECMESTO', 'NAZEV_NUTS', 'NAZEV_KRAJ', 'ID_OPATRENI', 'NAZEV_OPATRENI', 'NAZEV_ZKR', 'ZDROJ', 'PLATNOST_OD', 'ID_POLOZKA', 'NAZEV', 'KOMENTAR', 'KATEGORIE_ID_KATEGORIE', 'TYP', 'OPATRENI_ID_OPATRENI', 'ID_KATEGORIE', 'NAZEV_KAT', 'KOMENT_KATEGORIE')
        a = []
        for line in query_results:
            temp = []
            for i in range(0, len(line)):
                temp.append({columns[i]: line[i]})
            a.append(temp)
        return render(request, 'opatreni.html', {'query_results': a})"""


    #return row

    #return render(request, 'hello_world.html', {'objs':query_results})

def najdi_mesto(request):
        args = request.GET.copy()
        misto = args.get("misto", "Praha")

        qu = """select * from (
        SELECT  null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, nazev_kraj, id_kraj from kraj WHERE lower(nazev_kraj) LIKE lower('%Pra%')
union 
(SELECT null as id_obecmesto, null as nazev_obecmesto, id_nuts, nazev_nuts, nazev_kraj, id_kraj from nuts3   join kraj on nuts3.kraj_id_kraj=kraj.id_kraj WHERE lower(nazev_nuts) LIKE  lower('%Pra%'))
union
(
select  * from (
    select id_obecmesto, nazev_obecmesto, id_nuts, nazev_nuts, nazev_kraj, id_kraj from (
    SELECT * FROM obecmesto join nuts3 on nuts3_id_nuts=nuts3.id_nuts WHERE  lower(nazev_obecmesto) LIKE lower('%Pra%')
    ) join kraj on kraj_id_kraj=kraj.id_kraj  
)
) order by  nazev_obecmesto asc nulls first,  id_nuts asc nulls first)  WHERE ROWNUM <= 10 ;""".replace("\n", "")

        #diacritics = "( SELECT CONVERT( 'Pra', 'SF7ASCII' ) FROM DUAL )"

        qu = qu.replace("Pra", str(misto))
        with connection.cursor() as cursor:
            cursor.execute(qu)
            query_results = cursor.fetchall()
            desc = cursor.description
            #nt_result = namedtuple('Result', [col[0] for col in desc])

            jsonStr = json.dumps(query_results)

            if(jsonStr == []):
                return JsonResponse({ 'data': 'empty'}, safe=False)
            return JsonResponse(jsonStr, safe=False)

            #return render(request, 'hello_world.html', {'query_results': query_results})

        # return row

        # return render(request, 'hello_world.html', {'objs':query_results})