from django.db import connection

from projektrouska.functions import return_as_dict, return_as_array, calcmd5, format_num


def posledni_kontrola():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                *
            FROM
                (select * from INFO order by DATE_UPDATED desc )
            WHERE
                rownum <= 1;"""
        )
        dict = return_as_dict(cursor.fetchone(), cursor.description)
        print(dict)
        return dict


def posledni_databaze():
    with connection.cursor() as cursor:
        last_qu = """select max(posledni_uprava) from(
                       SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from polozka
                       union
                       SELECT SCN_TO_TIMESTAMP(MAX(ora_rowscn)) as posledni_uprava from opatreni)"""
        cursor.execute(last_qu)
        last_update = cursor.fetchone()
        return last_update[0]
