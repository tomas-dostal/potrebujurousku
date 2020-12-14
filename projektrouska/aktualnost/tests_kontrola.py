from django.test import TestCase
from projektrouska.aktualnost.kontrola import Update_check


# Tato testclassa v podstatě nic moc nedělá. Asi těžko budu
class UpdateCheckTest(TestCase):

    def setup(self):
        self.update_controller = Update_check()

    def test_empty_values(self):
        self.assert
        self.assertEqual(lion.speak(), 'The lion says "roar"')
        self.assertEqual(lion.speak(), 'The lion says "roar"')
        self.assertEqual(lion.speak(), 'The lion says "roar"')

        update_controller.run()


    def test_local_copy_empty(self):
        self.update_controller.clear()
        self.assertEqual(self.db_localcopy,  None)