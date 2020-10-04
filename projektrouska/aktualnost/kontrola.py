from bs4 import BeautifulSoup
from datetime import datetime

import requests
import time
import datetime
from projektrouska.functions import return_as_array, return_as_dict

fetched = 0
from django.db import connection

from projektrouska.settings import DEV
blacklist = ["https://eregpublicsecure.ksrzis.cz/jtp/public/ExterniZadost?s=ISIN_SOC"]


def check_in_db(tmp):
    out = ""
    aktualni = []
    chybi = []
    smazali_je = []
    zmena_odkazu = []

    print("Kotrnoluju soubor déky {}: \n{}".format(len(tmp), str(tmp)))
    # na jednom linku muze byt i vice narizeni, tak projed pro kazde
    for o in tmp:
        out += o["nazev"]
        if( o["odkaz"] in blacklist):
            continue # skip this

        with connection.cursor() as cursor:

            cursor.execute("""select * from opatreni where NAZEV_OPATRENI = :nazev or ZDROJ=:link and  PLATNOST_AUTOOPRAVA = null;""",
                           {"nazev": o["nazev"], "link": o["odkaz"]})
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
                chybi.append({"nazev": o["nazev"], "odkaz": o["odkaz"]})
                add_to_db(o) # await?

            else:  # něco takoveho v databazi je (bud sedi odkaz, nebo sedi nazev, nebo oboje)

                for i in query_results:
                    zdroj_server = i[columns.index("ZDROJ")]
                    # pokud je na serveru shoda okazu a zaroven je pocet_odkazu > 1, tak ignoruj chybu zmeny odkazu!

                    # Nazev je v DB, link se zmenil
                    if (zdroj_server != o["odkaz"] and o["pocet_odkazu"] <= 1):
                        if (DEV == True):
                            print(
                                "Opatření {} nalezeno, ID={}, změnil se odkaz. \nPůvodní:  {} \nAktuální: {}".format(
                                    o["nazev"],
                                    i[columns.index("ID_OPATRENI")],
                                    zdroj_server,
                                    o["odkaz"]))
                        to_add = {"ID_OPATRENI": i[columns.index("ID_OPATRENI")],
                                             "NAZEV_OPATRENI": o["nazev"],
                                             "STARY_ODKAZ": zdroj_server,
                                             "ZDROJ": o["odkaz"]}
                        if(to_add not in zmena_odkazu):
                            zmena_odkazu.append(to_add)

                    # Nazev i link jsou aktualni, necht je to tedy aktualni cele
                    else:

                        aktualni.append({"ID_OPATRENI": i[columns.index("ID_OPATRENI")],
                                         "NAZEV_OPATRENI": o["nazev"],
                                         "ZDROJ": o["odkaz"]})

    return {"aktualni": aktualni, "smazali": smazali_je, "zmena":  zmena_odkazu, "chybi":  chybi}

def add_to_db(dictionary):

    with connection.cursor() as cursor:
        cursor.execute("""select * from opatreni where (NAZEV_OPATRENI = :nazev or ZDROJ=:link) and PLATNOST_AUTOOPRAVA != 2;""",
                       {"nazev": dictionary["nazev"], "link": dictionary["odkaz"]})
        query_results = cursor.fetchall()
        desc = cursor.description  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta

        db_contains = return_as_array(query_results, desc)

        cursor.execute("""select max(id_opatreni) as MAX_ID from opatreni;""")

        # Meh. Next time I'll use autoincrement when creating a db. Sorry guys!
        max_id = int(return_as_dict(cursor.fetchone(),  cursor.description)["MAX_ID"])

        if(len(db_contains) > 0):
            print("Asi spatne oznacene, v databazi uz '{}' je".format(dictionary))
        else:
            "Mimořádné opatření Krajské hygienické stanice Zlínského kraje se sídlem ve Zlíně č. 3/2020"
            nazev_zkr = dictionary["nazev"].replace("Krajské ", "K").replace("hygienické stanice", "HS").replace(" se sídlem", "")


            cursor.execute('''insert into opatreni (id_opatreni, nazev_opatreni, platnost_od, je_platne, 
            zdroj, nazev_zkr, rozsah, platnost_do, zdroj_autooprava, 
            priorita, identifikator, platnost_autooprava, nazev_autooprava) 
            values   (
                     :id_opatreni,
                     :nazev_opatreni, 
                     null,  -- platnost_od
                     2,    -- je_platne
                     :zdroj, 
                     :nazev_zkr, 
                     null, -- rozsah
                     null, -- platnost_do 
                     null, -- zdroj_autooprava
                     0, -- priorita
                     null, -- identifikator
                     2, -- platnost_autooprava
                     null -- nazev_autooprava
                     )''', {"id_opatreni": max_id + 1,
                           "nazev_opatreni": dictionary["nazev"],
                           "zdroj": dictionary["odkaz"],
                           "nazev_zkr": nazev_zkr})

            cursor.execute('''commit;''')


def get_links_of_posts(cathegory_url):
    next_page = True
    links_of_posts = []

    # starting page with cathegories
    page = requests.get(cathegory_url)      #"https://koronavirus.mzcr.cz/category/mimoradna-opatreni/")
    print("Getting links")
    i = 1
    # scrap links of all to articles of the cathegory.
    while (next_page != None):
        print("[Getting links] page: {}".format(i))
        soupData = BeautifulSoup(page.content, 'html.parser')
        article = soupData.find_all('article', attrs={'class': 'post'})

        for a in article:
            link_to_detail = a.find(attrs={'class': 'moreLink'})
            links_of_posts.append(link_to_detail.find('a')["href"])

            next_page = soupData.find('a', attrs={'class': 'next page-numbers'})

            if (next_page is not None):
                page = requests.get(next_page["href"])
            else:
                break
        i += 1
    return links_of_posts


def start():
    cathegories_url = ['https://koronavirus.mzcr.cz/category/mimoradna-opatreni/']
    links_of_posts = []
    for cathegory_url in cathegories_url:
        links = get_links_of_posts(cathegory_url)
        links_of_posts[len(links_of_posts):len(links)] = links

    # open link and start scrapping
    results = []
    for link in links_of_posts:
        detail_page_soup = BeautifulSoup(requests.get(link).content, 'html.parser')

        article_posts = detail_page_soup.find_all('article', attrs={'class': 'post'})

        for article_post in article_posts:
            # every item here contains at least one entry like this
            """
            <div class="wp-block-file">
                <a aria-label="soubor PDF – Nařízení Krajské hygienické stanice Karlovarského kraje č. 4.2020 s účinností od 5. 10. 2020" 
                title="soubor PDF – Nařízení Krajské hygienické stanice Karlovarského kraje č. 4.2020 s účinností od 5. 10. 2020" 
                href="https://koronavirus.mzcr.cz/wp-content/uploads/2020/10/Na%C5%99%C3%ADzen%C3%AD-Krajsk%C3%A9-hygienick%C3%A9-stanice-Karlovarsk%C3%A9ho-kraje-%C4%8D.-4.2020.pdf" 
                class="link-file">
                Nařízení Krajské hygienické stanice Karlovarského kraje č. 4.2020 s&nbsp;účinností od 5.&nbsp;10.&nbsp;2020</a>
                <a aria-label="soubor PDF – Stáhnout" 
                title="soubor PDF – Stáhnout" href="https://koronavirus.mzcr.cz/wp-content/uploads/2020/10/Na%C5%99%C3%ADzen%C3%AD-Krajsk%C3%A9-hygienick%C3%A9-stanice-Karlovarsk%C3%A9ho-kraje-%C4%8D.-4.2020.pdf" class="wp-block-file__button" download="">Stáhnout
                </a>
                </div>
            """

            try:

                lines = article_post.find(attrs={'class': 'entry'}).find_all(attrs={'class': 'wp-block-file'})
                for line in lines:
                    text = line.find('a').text
                    link = line.find('a')["href"]
                    print("Text: {}, link {}".format(text, link))
                    results.append({'nazev': text.replace('\xa0', ' '), 'odkaz': link.replace('\xa0', ' ')})

            except:
                print("Somethig fucked up")
                try:
                    text = article_post.find(attrs={'class': 'entry'}).find('a')['title']
                    link = article_post.find(attrs={'class': 'entry'}).find('a')["href"]
                    print("FUCKED UP Text: {}, link {}".format(text, link))
                    results.append({'nazev': text.replace('\xa0', ' '), 'odkaz': link.replace('\xa0', ' ')})

                except:
                    print("Somethig fucked up a lot")
    return check_in_db(results)


