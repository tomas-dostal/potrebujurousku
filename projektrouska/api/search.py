import json
from django.http import JsonResponse
from django.db import connection


# TODO Pokud bude ve výsledku query dva řádky, které se budou
# lišit pouze v tom, že jeden je nuts a obecmesto je
# null a druhý že je nuts a obecmesto není null (pro uživatele vypadá jako
# dva stejné výsledky), tak smaž jeden z nich (asi ten NUTS)

def find_place_by_name(request):
    # misto, ktere hledam je ulozene v args
    args = request.GET.copy()
    mojemisto = str(args.get("misto", "Praha"))
    zobraz = len(mojemisto * 3)

    if (len(mojemisto) < 2):
        return

    qu = """select * from (
        SELECT null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, null as id_okres, null as nazev_okres,  nazev_kraj, id_kraj
        from kraj WHERE lower(nazev_kraj) LIKE lower('Pra%')

        union
        (
            SELECT null as id_obecmesto, null as nazev_obecmesto, id_nuts, nazev_nuts, id_okres, nazev_okres,  nazev_kraj, id_kraj from nuts3
            join okres on NUTS3_ID_NUTS=ID_NUTS
            join kraj on nuts3.kraj_id_kraj=kraj.id_kraj WHERE lower(nazev_nuts) LIKE lower('Pra%') -- TODO use bind varialbe

        )
        union
        (
            SELECT null as id_obecmesto, null as nazev_obecmesto, null as id_nuts, null as nazev_nuts, id_okres, nazev_okres,  nazev_kraj, id_kraj from okres
            join kraj on kraj_id_kraj=kraj.id_kraj WHERE lower(nazev_okres) LIKE lower('Pra%') -- TODO use bind varialbe
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
                                   WHERE lower(nazev_obecmesto) LIKE lower('Pra%') -- TODO use bind varialbe
                    ) join OKRES on OKRES.NUTS3_ID_NUTS=ID_NUTS

                ) join kraj using (id_kraj)
            )
        ) order by  nazev_obecmesto asc nulls first,  id_nuts asc nulls first, id_okres asc nulls first) where rownum <= 12
        """  # WHERE ROWNUM <= :zraz
    result = all(c.isalnum() or c.isspace() for c in mojemisto)

    if (not result):
        return JsonResponse(
            {'data': 'empty', 'invalid': 'Invalid character! Please stop injecting. Thank you'}, safe=False)

    with connection.cursor() as cursor:
        qu = qu.replace("Pra", str(mojemisto))
        cursor.execute(qu)

        from projektrouska.functions import return_as_array
        array = return_as_array(cursor.fetchall(), cursor.description)
        jsonStr = json.dumps(array)

        if (jsonStr == []):
            return JsonResponse({'data': 'empty'}, safe=False)
        return JsonResponse(jsonStr, safe=False)
        # except:
        #    print("Error occured")
