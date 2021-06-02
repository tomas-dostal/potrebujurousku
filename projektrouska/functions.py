import hashlib


def format_num(number):
    import locale

    locale.setlocale(locale.LC_ALL, "")
    return str(locale.format_string("%d", number, grouping=True)).replace(" ", "&nbsp;")


def return_as_array(data, description):
    """

    :param data: return value of  cursor.execute.fetchall (multiple rows only!)
    :param description:  value of cursor.description
    :return: return array of dics  of [{desc[0]: data[0], desc[1]: data[1],...},  {desc[0]: data[0], desc[1]: data[1],...},...]
    """
    desc = description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
    columns = []
    for col in desc:
        columns.append(col[0])
    array = []
    for row in data:
        array.append(return_as_dict(row, description))
    return array


def return_as_dict(data, description):
    """
    :param data: return value of  cursor.execute.fetchone (single row only!)
    example:
        ('355e8aa9b2f3d0be96a75b028815c80a', datetime.datetime(2020, 10, 24, 22, 54), 'Všechna data jsou aktuální!', 100, 0, '[]', 0, '[]', 0, '[]', 0, 41825)

    :param description:  value of cursor.description
    example:
        [('CHECKSUM', <cx_Oracle.DbType DB_TYPE_VARCHAR>, 50, 50, None, None, 1), ('DATE_UPDATED', <cx_Oracle.DbType DB_TYPE_DATE>, 23, None, None, None, 1), ('POZNAMKA', <cx_Oracle.DbType DB_TYPE_VARCHAR>, 500, 500, None, None, 1), ('AKTUALNOST', <cx_Oracle.DbType DB_TYPE_NUMBER>, 39, None, 38, 0, 1), ('CHYBI_POCET', <cx_Oracle.DbType DB_TYPE_NUMBER>, 39, None, 38, 0, 0), ('CHYBI_POLE', <cx_Oracle.DbType DB_TYPE_VARCHAR>, 4000, 4000, None, None, 1), ('ZMENA_LINK_POCET', <cx_Oracle.DbType DB_TYPE_NUMBER>, 39, None, 38, 0, 1), ('ZMENA_LINK_POLE', <cx_Oracle.DbType DB_TYPE_VARCHAR>, 4000, 4000, None, None, 1), ('ODSTRANIT_POCET', <cx_Oracle.DbType DB_TYPE_NUMBER>, 39, None, 38, 0, 1), ('ODSTRANIT_POLE', <cx_Oracle.DbType DB_TYPE_VARCHAR>, 4000, 4000, None, None, 1), ('CELK_ZMEN', <cx_Oracle.DbType DB_TYPE_NUMBER>, 39, None, 38, 0, 1), ('ID', <cx_Oracle.DbType DB_TYPE_NUMBER>, 39, None, 38, 0, 0)]

    :return: return dictionary of tuples {desc[0]: data[0], desc[1]: data[1]}
    """
    columns = [column[0] for column in description]
    dictionary = {}
    if data:
        for i in range(len(data)):
            dictionary[columns[i]] = data[i]
    else:
        for column in columns:
            dictionary[column] = None

    return dictionary


def calcmd5(string):
    # initializing string
    str2hash = string
    # encoding GeeksforGeeks using encode()
    # then sending to md5()
    result = hashlib.md5(str2hash.encode())

    # printing the equivalent hexadecimal value.
    return result.hexdigest()


# source: https://stackoverflow.com/questions/8906926/formatting-timedelta-objects
def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def display_by_cath(array):
    by_cath = []
    existing = []
    for col in array:
        if "NAZEV_KAT" in col:
            # fajn, ted zkontroluju, jestli uz jsem to vypsal, nebo ne
            if col["NAZEV_KAT"] in existing:
                by_cath[len(by_cath) - 1]["narizeni"].append(col)
            else:
                existing.append(col["NAZEV_KAT"])
                tmp = {"kategorie": col["NAZEV_KAT"], "narizeni": [col]}
                by_cath.append(tmp)

    return by_cath
