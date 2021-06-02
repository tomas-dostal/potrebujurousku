import datetime
import json
from django.http import JsonResponse
from django.db import connection
from pytz import utc
from django.core.serializers.json import DjangoJSONEncoder

from projektrouska.models import UpdateLogs
from django.db.models import Min


def get_stats(show_from=None, show_last_days=31):
    # qu = '''
    #    select * from(
    #    select min(DATE_UPDATED) as DATE_UPDATED, CHECKSUM, POZNAMKA, AKTUALNOST,
    #    CHYBI_POCET, CHYBI_POLE, ZMENA_LINK_POCET, ZMENA_LINK_POLE, ODSTRANIT_POCET,
    #    ODSTRANIT_POLE, CELK_ZMEN from info
    #    group by CHECKSUM, POZNAMKA, AKTUALNOST, CHYBI_POCET, CHYBI_POLE, ZMENA_LINK_POCET,
    #    ZMENA_LINK_POLE, ODSTRANIT_POCET, ODSTRANIT_POLE, CELK_ZMEN
    #    order by  DATE_UPDATED) where DATE_UPDATED >= trunc(sysdate)  - :old
    #    '''
    if not show_from:
        show_from = (datetime.datetime.now()
                     - datetime.timedelta(days=show_last_days)
                     - datetime.timedelta(seconds=10)).replace(tzinfo=utc)

    stats = UpdateLogs.objects.values(
        "checksum",
        "comment",
        "up_to_date_percents",
        "missing_count",
        # "missing_json",
        "change_link_count",
        # "change_link_json",
        "outdated_count",
        # "outdated_json",
        "total_changes").annotate(
        date_updated=Min('date_updated')).filter(date_updated__gte=show_from)

    return json.dumps(
        {
            "data": list(stats)
        },
        sort_keys=True,
        indent=1,
        cls=DjangoJSONEncoder
    )


def get_update_stats(request, show_from=None, show_last_days=31):
    args = request.GET.copy()

    try:
        days = int(args.get("days_old", "31"))
        show_from = datetime.datetime.now().replace(tzinfo=utc) - datetime.timedelta(days=days)
    except ValueError:  # bad request
        return JsonResponse({'error': 'bad request. Optional parameters: "days_old"'}, safe=False)

    if not show_from:
        show_from = datetime.datetime.now().replace(tzinfo=utc) \
                    - datetime.timedelta(days=show_last_days)

    return JsonResponse(get_stats(show_from), safe=False)


def get_all_update_stats(request):
    args = request.GET.copy()

    min_date = UpdateLogs.objects.aggregate(Min('date_updated'))

    return get_update_stats(request, min_date)
