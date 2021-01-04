import json
from django.http import JsonResponse
from projektrouska.models import City, State, Region, District, Nuts4
from itertools import chain

def find_place_by_name(request):
    # misto, ktere hledam je ulozene v args
    args = request.GET.copy()
    query_string = str(args.get("misto", "Praha"))

    if (len(query_string) < 2):
        return

    states = State.objects.filter(name__istartswith=query_string)

    regions = Region.objects.filter(name__istartswith=query_string)
    districts = District.objects.filter(name__istartswith=query_string)
    nuts4 = Nuts4.objects.filter(name__istartswith=query_string)
    cities = City.objects.filter(name__istartswith=query_string)

    results = list(chain([s.place_as_dict for s in list(states)],
                         [r.place_as_dict for r in list(regions)],
                         [d.place_as_dict for d in list(districts)],
                         [n.place_as_dict for n in list(nuts4)],
                         [c.place_as_dict for c in list(cities)]))

    jsonStr = json.dumps(results)

    if (jsonStr == []):
        return JsonResponse({'data': 'empty'}, safe=False)
    return JsonResponse(jsonStr, safe=False)
