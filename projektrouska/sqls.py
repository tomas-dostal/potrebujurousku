from datetime import datetime, timedelta
from django.db import connection
from django.db.models import Max
from django.db.models import Q

from projektrouska.functions import (
    return_as_dict,
    return_as_array,
    strfdelta,
    display_by_cath,
)
from projektrouska.models import *
from django.forms.models import model_to_dict

# urcuje v horizontu kolika dni se maji zobrazovat nadchazející opatreni
HORIZONT = 7


def last_check():
    """
   Automaticky co cca 5 min probíhá kontrola aktuálnosti.

    :return:
    {
        "data": {key: value ... as one line from db
        "is_outdated": True pokud poslední úspěšná kontrola proběhla
                       před méně jak 60 minutami,
        "last_check_datetime": datetime poslední úspěné kontroly
        "last_check_timespan": delta od poslední úspěné kontroly
        "last_check_timespan_str":  delta od poslední úspěné kontroly (string)
    }
    """

    """ data columns
     dict_keys(['id', 'checksum', 'date_updated', 'comment',
          'up_to_date_percents', 'missing_count', 'missing_json',
          'change_link_count','change_link_json', 'outdated_count',
          'outdated_json', 'total_changes'])
    """
    if UpdateLogs.objects.values().count() > 0:
        data = UpdateLogs.objects.values().latest('date_updated')
        date = data["date_updated"]
        timespan = datetime.datetime.now() - date.replace(tzinfo=None)
        timespan_str = strfdelta(
            timespan, "{days} dny, {hours} hodinami {minutes} minutami")
        is_outdated = timespan > timedelta(minutes=60)
    else:
        data = None
        date = None
        timespan = None
        timespan_str = None
        is_outdated = True
    return {
        "data": data,
        "is_outdated": is_outdated,
        "last_check_datetime": date,
        "last_check_timespan": timespan,
        "last_check_timespan_str": timespan_str
    }


def last_modified_date():
    """
    :return: Latest modification date of one of {precaution, part}
    """
    lst = [Precaution.objects.latest('modified_date').modified_date,
           Parts.objects.latest('modified_date').modified_date]
    return max(filter(lambda x: x is not None, lst)) if any(lst) else None


def opatreni_stat(id=1):
    """
    Return all active parts ordered by category

    @:param id: select all (active only) precautions,parts from State id = id

    @:return [{category1: [parts1]}]
    """
    """

    p = Precaution.objects.annotate(
        order_priority=Max('parts__category__priority')).order_by('-order_priority')
    # select only those valid for state=1
    p = p.filter(state__id=1)

    # filter valid only
    p = p.filter(valid_from__lte=datetime.datetime.now().replace(tzinfo=utc),
                 # valid_to__gte=datetime.datetime.now(),
                 status__gt=0)
    """
    res = []

    for c in Category.objects.order_by("priority").all():
        parts = c.parts_set.filter(
            precaution__valid_from__lte=datetime.datetime.now().replace(
                tzinfo=utc),
            # precaution__valid_to__gte=datetime.datetime.now(),
            # uncomment to have right matching data displayed
            # precaution__status__gt=0,
            precaution__state__id=1).all()

        # TODO use select related
        parts = parts.prefetch_related(
            "precaution_set",
            "external_contents__part_set",
            "category")
        res.append({"category": c, "data": parts})

    return res


def opatreni_nuts(id_nuts):
    with connection.cursor() as cursor:
        cursor.execute(qu, {"id_nuts": id_nuts, "zobrazit_dopredu": HORIZONT})
        array = return_as_array(cursor.fetchall(), cursor.description)

        cursor.execute(misto_qu, {"id_nuts": id_nuts})
        location = return_as_dict(cursor.fetchone(), cursor.description)
        return display_by_cath(array), location


def opatreni_kraj(id_kraj):
    """
    Vybere všechny OPATRENI navázané na kraj (OP_KRAJ) / stát (OP_STAT),
        které:
            + mají OPATRENI.PLATNOST = 1
            + a zároveň mají blížící se začátek platnosti (OPATRENI.PLATNOST_OD
                (zobrazují se na :zobrazit_dopredu dní dopředu))

    Výsledek spojí s tabulkou POLOZKA a tabulkou KATEGORIE


    :type id_kraj: ID okraje z tabulky KRAJ.ID_KRAJ
    """
    p = Precaution.objects.annotate(
        order_priority=Max('parts__category__priority')).order_by('-order_priority')
    # select only those valid for state=1

    region = Region.objects.filter(id=id_kraj).all()[0]
    p = p.filter(Q(region__id=id_kraj) | Q(state__id=region.get_parent().id))

    # filter valid only
    p = p.filter(valid_from__lte=datetime.datetime.now().replace(tzinfo=utc),
                 # valid_to__gte=datetime.datetime.now(),
                 status__gt=0)

    

    with connection.cursor() as cursor:
        cursor.execute(qu, {"id_k": id_kraj, "zobrazit_dopredu": HORIZONT})
        array = return_as_array(cursor.fetchall(), cursor.description)

        cursor.execute(misto_qu, {"id_k": id_kraj})
        location = return_as_dict(cursor.fetchone(), cursor.description)
        return display_by_cath(array), location


def opatreni_okres(id_okres):
    """
    Vybere všechny OPATRENI navázané na okres (OP_OKRES) / kraj (OP_KRAJ) / stát (OP_STAT),
        které:
            + mají OPATRENI.PLATNOST = 1
            + a zároveň mají blížící se začátek platnosti (OPATRENI.PLATNOST_OD
                (zobrazují se na :zobrazit_dopredu dní dopředu))

    Výsledek spojí s tabulkou POLOZKA a tabulkou KATEGORIE


    :type id_okres: ID okresu z tabulky OKRES.ID_OKRES
    """


def opatreni_om(id_obecmesto):
    """
    Vybere všechny OPATRENI navázané na obecmesto (OP_OM) / obec s rozšířenou působností (OP_NUTS) / okres (OP_OKRES) / kraj (OP_KRAJ) / stát (OP_STAT),
        které:
            + mají OPATRENI.PLATNOST = 1
            + a zároveň mají blížící se začátek platnosti (OPATRENI.PLATNOST_OD
                (zobrazují se na :zobrazit_dopredu dní dopředu))

    Výsledek spojí s tabulkou POLOZKA a tabulkou KATEGORIE


    :type id_obecmesto: ID obce/města z tabulky OBECMESTO.ID_OBECMESTO
    """

