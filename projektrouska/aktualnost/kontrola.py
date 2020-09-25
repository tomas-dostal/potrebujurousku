import requests
from bs4 import BeautifulSoup

fetched = 0
from django.db import connection

from projektrouska.settings import DEV


def scrappni_link(link):
    global fetched
    fetched += 1
    subpage = requests.get(link)
    soupsubpage = BeautifulSoup(subpage.content, 'html.parser')
    # print(soup.prettify())

    ret = []
    for i in soupsubpage.find("article").find_all("a"):
        odkaz = i["href"]
        nazev_op = i.contents[0]

        nazev_op =i.attrs["title"].replace("soubor PDF – ", "")
        if (len(nazev_op.split("-")) > 3):
            nazev_op = soupsubpage.find("article").find_all("h1")[0].string

        publikovano = soupsubpage.find(class_="entryDate").text

        ret.append({'nazev': nazev_op, 'odkaz': odkaz, "publikovano": publikovano, "pocet_odkazu": len(soupsubpage.find("article").find_all("a"))})

        if(DEV == True):
            print("{}: {}".format(fetched, nazev_op))

    # print("Nazev: \n{} Publikovano: \n{}\nOdkaz: \n{}\n".format(nazev_op, publikovano, odkaz))
    return ret

    #return "Nazev: \n{} Publikovano: \n{}\nOdkaz: \n{}\n".format(nazev_op, publikovano, odkaz)
    # return nazev_op,  publikovano,  odkaz


def start():
    page = requests.get("https://koronavirus.mzcr.cz/mapa-webu/")
    soup = BeautifulSoup(page.content, 'html.parser')

    # print(soup.prettify())
    out = ""

    aktualni = []
    chybi = []
    smazali_je = []
    zmena_odkazu = []
    global fetched
    fetched = 0
    kategorie = soup.select('#page > div > ul.wsp-posts-list > li:nth-child(1) > ul')
    for k in kategorie[0].contents:
        try:
            for i in k:
                # print(i.attrs["href"])

                tmp = {}
                tmp = scrappni_link(i.attrs["href"])

                # na jednom linku muze byt i vice narizeni, tak projed pro kazde
                for o in tmp:
                    out += o["nazev"]
                    with connection.cursor() as cursor:

                        cursor.execute("""select * from opatreni where NAZEV_OPATRENI = :nazev or ZDROJ=:link;""", {"nazev": o["nazev"].replace('\xa0', ' '), "link": o["odkaz"].replace('\xa0', ' ')})
                        # vysledek bude plus minus
                        # <class 'tuple'>: ('NAZEV_OBECMESTO', 'NAZEV_NUTS', 'NAZEV_KRAJ', 'ID_OPATRENI', 'NAZEV_OPATRENI', 'NAZEV_ZKR', 'ZDROJ', 'PLATNOST_OD', 'ID_POLOZKA', 'NAZEV', 'KOMENTAR', 'KATEGORIE_ID_KATEGORIE', 'TYP', 'OPATRENI_ID_OPATRENI', 'ID_KATEGORIE', 'NAZEV_KAT', 'KOMENT_KATEGORIE')

                        query_results = cursor.fetchall()
                        desc = cursor.description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
                        columns = []
                        for col in desc:
                            columns.append(col[0])

                        if (len(query_results) == 0):
                            if (DEV == True):
                                print("Opatření '{}' není v databázi".format(o["nazev"]))
                            chybi.append({"nazev": o["nazev"].replace('\xa0', ' '), "odkaz": o["odkaz"]})

                        else: # něco takoveho v databazi je (bud sedi odkaz, nebo sedi nazev, nebo oboje)

                            for i in query_results:
                                zdroj_server = i[columns.index("ZDROJ")]
                                # pokud je na serveru shoda okazu a zaroven je pocet_odkazu > 1, tak ignoruj chybu zmeny odkazu!



                                # Nazev je v DB, link se zmenil
                                if (zdroj_server != o["odkaz"] and o["pocet_odkazu"] <= 1):
                                    if (DEV == True):
                                        print(
                                        "Opatření {} nalezeno, ID={}, změnil se odkaz. \nPůvodní:  {} \nAktuální: {}".format(
                                            o["nazev"].replace('\xa0', ' '),
                                            i[columns.index("ID_OPATRENI")],
                                            zdroj_server,
                                            o["odkaz"]))

                                    zmena_odkazu.append({"ID_OPATRENI": i[columns.index("ID_OPATRENI")],
                                                         "NAZEV_OPATRENI": o["nazev"].replace('\xa0', ' '),
                                                         "STARY_ODKAZ": zdroj_server,
                                                         "ZDROJ": o["odkaz"]})

                                # Nazev i link jsou aktualni, necht je to tedy aktualni cele
                                else:

                                    aktualni.append({"ID_OPATRENI": i[columns.index("ID_OPATRENI")],
                                                     "NAZEV_OPATRENI": o["nazev"].replace('\xa0', ' '),
                                                     "ZDROJ": o["odkaz"]})

                # print(i.attrs["aria-label"])
        except AttributeError:
            pass
    with connection.cursor() as cursor:

        # Ted potrebuju zkontrolovat opatreni, ktere jsou v databazi, ale uz je stahli z internetu
        cursor.execute("""select * from opatreni""")
        query_results = cursor.fetchall()
        desc = cursor.description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
        columns = []
        for col in desc:
            columns.append(col[0])

        id_v_databazi = []
        for a in aktualni:
            id_v_databazi.append(a.get("ID_OPATRENI"))
        for z in zmena_odkazu:
            """NAZEV_OPATRENI": tmp["nazev"],
                 "STARY_ODKAZ": i[columns.index("ZDROJ")],
                 "ZDROJ": tmp["odkaz"]})"""
            try:
                print("Zkousim aktualizaci databaze")

                cursor.execute("""UPDATE OPATRENI 
                    SET ZDROJ_AUTOOPRAVA = :link
                    WHERE ID_OPATRENI = :id ;""",
                               {"id": z.get("ID_OPATRENI"), "link": z.get("ZDROJ")})
                #cursor.fetchall
                cursor.execute("""COMMIT;""")
                if (DEV == True):
                    print("Update databaze se POVEDLA")


            except Exception as e:
                id_v_databazi.append(z.get("ID_OPATRENI"))
                if (DEV == True):
                    print(e)
                    print("Update databaze se nezdaril")

        # ted bych mel mit vsechna IDcka co jsou v databazi a maji tam byt v id_v_databazi

        for i in query_results:
            if (i[columns.index("ID_OPATRENI")] not in id_v_databazi and i[columns.index("JE_PLATNE")] > 0):
                # bylo stazeno z webu, TODO deaktivuj

                try:
                    cursor.execute("""UPDATE OPATRENI 
                                SET PLATNOST_AUTOOPRAVA = 0--, JE_PLATNE = 2
                                WHERE ID_OPATRENI = :id ;""",
                                   {"id": i[columns.index("ID_OPATRENI")]})
                    # cursor.fetchall
                    cursor.execute("""COMMIT;""")

                except Exception as e:
                    if (DEV == True):
                        print(e)

                        print("Update databaze se nezdaril")

                smazali_je.append({"ID_OPATRENI": i[columns.index("ID_OPATRENI")],
                                   "NAZEV_OPATRENI": i[columns.index("NAZEV_OPATRENI")],
                                   "ZDROJ": i[columns.index("ZDROJ")]})
                print("Opatření ID={}, '{}' bylo z webu ministerstva odstraneno. \nOdkaz: {}".format(
                    i[columns.index("ID_OPATRENI")],
                    i[columns.index("NAZEV_OPATRENI")],
                    i[columns.index("ZDROJ")]
                ))

    return {"aktualni": aktualni, "chybi": chybi, "smazali": smazali_je, "zmena": zmena_odkazu}

