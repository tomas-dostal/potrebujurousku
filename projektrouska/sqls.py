from datetime import datetime, timedelta
from django.db import connection
from django.db.models import Max

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

    :return: {
                "data": {key: value ... as one line from db
                "is_outdated": True pokud poslední úspěšná kontrola proběhla před méně jak 60 minutami,
                "last_check_datetime": datetime poslední úspěné kontroly
                "last_check_timespan": delta od poslední úspěné kontroly
                "last_check_timespan_str": delta od poslední úspěné kontroly (string)
            }
    """

    """ data columns
     dict_keys(['id', 'checksum', 'date_updated', 'comment', 'up_to_date_percents',
                            'missing_count', 'missing_json', 'change_link_count',
                            'change_link_json', 'outdated_count', 'outdated_json', 'total_changes'])
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
    :return: Datum a čas nejnovější změny z některé z tabulek {POLOZKA, OPATRENI}
    """
    lst = [Precaution.objects.latest('modified_date').modified_date,
           Parts.objects.latest('modified_date').modified_date]
    return max(filter(lambda x: x is not None, lst)) if any(lst) else None


# TODO: Work in progress
def opatreni_stat():
    """
    Vybere všechny OPATRENI navázané na stát (OP_STAT),
        které:
            + mají OPATRENI.PLATNOST = 1
            + a zároveň mají blížící se začátek platnosti (OPATRENI.PLATNOST_OD
                (zobrazují se na :zobrazit_dopredu dní dopředu))

    Výsledek spojí s tabulkou POLOZKA a tabulkou KATEGORIE

    """

    display_within = datetime.datetime.now() + datetime.timedelta(days=7)

    precautions = State.objects.get(pk=1).precaution_set.filter(
        valid_from__lte=display_within.replace(tzinfo=None),
        valid_to__lte=datetime.datetime.now().replace(tzinfo=None),
        status__gt=0)

    test = model_to_dict(precautions)

    precautions = precautions.all().prefetch_related("parts")

    array = []
    for p in precautions:

        p.parts.all()
        precautions_external = p.external_contents.all()
        precautions_pes = p.pes_history_set.values()

        for part in p.parts.all():
            part_external = []
            if part.external_contents:
                part_external = part.external_contents.values()
            cathegory = part.cathegory

    newlist = sorted(array, key=lambda k: k['priorita'])

    cursor = connection.cursor()
    # do not look here, it looks much worse than before, I'll do my best to use models instead
    """ 
    select * from (
        select * from (
                      select *
                      from (
                               select *
                               from (
                                        select *
                                        from (
                                                 select *
                                                 from (select precaution_id
                                                       from precaution_state
                                                       where state_id = 1
                                                      ) as pr
                                                          join precaution on precaution.id = pr.precaution_id
                                             ) as prec
                                                 join precaution_parts using (precaution_id)
                                    ) as pa
                                        join part on part.id = pa.parts_id
                           ) as parts
    
                               join cathegory on cathegory.id = cathegory_id
                  ) as pwp
        join precaution_external_contents using (precaution_id)
        )  as pre
    join external_content on public.external_content.id=pre.externalcontent_id

    """
    qu = """select * from (
                select * from (
                      select * from (
                               -- stat
                               select distinct null as nazev_obecmesto,
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
                                               nazev_autooprava,
                                               CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO
    
                               from (
                                        select *
                                        from OP_STAT
                                                 join OPATRENI using (id_opatreni)
                                        where (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null)
                                          and trunc(sysdate) >= PLATNOST_OD - :zobrazit_dopredu
                                          and je_platne = 1
                                    )
                           )
                               join polozka on id_opatreni = opatreni_id_opatreni
                  )
                      join kategorie on kategorie.id_kategorie = kategorie_id_kategorie)
        order by PRIORITA_ZOBRAZENI asc, PLATNOST_OD desc, NAZEV asc, TYP desc;"""
    with connection.cursor() as cursor:
        cursor.execute(qu, {"zobrazit_dopredu": DNI_DOPREDU})
        array = return_as_array(cursor.fetchall(), cursor.description)
        location = {}
        return display_by_cath(array), location


def opatreni_nuts(id_nuts):
    """
    Vybere všechny OPATRENI navázané na obce s rozšířenou působností  (OP_NUTS) / okres (OP_OKRES) / kraj (OP_KRAJ) / stát (OP_STAT),
        které:
            + mají OPATRENI.PLATNOST = 1
            + a zároveň mají blížící se začátek platnosti (OPATRENI.PLATNOST_OD
                (zobrazují se na :zobrazit_dopredu dní dopředu))

    Výsledek spojí s tabulkou POLOZKA a tabulkou KATEGORIE


    :type id_nuts: ID obce s rozšířenou působností z tabulky NUTS3.ID_NUTS
    """
    qu = """select * from
           (
               select * from (
               -- Vybere všechny OPATRENI navázané územní platností na NUTS3 (OP_NUTS)
               select  null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni,nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava, CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO from (
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
    
               -- Vybere všechny OPATRENI navázané územní platností na OKRES (OP_OKRES)
               select  null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava, CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO   from
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
               -- Vybere všechny OPATRENI navázané územní platností na KRAJ (OP_KRAJ)
               select null as nazev_obecmesto, nazev_nuts, nazev_okres,  nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava, CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO from
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
               -- Vybere všechny celostátní OPATRENI (OP_STAT)
               union
               select null as nazev_obecmesto, null as nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava, CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO from (
               select * from OP_STAT join OPATRENI using(id_opatreni) where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                   )
    
           ) join polozka on opatreni_id_opatreni = id_opatreni
       ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by PRIORITA_ZOBRAZENI asc, PLATNOST_OD desc, NAZEV asc, TYP desc"""

    misto_qu = """select null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj from (
                 select * from (
                              select ID_NUTS, NAZEV_NUTS, KRAJ_ID_KRAJ as id_kraj from nuts3 where ID_NUTS=:id_nuts
                     )join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS
                   ) join kraj using(id_kraj);"""

    with connection.cursor() as cursor:
        cursor.execute(qu, {"id_nuts": id_nuts, "zobrazit_dopredu": DNI_DOPREDU})
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
    qu = """ select * from (
            select * from
            (
                select * from
                (
                    -- Vybere všechny OPATRENI navázané územní platností na KRAJ (OP_KRAJ)
                    select null as nazev_obecmesto, null as nazev_nuts, null as  nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava, CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO  from
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
                    -- Vybere všechny celostátní OPATRENI (OP_STAT)
                    select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava, CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO  from (
                    select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                    )


                ) join polozka on id_opatreni=opatreni_id_opatreni
            ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie) order by PRIORITA_ZOBRAZENI asc, PLATNOST_OD desc, NAZEV asc, TYP desc"""
    misto_qu = """select null as nazev_obecmesto, null as nazev_nuts, null as nazev_okres, nazev_kraj from (
              select * from kraj  where id_kraj=:id_k) """

    with connection.cursor() as cursor:
        cursor.execute(qu, {"id_k": id_kraj, "zobrazit_dopredu": DNI_DOPREDU})
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
    qu = """select * from (
                  select * from (
                          -- Vybere všechny OPATRENI navázané územní platností na OKRES (OP_OKRES)
                          select  null as nazev_obecmesto, null as  nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni,nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava, CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO from (

                              select * from
                              (
                                  select * from OKRES  where ID_OKRES = :id_okr
                              ) join kraj on kraj.id_kraj=KRAJ_ID_KRAJ
                              join op_okres on op_okres.okres_id_okres=id_okres
                              )
                          join opatreni on opatreni_id_opatreni=opatreni.id_opatreni   where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                          union

                          -- Vybere všechny OPATRENI navázané územní platností na KRAJ (OP_KRAJ)
                          select null as nazev_obecmesto, null as  nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava, CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO from (
                          select * from (
                                  select * from
                                  (
                                      select * from OKRES  where ID_OKRES = :id_okr
                                  ) join op_kraj using(KRAJ_ID_KRAJ)
                              ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                              ) join kraj on KRAJ_ID_KRAJ=kraj.id_kraj

                          union

                          -- Vybere všechny celostátní OPATRENI (OP_STAT)
                          select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,  ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava, CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO from
                         (
                          select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                         )

                          ) join polozka on id_opatreni=opatreni_id_opatreni
                      ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by PRIORITA_ZOBRAZENI asc, PLATNOST_OD desc, NAZEV asc, TYP desc"""

    misto_qu = """select distinct null as nazev_obecmesto, null as nazev_nuts, nazev_okres, nazev_kraj from (
                               select * from (
                                        select *
                                        from okres
                                        where ID_OKRES = :id_okr
                                    )join kraj on kraj.id_kraj = KRAJ_ID_KRAJ
                              );"""

    with connection.cursor() as cursor:
        cursor.execute(qu, {"id_okr": id_okres, "zobrazit_dopredu": DNI_DOPREDU})
        array = return_as_array(cursor.fetchall(), cursor.description)

        cursor.execute(misto_qu, {"id_okr": id_okres})
        location = return_as_dict(cursor.fetchone(), cursor.description)
        return display_by_cath(array), location


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
    qu = """
       select * from (
         select * from (
                        -- Vybere všechny OPATRENI navázané územní platností na OBECMESTO (OP_OM)
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
                                      nazev_autooprava,
                                      CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO
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
                        -- Vybere všechny OPATRENI navázané územní platností na obec s rozšřenou působností NUTS3 (OP_NUTS)
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
                                      nazev_autooprava,
                                      CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO
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
                        -- Vybere všechny OPATRENI navázané územní platností na OKRES (OP_OKRES)
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
                                      nazev_autooprava,
                                      CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO
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
                        -- Vybere všechny OPATRENI navázané územní platností na KRAJ (OP_KRAJ)

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
                                      nazev_autooprava,
                                      CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO
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

                        -- Vybere všechny celostatni OPATRENI (OP_STAT)
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
                                      nazev_autooprava,
                                      CASE WHEN ((PLATNOST_DO) <= (trunc(sysdate) + :zobrazit_dopredu)) OR (PLATNOST_DO  <= (PLATNOST_OD + :zobrazit_dopredu)) THEN 1 ELSE 0 END AS MAM_ZOBRAZOVAT_DO
                               from (
                                        select *
                                        from OP_STAT
                                                 join OPATRENI using (id_opatreni)
                                        where (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null)
                                          and trunc(sysdate) >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                                    )
                           )
               )join polozka on id_opatreni=opatreni_id_opatreni
              join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by PRIORITA_ZOBRAZENI asc, PLATNOST_OD desc, NAZEV asc, TYP desc ;"""
    misto_qu = """select nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj from (
               select * from (
                        select * from (
                            select * from obecmesto where id_obecmesto=:id_ob
                            ) join nuts3 on nuts3_id_nuts = nuts3.id_nuts
                   )join OKRES on OKRES.NUTS3_ID_NUTS = ID_NUTS
                 ) join kraj on kraj.id_kraj=nuts3_kraj_id_kraj;"""
    with connection.cursor() as cursor:
        cursor.execute(qu, {"id_ob": id_obecmesto, "zobrazit_dopredu": DNI_DOPREDU})
        array = return_as_array(cursor.fetchall(), cursor.description)

        cursor.execute(misto_qu, {"id_ob": id_obecmesto})
        location = return_as_dict(cursor.fetchone(), cursor.description)

        return display_by_cath(array), location
