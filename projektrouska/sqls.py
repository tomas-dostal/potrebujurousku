from datetime import datetime, timedelta

from django import db
from django.db import connection

from projektrouska.functions import (
    return_as_dict,
    return_as_array,
    # calcmd5,
    # format_num,
    strfdelta,
    display_by_cath,
)

# urcuje v horizontu kolika dni se maji zobrazovat nadchazející opatreni
DNI_DOPREDU = 7


def posledni_kontrola():
    """
    :return: DICT: Nejnovější záznam z tabulky INFO (všechny sloupce) {"CHECKSUM": "value", "DATE_UPDATED": "value" ... }
    """
    with connection.cursor() as cursor:
        query = """select * from (select * from INFO order by DATE_UPDATED desc) where rownum <= 1;"""
        cursor.execute(query)
        dictionary = return_as_dict(cursor.fetchone(), cursor.description)
        return dictionary


# TODO: Nějak rozumně přejmenovat?
def posledni_databaze():
    """

    :return: Datum a čas nejnovější změny z některé z tabulek {POLOZKA, OPATRENI}
    """
    with connection.cursor() as cursor:
        last_qu = """select max(posledni_uprava) from(
                       SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from polozka
                       union
                       SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from opatreni);"""
        try:

            cursor.execute(last_qu)
            last_update = cursor.fetchone()[0]
        except db.utils.DatabaseError:
            # something went wrong. Maybe just a db went down, maybe (more likely) we've just reached SCN_TO_TIMESTAMP
            # conversion limit, which is something like 5 days (https://stackoverflow.com/questions/22681705/how-to-use-timestamp-to-scn-and-scn-to-timestamp-in-oracle)
            # We were just too lazy and did not inserted anything to the db...
            # Possible solution: Insert a row to POLOZKA and OPATRENI to bypass that LOL
            # better solution: Just give there try - catch, or pass

            """
            insert into OPATRENI(ID_OPATRENI, NAZEV_OPATRENI, PLATNOST_OD, JE_PLATNE, ZDROJ, NAZEV_ZKR, ROZSAH, PLATNOST_DO, ZDROJ_AUTOOPRAVA, IDENTIFIKATOR, PLATNOST_AUTOOPRAVA, NAZEV_AUTOOPRAVA)
            values (99999, 'Nazev', trunc(sysdate), 1, 'asdf', '', null, null, null, null, 42, null);
            commit;
            delete from OPATRENI
            where ID_OPATRENI=99999 and PLATNOST_AUTOOPRAVA=42;
            commit;

            insert into POLOZKA(ID_POLOZKA, NAZEV, KOMENTAR, KATEGORIE_ID_KATEGORIE, TYP, OPATRENI_ID_OPATRENI, VYJIMKA, EXTRA_LINK, EXTRA_POPIS, MODAL_SIZE, ICON)
            values (99999, 'nazev', 'komentar', 1, '42', 100, null, null, null, 'modal-lg', null);
            commit;
            delete from POLOZKA
            where ID_POLOZKA=99999 and TYP='42';
            commit;
            """

            last_qu = """select 'před nějakou dobou'  as posledni_uprava from dual"""
            # other option is
            # last_qu = """select  trunc(sysdate)  as posledni_uprava from dual"""

            cursor.execute(last_qu)
            last_update = cursor.fetchone()[0]
        return last_update


def zastarala_data():
    """
    Automaticky co cca 5 min probíhá kontrola aktuálnosti.

    :return: {
                "zastarala_data": True pokud poslední úspěšná kontrola proběhla před méně jak 60 minutami,
                "posledni_uspesna_kontrola_timespan": delta od poslední úspěné kontroly (string)
            }

    """
    posledni_datetime = posledni_kontrola()["DATE_UPDATED"]
    naposledy_provedeno = datetime.now() - posledni_datetime
    str_naposledy = strfdelta(
        naposledy_provedeno, "{days} dny, {hours} hodinami {minutes} minutami"
    )  # {seconds} vteřinami
    if (datetime.now() - posledni_datetime) < timedelta(minutes=60):
        return {
            "zastarala_data": False,
            "posledni_uspesna_kontrola_timespan": str_naposledy,
        }
    return {
        "zastarala_data": True,
        "posledni_uspesna_kontrola_timespan": str_naposledy}


def opatreni_stat():
    """
    Vybere všechny OPATRENI navázané na stát (OP_STAT),
        které:
            + mají OPATRENI.PLATNOST = 1
            + a zároveň mají blížící se začátek platnosti (OPATRENI.PLATNOST_OD
                (zobrazují se na :zobrazit_dopredu dní dopředu))

    Výsledek spojí s tabulkou POLOZKA a tabulkou KATEGORIE

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
        cursor.execute(
            qu, {
                "id_nuts": id_nuts, "zobrazit_dopredu": DNI_DOPREDU})
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
        cursor.execute(
            qu, {
                "id_okr": id_okres, "zobrazit_dopredu": DNI_DOPREDU})
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
        cursor.execute(qu, {"id_ob": id_obecmesto,
                            "zobrazit_dopredu": DNI_DOPREDU})
        array = return_as_array(cursor.fetchall(), cursor.description)

        cursor.execute(misto_qu, {"id_ob": id_obecmesto})
        location = return_as_dict(cursor.fetchone(), cursor.description)

        return display_by_cath(array), location
