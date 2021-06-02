from bs4 import BeautifulSoup
import requests
from django.contrib.sessions.backends import db

from projektrouska.functions import return_as_array, return_as_dict
from django.db import connection, utils
from projektrouska.functions import return_as_array

from projektrouska.logger import Logger
from projektrouska.models import *

logger = Logger()


class UpdateCheck():

    def __init__(self):

        self.clear()

    def clear(self):
        # define some variables
        self.cathegories_url = [
            "https://koronavirus.mzcr.cz/category/mimoradna-opatreni/"]
        self.blacklist = []
        self.links_to_posts = []
        self.scrapping_results = None

        self.all = []
        self.up_to_date = []
        self.to_be_added = []
        self.to_be_removed = []
        self.to_be_changed_link = []
        self.to_be_modified = []

        self.to_be_reviewed = []  # todo: not implemented in the rest of app

        self.all_precautions_from_db = Precaution.objects.prefetch_related(
            "external_contents", "parts")

    def run(self):
        # set default values to variables
        self.clear()
        # first we need to fetch and scrapp all links of all posts from
        # self.cathegories_url
        self.scrap_content_from_links()

        # now its time to check if all scrapped links exists
        self.process_scrapped()

        # reults are saved in
        #         self.up_to_date = []
        #         self.to_be_added = []
        #         self.to_be_removed = []
        #         self.to_be_changed_link = []
        #         self.to_be_modified = []

        self.all = self.up_to_date \
                   + self.to_be_added \
                   + self.to_be_removed \
                   + self.to_be_changed_link \
                   + self.to_be_modified

    def add_to_list(self, list, dict_to_add):
        if dict_to_add not in list:
            return list.append(dict_to_add)
        else:
            return list

    # this one should be private
    def scrap_posts_links(self, cathegory_url):
        """
        :param cathegory_url: string of source URL address with wordpress
        thumbnails posts like
        "https://koronavirus.mzcr.cz/category/mimoradna-opatreni/"
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
                    self.links_to_posts.append(
                        link_to_detail.find("a")["href"])
                next_page = soupData.find(
                    "a", attrs={"class": "next page-numbers"})

                if next_page is not None:
                    page = requests.get(next_page["href"])
                else:
                    break
            i += 1

    def fetch_all_links(self):
        self.links_to_posts = []
        for cathegory_url in self.cathegories_url:
            self.scrap_posts_links(cathegory_url)

    def scrap_content_from_links(self):

        self.fetch_all_links()

        # open link and start scrapping
        self.scrapping_results = []

        for link in self.links_to_posts:
            detail_page_soup = BeautifulSoup(
                requests.get(link).content, "html.parser")

            article_posts = detail_page_soup.find_all(
                "article", attrs={"class": "post"})

            for article_post in article_posts:
                # every item here contains at least one entry like this
                """
                <div class="wp-block-file">
                    <a aria-label="soubor PDF – Nařízení Krajské hygienické
                    stanice Karlovarského kraje č. 4.2020 s účinností
                    od 5. 10. 2020"  title="soubor PDF – Nařízení Krajské
                    hygienické stanice Karlovarského kraje
                    č. 4.2020 s účinností od 5. 10. 2020"
                    href="https...8D.-4.2020.pdf"
                    class="link-file">
                    Nařízení Krajské hygienické stanice Karlovarského kraje č.
                     4.2020 s&nbsp;účinností od 5.&nbsp;10.&nbsp;2020</a>
                    <a aria-label="soubor PDF – Stáhnout"
                    title="soubor PDF – Stáhnout" href="https://korona...0.pdf"
                    class="wp-block-file__button" download="">Stáhnout
                    </a>
                    </div>
                """

                try:

                    lines = article_post.find(
                        attrs={
                            "class": "entry"}).find_all(
                        attrs={
                            "class": "wp-block-file"})
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
                        self.__name__ +
                        "Somethig went wrong, maybe 'wp-block-file'\
                         or something like that not found")
                    try:
                        text = article_post.find(
                            attrs={"class": "entry"}).find("a")["title"]
                        link = article_post.find(
                            attrs={"class": "entry"}).find("a")["href"]
                        logger.error(
                            "Trying to find at least something: \
                            Text: {}, link {}".format(text, link)
                        )
                        self.scrapping_results.append(
                            {
                                "name": text.replace("\xa0", " "),
                                "link": link.replace("\xa0", " "),
                            }
                        )

                    except Exception:
                        logger.error(
                            "Scrapper: Unable to find text and/or link")

        # now remove duplicates. Not very fast, but works
        tmp = []
        for item in self.links_to_posts:
            if item not in tmp:
                tmp.append(item)
        self.links_to_posts = tmp

        return

    def remove_from_db(self, id: int, link: str):
        logger.log("(re)moving OPATRENI ID={} - url= {}".format(id, link))

        # I don't really want to delete it, just set as "inactive"
        # Precaution.objects.filter(id=id).delete()
        try:
            p = self.all_precautions_from_db.get(id=id)
            p.status = Precaution.DISABLED_AUTO
            p.save()
            return True
        except Exception as e:
            logger.error(e)
            return False

    def process_scrapped(self):
        """
        Checks how many items from given array of dicts is up-to-date
        :param to_check: Array of dictinoaries like:
        [{nazev: value, odkaz: value},
        {nazev: value, odkaz: value}, ...]
        :return:  Returns
        {"aktualni": array of up-to-date items,
        "smazali": array of to-delete items,
        "zmena": array of to-change items,
        "chybi": array of missing items }

        """
        for res in self.scrapping_results:
            self.add_if_not_exists(name=res["name"], link=res["link"])
        return

    def add_if_not_exists(self, name, link):
        """
        Check if {nazev: value, odkaz: value} already exists in database.
         If not exists, it is added to the db.

        :param link: url you want to add of not exists
        :param name: name you want to add of not exists
        :param dictionary: Dict of {nazev: value, odkaz: value} which is
        checked if already exists in the database
        :return: 1 if already exists; 2 if pending for update;
         0 if not exists (+ adds to the database)
        """

        # ---- case 1 - matching both ----

        global item
        res = self.all_precautions_from_db.filter(
            external_contents__url_external__exact=link).filter(
            full_name__exact=name).all()

        for item in res:
            d = {
                "ID_OPATRENI": item.id,
                "NAZEV_OPATRENI": name,
                # pls work
                "STARY_ODKAZ": item.external_contents.all()[0].url_external,
                "ZDROJ": link,
                "PRECAUTION": item
            }

            if item.status in [
                Precaution.CHECK_REQUIRED,
                Precaution.MAINTENANCE_IN_PROGRESS]:
                logger.log(
                    "Ceka na zpracovani (kod {}) nazev: {}, link: {}".format(
                        item.status, name, link))
                self.to_be_reviewed.append(d)

            elif item.status in [Precaution.ENABLED_AUTO,
                                 Precaution.FORCE_ENABLE]:
                logger.log(
                    "Uz je v db, aktivni (kod {}) "
                    "id: {}  nazev: {}, link: {}".format(
                        item.status, item.id, name, link))
                self.up_to_date.append(d)

            elif item.status in [Precaution.FORCE_DISABLE,
                                 Precaution.DISABLED_AUTO]:
                logger.log(
                    "Uz je v db, neaktivni (kod {}) "
                    "id: {}  nazev: {}, link: {}".format(
                        item.status, item.id, name, link))
                # self.to_be_removed.append(d)

        if len(res) > 0:
            return

        # ---- case 2 - matching one of {name, link} ----

        matching_link = self.all_precautions_from_db.filter(
            external_contents__url_external__exact=link)
        matching_name = self.all_precautions_from_db.filter(
            full_name__exact=name)
        intersection = matching_link & matching_name

        matching_name_only = intersection.difference(matching_name)
        matching_link_only = intersection.difference(matching_link)

        if matching_name_only.all().count() > 0:

            for precaution in matching_name.all():
                prec_link = precaution.external_contents.all()[0].url_external
                self.to_be_changed_link.append(
                    {
                        "ID_OPATRENI": precaution.id,
                        "NAZEV_OPATRENI": name,
                        "STARY_ODKAZ": prec_link,
                        "ZDROJ": link,
                        "PRECAUTION": precaution
                    }
                )
                logger.log(
                    "Zmena odkazu (id {}) \
                nazev: {}, link: {} , novylink {}".format(
                        item.id,
                        name,
                        link,
                        precaution.external_contents.all()[0].url_external))

        if matching_link_only.all().count() > 0:
            pass

        # ---- case 3 - matching none of {name, link} ----

        if (matching_link | matching_name).all().count() == 0:
            self.to_be_added.append(
                {
                    "ID_OPATRENI": None,
                    "NAZEV_OPATRENI": name,
                    "STARY_ODKAZ": None,
                    "ZDROJ": link,
                    "PRECAUTION": None

                }
            )

            short_name = (
                name.replace("Krajské ", "K")
                    .replace("hygienické stanice", "HS")
                    .replace(" se sídlem", "")
                    .replace("s účinností ", "")
                    .replace("-", " ")
            )
            short_name = short_name[:250]

            p = Precaution(
                full_name=name,
                short_name=short_name,
                status=Precaution.ENABLED_AUTO,
                created_date=datetime.datetime.now().replace(tzinfo=utc)
            )
            p.save()

            type = ExternalContent.GENERAL
            if "pdf" in link or "PDF" in link:
                type = ExternalContent.PDF

            e = ExternalContent(
                date_inserted=datetime.datetime.now().replace(tzinfo=utc),
                content_type=type,
                preview=False,
                url_external=link
            )
            logger.log(
                "Přidat (id {}) nazev: {}, novylink {}".format(
                    p.id, name, link))

            e.save()

            p.external_contents.add(e)
            p.save()
