import hashlib


def vrat_seznam(data, description):
    """

    :param data: return value of  cursor.execute
    :param description:  value of cursor.description
    :return: return list of {desc[0]: data[0], desc[1]: data[1]}
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
    print(dict)
    return dict


def calcmd5(string):
    # initializing string
    str2hash = string
    # encoding GeeksforGeeks using encode()
    # then sending to md5()
    result = hashlib.md5(str2hash.encode())

    # printing the equivalent hexadecimal value.
    return (result.hexdigest())
