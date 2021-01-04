import json
from django.http import JsonResponse
from projektrouska.models import City, State, Region, District, Nuts4


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

    merged = list(states) + list(regions) + list(districts) + list(nuts4) + list(cities)

    json_str = json.dumps([place.place_as_dict() for place in merged])

    if json_str == "[]":
        return JsonResponse({'data': 'empty'}, safe=False)
    return JsonResponse(json_str, safe=False)
