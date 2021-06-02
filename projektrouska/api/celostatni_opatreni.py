from django.core.serializers import json
from django.http import JsonResponse
from django.db import connection
from projektrouska.sqls import opatreni_stat


def celostatni_opatreni(request):
    array = opatreni_stat()[0]

    if (not array):
        return JsonResponse({'data': 'empty'},
                            safe=False)

    else:
        from django.core.serializers.json import DjangoJSONEncoder
        dum = json.dumps(
            {"data": array},
            sort_keys=True,
            indent=1,
            cls=DjangoJSONEncoder)

        return JsonResponse(dum, safe=False)
