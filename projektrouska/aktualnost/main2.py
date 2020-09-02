import requests
from bs4 import BeautifulSoup, NavigableString
import re
import difflib
from pathlib import Path

import argparse
import difflib
import sys

fetched = 0
from django.db import connection


def scrappni_link(link):
    global fetched
    fetched += 1
    subpage = requests.get(link)
    soupsubpage = BeautifulSoup(subpage.content, 'html.parser')
    # print(soup.prettify())

    odkaz = soupsubpage.find("article").find_all("a")[0]["href"]
    nazev_op = soupsubpage.find("article").find_all("a")[0].contents[0]

    nazev_op = soupsubpage.find("article").find_all("a")[0].attrs["title"].replace("soubor PDF – ", "")
    if(len(nazev_op.split("-")) > 3):
        nazev_op = soupsubpage.find("article").find_all("h1")[0].string

    if (nazev_op == 'Mimořádné opatření organizace a provádění karantény u zdravotnických pracovníků'):
        print("jsemtoja")


    publikovano = soupsubpage.find(class_="entryDate").text
    print("{}: {}".format(fetched, nazev_op))

    # print("Nazev: \n{} Publikovano: \n{}\nOdkaz: \n{}\n".format(nazev_op, publikovano, odkaz))
    return {'nazev': nazev_op, 'odkaz': odkaz, "publikovano": publikovano}

    #return "Nazev: \n{} Publikovano: \n{}\nOdkaz: \n{}\n".format(nazev_op, publikovano, odkaz)
    # return nazev_op,  publikovano,  odkaz


def stahni():
    page = requests.get("https://koronavirus.mzcr.cz/mapa-webu/")
    soup = BeautifulSoup(page.content, 'html.parser')

    # print(soup.prettify())
    out = ""

    aktualni = []
    chybi = []
    smazali_je = []
    zmena_odkazu = []

    kategorie = soup.select('#page > div > ul.wsp-posts-list > li:nth-child(1) > ul')
    for k in kategorie[0].contents:
        try:
            for i in k:
                # print(i.attrs["href"])
                tmp = {}
                tmp = scrappni_link(i.attrs["href"])
                out += tmp["nazev"]
                with connection.cursor() as cursor:

                    cursor.execute("""select * from opatreni where NAZEV_OPATRENI = :nazev or ZDROJ=:link;""", {"nazev": tmp["nazev"].replace('\xa0', ' '), "link": tmp["odkaz"].replace('\xa0', ' ')})
                    # vysledek bude plus minus
                    # <class 'tuple'>: ('NAZEV_OBECMESTO', 'NAZEV_NUTS', 'NAZEV_KRAJ', 'ID_OPATRENI', 'NAZEV_OPATRENI', 'NAZEV_ZKR', 'ZDROJ', 'PLATNOST_OD', 'ID_POLOZKA', 'NAZEV', 'KOMENTAR', 'KATEGORIE_ID_KATEGORIE', 'TYP', 'OPATRENI_ID_OPATRENI', 'ID_KATEGORIE', 'NAZEV_KAT', 'KOMENT_KATEGORIE')

                    query_results = cursor.fetchall()
                    desc = cursor.description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta
                    columns = []
                    for col in desc:
                        columns.append(col[0])

                    if (len(query_results) == 0):
                        print("Opatření '{}' není v databázi".format(tmp["nazev"]))
                        chybi.append({"nazev": tmp["nazev"].replace('\xa0', ' '), "odkaz": tmp["odkaz"]})
                    else:

                        for i in query_results:
                            zdroj_server = i[columns.index("ZDROJ")]

                            # Nazev je v DB, link se zmenil
                            if (zdroj_server != tmp["odkaz"]):
                                print(
                                    "Opatření {} nalezeno, ID={}, změnil se odkaz. \nPůvodní:  {} \nAktuální: {}".format(
                                        tmp["nazev"].replace('\xa0', ' '),
                                        i[columns.index("ID_OPATRENI")],
                                        zdroj_server,
                                        tmp["odkaz"]))

                                zmena_odkazu.append({"ID_OPATRENI": i[columns.index("ID_OPATRENI")],
                                                     "NAZEV_OPATRENI": tmp["nazev"].replace('\xa0', ' '),
                                                     "STARY_ODKAZ": zdroj_server,
                                                     "ZDROJ": tmp["odkaz"]})

                            # Nazev i link jsou aktualni, necht je to tedy aktualni cele
                            else:

                                aktualni.append({"ID_OPATRENI": i[columns.index("ID_OPATRENI")],
                                                 "NAZEV_OPATRENI": tmp["nazev"].replace('\xa0', ' '),
                                                 "ZDROJ": tmp["odkaz"]})

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
            """"NAZEV_OPATRENI": tmp["nazev"],
                 "STARY_ODKAZ": i[columns.index("ZDROJ")],
                 "ZDROJ": tmp["odkaz"]})"""
            try:
                print("Zkousim aktualizaci databaze")

                cursor.execute("""UPDATE OPATRENI 
                    SET ZDROJ_AUTOOPRAVA = :link
                    WHERE ID_OPATRENI = :id ;
                    commit;""",
                               {"id": z.get("ID_OPATRENI"), "link": z.get("ZDROJ")})
                cursor.fetchall
                cursor.execute("""commit;""",
                               {"id": z.get("ID_OPATRENI"), "link": z.get("ZDROJ")})
                print("Update databaze se POVEDLA")


            except Exception as e:
                id_v_databazi.append(z.get("ID_OPATRENI"))
                print(e)

                print("Update databaze se nezdaril")

        # ted bych mel mit vsechna IDcka co jsou v databazi a maji tam byt v id_v_databazi

        for i in query_results:
            if (i[columns.index("ID_OPATRENI")] not in id_v_databazi and i[columns.index("JE_PLATNE")] > 0):
                # bylo stazeno z webu, TODO deaktivuj
                smazali_je.append({"ID_OPATRENI": i[columns.index("ID_OPATRENI")],
                                   "NAZEV_OPATRENI": i[columns.index("NAZEV_OPATRENI")],
                                   "ZDROJ": i[columns.index("ZDROJ")]})
                print("Opatření ID={}, '{}' bylo z webu ministerstva odstraneno. \nOdkaz: {}".format(
                    i[columns.index("ID_OPATRENI")],
                    i[columns.index("NAZEV_OPATRENI")],
                    i[columns.index("ZDROJ")]
                ))

    return {"aktualni": aktualni, "chybi": chybi, "smazali": smazali_je, "zmena": zmena_odkazu}


def main():
    return stahni()

if __name__ == "__main__":
    main()
