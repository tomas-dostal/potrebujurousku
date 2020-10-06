import json
from django.http import JsonResponse
from django.db import connection

def get_update_stats(request):
    args = request.GET.copy()
    show_last_days = 7
    try:
        show_last_days = int(args.get("days_old", "31"))
    except: # bad request
        return JsonResponse({'error': 'bad request. Optional parameters: "days_old"'}, safe=False)


    qu = '''
        select * from(
        select min(DATE_UPDATED) as DATE_UPDATED, CHECKSUM, POZNAMKA, AKTUALNOST, CHYBI_POCET, CHYBI_POLE, ZMENA_LINK_POCET, ZMENA_LINK_POLE, ODSTRANIT_POCET, ODSTRANIT_POLE, CELK_ZMEN from info
        group by CHECKSUM, POZNAMKA, AKTUALNOST, CHYBI_POCET, CHYBI_POLE, ZMENA_LINK_POCET, ZMENA_LINK_POLE, ODSTRANIT_POCET, ODSTRANIT_POLE, CELK_ZMEN
        order by  DATE_UPDATED) where DATE_UPDATED >= trunc(sysdate)  - :old
        '''
    with connection.cursor() as cursor:
        cursor.execute(qu, {"old": show_last_days})

        from projektrouska.functions import return_as_array
        array = return_as_array(cursor.fetchall(), cursor.description)
        #jsonStr = json.dumps(array)
        #if (jsonStr == []):
        #    return JsonResponse({'data': 'empty'}, safe=False)

        from django.core.serializers.json import DjangoJSONEncoder
        dum = json.dumps(
            {"data": array},
            sort_keys=True,
            indent=1,
            cls=DjangoJSONEncoder)

        return JsonResponse(dum, safe=False)
