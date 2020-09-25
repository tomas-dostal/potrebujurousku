import hashlib

def format_num(number):
    import locale
    locale.setlocale(locale.LC_ALL, '')
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
    :param description:  value of cursor.description
    :return: return dictionary of tuples {desc[0]: data[0], desc[1]: data[1]}
    """
    desc = description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
    columns = []
    for col in desc:
        columns.append(col[0])
    dict = {}
    i = 0
    for row in data:
        dict[columns[i]] = row
        i += 1
    return dict

def calcmd5(string):
    # initializing string
    str2hash = string
    # encoding GeeksforGeeks using encode()
    # then sending to md5()
    result = hashlib.md5(str2hash.encode())

    # printing the equivalent hexadecimal value.
    return (result.hexdigest())
