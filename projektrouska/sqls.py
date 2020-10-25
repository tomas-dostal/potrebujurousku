from datetime import datetime, timedelta

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
    with connection.cursor() as cursor:
        query = """select * from (select * from INFO order by DATE_UPDATED desc) where rownum <= 1;"""
        cursor.execute(query)
        dictionary = return_as_dict(cursor.fetchone(), cursor.description)
        return dictionary


def posledni_databaze():
    with connection.cursor() as cursor:
        last_qu = """select max(posledni_uprava) from(
                       SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from polozka
                       union
                       SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from opatreni);"""
        cursor.execute(last_qu)
        last_update = cursor.fetchone()[0]
        return last_update


def zastarala_data():
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
    return {"zastarala_data": True, "posledni_uspesna_kontrola_timespan": str_naposledy}


def opatreni_stat():
    qu = """ select * from (
            select * from 
            (
                select * from
                (
                    -- stat 
                    select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava  from (
                    select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                    )


                ) join polozka on id_opatreni=opatreni_id_opatreni
            ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie) order by  PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc;"""
    with connection.cursor() as cursor:
        cursor.execute(qu, {"zobrazit_dopredu": DNI_DOPREDU})
        array = return_as_array(cursor.fetchall(), cursor.description)
        location = {}
        return display_by_cath(array), location


def opatreni_nuts(id_nuts):
    qu = """


                       select * from
                       (
                           select * from (


                           -- nuts3
                           select  null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni,nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava from (
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

                           -- okres
                           select  null as nazev_obecmesto, nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava   from
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
                           -- kraj
                           select null as nazev_obecmesto, nazev_nuts, nazev_okres,  nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava from
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
                           -- stat
                           union

                           select null as nazev_obecmesto, null as nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava from (
                           select * from OP_STAT join OPATRENI using(id_opatreni) where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                               )

                       ) join polozka on opatreni_id_opatreni = id_opatreni
                   ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by  PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc"""

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
    qu = """ select * from (
            select * from 
            (
                select * from
                (
                    -- kraj 
                    select null as nazev_obecmesto, null as nazev_nuts, null as  nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava  from 
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
                    -- stat 
                    select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava  from (
                    select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                    )


                ) join polozka on id_opatreni=opatreni_id_opatreni
            ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie) order by  PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc"""
    misto_qu = """select null as nazev_obecmesto, null as nazev_nuts, null as nazev_okres, nazev_kraj from (
              select * from kraj  where id_kraj=:id_k) """

    with connection.cursor() as cursor:
        cursor.execute(qu, {"id_k": id_kraj, "zobrazit_dopredu": DNI_DOPREDU})
        array = return_as_array(cursor.fetchall(), cursor.description)

        cursor.execute(misto_qu, {"id_k": id_kraj})
        location = return_as_dict(cursor.fetchone(), cursor.description)
        return display_by_cath(array), location


def opatreni_okres(id_okres):
    qu = """select * from (
                  select * from (
                         -- okres
                          select  null as nazev_obecmesto, null as  nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni,nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava  from (

                              select * from
                              (
                                  select * from OKRES  where ID_OKRES = :id_okr
                              ) join kraj on kraj.id_kraj=KRAJ_ID_KRAJ
                              join op_okres on op_okres.okres_id_okres=id_okres
                              )
                          join opatreni on opatreni_id_opatreni=opatreni.id_opatreni   where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                          union
                          -- kraj

                          select null as nazev_obecmesto, null as  nazev_nuts, nazev_okres, nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,   ROZSAH,  platnost_od , platnost_do , platnost_autooprava, zdroj_autooprava, nazev_autooprava from (
                          select * from (
                                  select * from
                                  (
                                      select * from OKRES  where ID_OKRES = :id_okr
                                  ) join op_kraj using(KRAJ_ID_KRAJ)
                              ) join opatreni on opatreni_id_opatreni=opatreni.id_opatreni  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                              ) join kraj on KRAJ_ID_KRAJ=kraj.id_kraj

                          union

                          select distinct null as nazev_obecmesto, null as  nazev_nuts, null as nazev_okres, null as nazev_kraj, id_opatreni, nazev_opatreni, nazev_zkr, zdroj,  ROZSAH,  platnost_od , platnost_do, platnost_autooprava, zdroj_autooprava, nazev_autooprava from
                         (
                          select * from OP_STAT join OPATRENI using(id_opatreni)  where  (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null) and  trunc(sysdate)  >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                         )

                          ) join polozka on id_opatreni=opatreni_id_opatreni
                      ) join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by  PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc"""
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
    qu = """
             select * from (
         select * from (
                               -- lokalni
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
                                      nazev_autooprava
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
                               -- nuts3
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
                                      nazev_autooprava
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
                               -- okres
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
                                      nazev_autooprava
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
                               -- kraj

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
                                      nazev_autooprava
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

                                    -- stat
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
                                      nazev_autooprava
                               from (
                                        select *
                                        from OP_STAT
                                                 join OPATRENI using (id_opatreni)
                                        where (trunc(sysdate) < PLATNOST_DO or PLATNOST_DO is null)
                                          and trunc(sysdate) >= PLATNOST_OD - :zobrazit_dopredu and je_platne=1
                                    )
                           )
               )join polozka on id_opatreni=opatreni_id_opatreni
              join kategorie on kategorie.id_kategorie=kategorie_id_kategorie order by PRIORITA_ZOBRAZENI asc, id_kategorie asc, TYP desc, PLATNOST_OD asc 
              """
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
