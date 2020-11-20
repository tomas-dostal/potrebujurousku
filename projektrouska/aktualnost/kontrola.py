from bs4 import BeautifulSoup
import requests
from django.contrib.sessions.backends import db

from projektrouska.functions import return_as_array, return_as_dict
from django.db import connection, utils
from projektrouska.functions import return_as_array

from projektrouska.logger import Logger

logger = Logger()


class Update_check():

    def __init__(self):
        self.clear()

    def clear(self):
        self.db_localcopy = None

        # define some variables
        self.cathegories_url = ["https://koronavirus.mzcr.cz/category/mimoradna-opatreni/"]
        self.blacklist = ["https://eregpublicsecure.ksrzis.cz/jtp/public/ExterniZadost?s=ISIN_SOC"]
        self.links_to_posts = []
        self.scrapping_results = None

        self.all = []
        self.up_to_date = []
        self.to_be_added = []
        self.to_be_removed = []
        self.to_be_changed_link = []
        self.to_be_modified = []

        self.to_be_reviewed = []  # todo: not implemented in the rest of app

    def run(self):
        # set default values to variables
        self.clear()
        # first we need to fetch and scrapp all links of all posts from self.cathegories_url
        self.scrap_content_from_links()

        self.fetch_db()
        # now its time to check if all scrapped links exists
        self.check()

        # reults are saved in
        #         self.up_to_date = []
        #         self.to_be_added = []
        #         self.to_be_removed = []  # todo, not checked
        #         self.to_be_changed_link = []
        #         self.to_be_modified = []

        self.add_all_to_db(self.to_be_added)

        self.check_if_can_be_removed()

        self.remove_redundant_from_db(self.to_be_removed)

    def add_to_list(self, list, dict_to_add):
        if dict_to_add not in list:
            return list.append(dict_to_add)
        else:
            return list

    # this one should be private
    def scrap_posts_links(self, cathegory_url):
        """
        :param cathegory_url: string of source URL address with wordpress posts thumbnails like "https://koronavirus.mzcr.cz/category/mimoradna-opatreni/"
        :return: list of direct URLs to posts
        """
        next_page = True
        self.links_to_posts = []

        # starting page with cathegories
        page = requests.get(
            cathegory_url
        )  # "https://koronavirus.mzcr.cz/category/mimoradna-opatreni/")
        logger.log("Getting links")
        i = 1
        # scrap links of all to articles of the cathegory.
        while next_page is not None:
            logger.log("[Getting links] page: {}".format(i))
            soupData = BeautifulSoup(page.content, "html.parser")
            article = soupData.find_all("article", attrs={"class": "post"})

            for a in article:
                link_to_detail = a.find(attrs={"class": "moreLink"})

                if link_to_detail.find("a")["href"] not in self.links_to_posts:
                    self.links_to_posts.append(link_to_detail.find("a")["href"])
                next_page = soupData.find("a", attrs={"class": "next page-numbers"})

                if next_page is not None:
                    page = requests.get(next_page["href"])
                else:
                    break
            i += 1

    # this one should be private

    def fetch_all_links(self):
        self.links_to_posts = []
        for cathegory_url in self.cathegories_url:
            self.scrap_posts_links(cathegory_url)
            # links = self.scrap_posts_links(cathegory_url)  # get links of posts
            # self.links_of_posts[
            # len(self.links_of_posts): len(links)] = links  # append all links of posts scrapped this run
        return

    def scrap_content_from_links(self):

        self.fetch_all_links()

        # open link and start scrapping
        self.scrapping_results = []

        for link in self.links_to_posts:
            detail_page_soup = BeautifulSoup(requests.get(link).content, "html.parser")

            article_posts = detail_page_soup.find_all("article", attrs={"class": "post"})

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

                    lines = article_post.find(attrs={"class": "entry"}).find_all(
                        attrs={"class": "wp-block-file"}
                    )
                    for line in lines:
                        text = line.find("a").text
                        link = line.find("a")["href"]
                        logger.log("Text: {}, link {}".format(text, link))
                        dict = \
                            {
                                "name": text.replace("\xa0", " "),
                                "link": link.replace("\xa0", " "),
                            }
                        if dict not in self.scrapping_results:
                            self.scrapping_results.append(dict)

                except Exception:
                    logger.error(
                        self.__name__ + "Somethig went wrong, maybe 'wp-block-file' or something like that not found"
                    )
                    try:
                        text = article_post.find(attrs={"class": "entry"}).find("a")[
                            "title"
                        ]
                        link = article_post.find(attrs={"class": "entry"}).find("a")["href"]
                        logger.error(
                            "Trying to find at least something: Text: {}, link {}".format(
                                text, link
                            )
                        )
                        self.scrapping_results.append(
                            {
                                "name": text.replace("\xa0", " "),
                                "link": link.replace("\xa0", " "),
                            }
                        )

                    except Exception:
                        logger.error("Scrapper: Unable to find text and/or link")

        # now remove duplicates. Not very fast, but works
        tmp = []
        for item in self.links_to_posts:
            if item not in tmp:
                tmp.append(item)
        self.links_to_posts = tmp

        return

    def check_if_can_be_removed(self):
        for item in self.db_localcopy:
            if item not in self.all:
                self.to_be_removed.append(item)

    def fetch_db(self):

        # If I put this in try-catch, it would run slower. There is no "backup" option, so
        # we are screwed anyway.
        try:
            with connection.cursor() as cursor:

                cursor.execute(
                    """select * from DOSTATO6.OPATRENI order by ID_OPATRENI desc"""
                )
                self.db_localcopy = return_as_array(description=cursor.description, data=cursor.fetchall())
        except:
            logger.error("DB communication error")

        finally:  # maybe it is ok and still exitst
            connection.close()

    def remove_from_db(self, id: int, link: str):
        logger.log("(re)moving OPATRENI ID={} - url= {}".format(id, link))
        try:
            with connection.cursor() as cursor:
                sql = """SELECT * from DOSTATO6.OPATRENI
                                WHERE (ID_OPATRENI=:id_opatreni and ZDROJ=:zdroj)
                                """
                cursor.execute(sql, {"id_opatreni": id, "zdroj": link})
                """r = return_as_dict(data=cursor.fetchone, description=cursor.description)

                if(r["JE_PLATNE"] == 0)
                    # Lets consider it as removed
                    return True
                """

                sql = """UPDATE DOSTATO6.OPATRENI
                        SET --JE_PLATNE=0,
                         PLATNOST_AUTOOPRAVA=0
                    WHERE (ID_OPATRENI=:id_opatreni and ZDROJ=:zdroj)
                    """
                cursor.execute(sql, {"id_opatreni": id, "zdroj": link})

                try:
                    sql = """INSERT INTO DOSTATO6.OPATRENI_STARE(ID_OPATRENI, NAZEV_OPATRENI, PLATNOST_OD, JE_PLATNE, ZDROJ, NAZEV_ZKR, ROZSAH, PLATNOST_DO, ZDROJ_AUTOOPRAVA, IDENTIFIKATOR, PLATNOST_AUTOOPRAVA, NAZEV_AUTOOPRAVA)
                        SELECT ID_OPATRENI, NAZEV_OPATRENI, PLATNOST_OD, JE_PLATNE, ZDROJ, NAZEV_ZKR, ROZSAH, PLATNOST_DO, ZDROJ_AUTOOPRAVA, IDENTIFIKATOR, PLATNOST_AUTOOPRAVA, NAZEV_AUTOOPRAVA
                            FROM DOSTATO6.OPATRENI WHERE ID_OPATRENI = :id_opatreni
                        """
                    cursor.execute(sql, {"id_opatreni": id})
                except db.IntegrityError as e:
                    logger.error(str(e))
                    pass

                sql = """commit"""

                # better not to delete it directly
                # cursor.execute(sql)
                # cursor.execute("""SELECT * from DOSTATO6.OPATRENI_STARE WHERE ID_OPATRENI=:id_opatreni""", {"id_opatreni": id})
                # check if changes were really made and if I can find row in OPATRENI_STARE to "safely" remove it from "OPATRENI"
                # if(return_as_dict(data=cursor.fetchone(), description=cursor.description)["ID_OPATRENI"]):
                #    cursor.execute("""DELETE from DOSTATO6.OPATRENI WHERE ID_OPATRENI=:id_opatreni""",
                #                   {"id_opatreni": id})
                #    cursor.execute("COMMIT")
                logger.log("Success")
                return True

        except Exception as e:
            logger.error(e)
            return False

        finally:  # maybe it is ok and still exitst
            connection.close()

    def is_in_db(self, name, link):

        if not self.db_localcopy:
            self.fetch_db()

        for line in self.db_localcopy:
            if line["NAZEV_OPATRENI"] == name or line[
                "ZDROJ"] == link:  # It is in the db, just check details and cathegorize

                if line["NAZEV_OPATRENI"] == name and line["ZDROJ"] != link:

                    self.to_be_changed_link.append(
                        {
                            "ID_OPATRENI": line["ID_OPATRENI"],
                            "NAZEV_OPATRENI": name,
                            "STARY_ODKAZ": line["ZDROJ"],
                            "ZDROJ": link
                        }
                    )
                    self.all.append(line)  # to be able to figure out which ones are redundant

                    logger.log(
                        "Opatření {} nalezeno, ID={}, změnil se odkaz. \nPůvodní:  {} \nAktuální: {}".format(
                            name,
                            line["ID_OPATRENI"],
                            line["ZDROJ"],
                            link
                        )
                    )
                    return

                # ok, lets skip situation when link remains same, but name is modified, it happends

                # Need to fix this one in db
                elif line["PLATNOST_AUTOOPRAVA"] == 2:
                    self.to_be_modified.append(
                        {
                            "ID_OPATRENI": line["ID_OPATRENI"],
                            "NAZEV_OPATRENI": name,
                            "STARY_ODKAZ": line["ZDROJ"],
                            "ZDROJ": link
                        }
                    )
                    self.all.append(line)  # to be able to figure out which ones are redundant

                    return

                # Pending review
                elif line["PLATNOST_AUTOOPRAVA"] == 3:
                    self.to_be_reviewed.append(
                        {
                            "ID_OPATRENI": line["ID_OPATRENI"],
                            "NAZEV_OPATRENI": name,
                            "STARY_ODKAZ": line["ZDROJ"],
                            "ZDROJ": link
                        }
                    )
                    self.all.append(line)  # to be able to figure out which ones are redundant

                    return

                # Up-to-date
                else:
                    self.up_to_date.append(
                        {
                            "ID_OPATRENI": line["ID_OPATRENI"],
                            "NAZEV_OPATRENI": name,
                            "STARY_ODKAZ": line["ZDROJ"],
                            "ZDROJ": link
                        }
                    )
                    self.all.append(line)  # to be able to figure out which ones are redundant

                    return
            else:
                pass

        # missing - to be added to our db
        self.to_be_added.append(
            {
                "NAZEV_OPATRENI": name,
                "ZDROJ": link
            }
        )

        return

    def check(self):
        """
        Checks how many items from given array of dicts is up-to-date
        :param to_check: Array of dictinoaries like: [{nazev: value, odkaz: value}, {nazev: value, odkaz: value}, ...]
        :return:  Returns {"aktualni": array of up-to-date items, "smazali": array of to-delete items, "zmena": array of to-change items, "chybi": array of missing items}

        """
        for item in self.scrapping_results:
            self.is_in_db(name=item["name"], link=item["link"])
        return

    def add_to_db(self, name, link):
        """
        Check if {nazev: value, odkaz: value} already exists in database. If not exists, it is added to the db.

        :param dictionary: Dict of {nazev: value, odkaz: value} which is checked if already exists in the database
        :return: 1 if already exists; 2 if pending for update; 0 if not exists (+ adds to the database)
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """select * from DOSTATO6.OPATRENI where (NAZEV_OPATRENI = :nazev or ZDROJ = :odkaz) order by PLATNOST_AUTOOPRAVA;""",
                {"nazev": name, "odkaz": link},
            )
            query_results = cursor.fetchall()
            desc = (
                cursor.description
            )  # pouzivam dale, kde se z techle dat dela neco jako slovnik, co uz django schrousta

            db_contains = return_as_array(query_results, desc)

            if len(db_contains) > 0:  #

                if (
                        db_contains[0]["PLATNOST_AUTOOPRAVA"] == 2
                        or db_contains[0]["PLATNOST_AUTOOPRAVA"] == 0
                ):
                    logger.log("Ceka na zpracovani nazev: {}, link: {}".format(name, link))
                    return 2
                elif db_contains[0]["PLATNOST_AUTOOPRAVA"] == None:
                    logger.log("Uz je v databazi, zpracovano  {}, link: {}".format(name, link))
                    return 1
                else:
                    logger.log("v DB uz je  {}, link: {}".format(name, link))
                    return 0

            else:
                cursor.execute("""select max(id_opatreni) as MAX_ID from opatreni;""")

                # Meh. Next time I'll use autoincrement when creating a db. Sorry guys!
                max_id = int(
                    return_as_dict(cursor.fetchone(), cursor.description)["MAX_ID"]
                )

                nazev_zkr = (
                    name
                        .replace("Krajské ", "K")
                        .replace("hygienické stanice", "HS")
                        .replace(" se sídlem", "")
                        .replace("s účinností ", "")
                        .replace("-", " ")
                )
                nazev_zkr = nazev_zkr[:250]

                cursor.execute(
                    """insert into opatreni (id_opatreni, nazev_opatreni, platnost_od, je_platne, 
                zdroj, nazev_zkr, rozsah, platnost_do, zdroj_autooprava, 
                priorita, identifikator, platnost_autooprava, nazev_autooprava)  values   ( :id_opatreni,
                         :nazev_opatreni, 
                         null,  -- platnost_od
                         2,    -- je_platne
                         :zdroj, 
                         :nazev_zkr, -- limit 250 chars
                         null, -- rozsah
                         null, -- platnost_do 
                         null, -- zdroj_autooprava
                         0, -- priorita
                         null, -- identifikator
                         2, -- platnost_autooprava
                         null -- nazev_autooprava
                         )""",
                    {
                        "id_opatreni": max_id + 1,
                        "nazev_opatreni": name,
                        "zdroj": link,
                        "nazev_zkr": nazev_zkr,
                    },
                )

                cursor.execute("""select * from DOSTATO6.OPATRENI where ID_OPATRENI=:id_opatreni""",
                               {
                                   "id_opatreni": max_id + 1,
                               }, )

                # add to "have in db" not to be marked as "to-remove"
                self.all.append(return_as_dict(data=cursor.fetchone(), description=cursor.description))

                cursor.execute("""commit;""")
        return 1

    def add_all_to_db(self, to_be_added: list):
        for item in to_be_added:
            self.add_to_db(item["NAZEV_OPATRENI"], item["ZDROJ"])

    def remove_redundant_from_db(self, to_be_removed):

        v = [self.remove_from_db(id=to_remove["ID_OPATRENI"], link=to_remove["ZDROJ"]) for to_remove in to_be_removed]
        logger.log("remove_redundant_from_db: " + str(v))
        # self.to_be_removed = []

        return
