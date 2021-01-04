from django.test import TestCase
from projektrouska.aktualnost.updatecheck import UpdateCheck
from projektrouska.models import *

update_controller = UpdateCheck()


class UpdateCheckTest(TestCase):

    def test_scrap_posts_links(self):
        update_controller.links_to_posts = []
        update_controller.scrap_posts_links(
            "https://koronavirus.mzcr.cz/category/mimoradna-opatreni/")

        self.assertNotEqual(update_controller.links_to_posts, [])
        self.assertTrue(isinstance(update_controller.links_to_posts[0], str))
        self.assertTrue(len(update_controller.links_to_posts[0]) > 0)

    def test_is_in_db_matching_all(self):
        update_controller.up_to_date = []
        self.p = Precaution(id=1,
                            code_identificator="TEST1",
                            full_name="TEST1 full name",
                            short_name="TEST1 nme",
                            valid_from=datetime.date(2015, 10, 10),
                            valid_to=datetime.datetime.now(),
                            status=0,
                            priority=1,
                            created_date=datetime.datetime.now(),
                            # modified_date=datetime.datetime.now(),
                            )
        self.p.save()

        self.e = ExternalContent(
            id=1,
            date_inserted=datetime.datetime.now(),
            content_type=ExternalContent.PDF,
            preview=False,
            url_external="https://urlexternal.com"
        )
        self.e.save()

        self.p.external_contents.add(self.e)

        self.p.save()
        self.e.save()

        update_controller.add_if_not_exists("TEST1", "https://urlexternal.com")

        matching_objects = Precaution.objects.filter(
            full_name="TEST1",
            external_contents__url_external="https://urlexternal.com"
        ).all()

        self.assertTrue(len(matching_objects) == 2)

        update_controller.add_if_not_exists(
            "TEST1", "https://urlexternal222.com")
        matching_objects = Precaution.objects.filter(
            full_name="TEST1",
            external_contents__url_external="https://urlexternal222.com"
        ).all()

        self.assertTrue(len(matching_objects) == 1)

    def test_is_in_db_matching_name_only(self):
        update_controller.up_to_date = []
        p = Precaution(id=1,
                       code_identificator="TEST1",
                       full_name="TEST1 full name",
                       short_name="TEST1 nme",
                       valid_from=datetime.date(2015, 10, 10),
                       created_date=datetime.datetime.now(),
                       modified_date=datetime.datetime.now(),
                       valid_to=datetime.datetime.now(),
                       status=Precaution.ENABLED_AUTO,
                       priority=1)
        p.save()

        e = ExternalContent(
            id=1,
            date_inserted=datetime.datetime.now(),
            content_type=ExternalContent.PDF,
            preview=False,
            url_external="https://urlexternal.com"
        )
        e.save()

        p.external_contents.add(e)

        p.save()
        e.save()
        update_controller.to_be_changed_link = []
        update_controller.to_be_added = []
        update_controller.up_to_date = []

        # TODO: Maybe it creates a new instance of db or sth like that
        # Because of some strange reason it does not work as expected
        update_controller.add_if_not_exists(
            "TEST1", "https://urlexternal222.com")
        self.assertEqual(len(update_controller.to_be_changed_link), 1)
        self.assertEqual(len(update_controller.up_to_date), 0)
        self.assertEqual(len(update_controller.to_be_added), 0)
