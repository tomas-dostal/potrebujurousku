import requests
from django.test import TestCase
from projektrouska.updatecheck import UpdateCheck
from projektrouska.models import *


class UpdateCheckTest(TestCase):

    def test_source_pages_available(self):
        """

        :return:
        """
        update_controller = UpdateCheck()

        for link in update_controller.cathegories_url:
            response = requests.get(link)
            self.assertEqual(response.status_code, 200)

    def test_at_least_one_result_is_up_to_date(self):
        update_controller = UpdateCheck()

        update_controller.clear()
        self.assertTrue(len(update_controller.all) == 0)

        update_controller.run()
        self.assertTrue(len(update_controller.all) > 0)

    def test_scrap_posts_links(self):
        update_controller = UpdateCheck()

        update_controller.links_to_posts = []
        update_controller.scrap_posts_links(
            "https://koronavirus.mzcr.cz/category/mimoradna-opatreni/")

        self.assertNotEqual(update_controller.links_to_posts, [])
        self.assertTrue(isinstance(update_controller.links_to_posts[0], str))
        self.assertTrue(len(update_controller.links_to_posts[0]) > 0)
