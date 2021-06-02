import json
import unittest

from django.core.serializers.json import DjangoJSONEncoder

from projektrouska.functions import return_as_array
from projektrouska.api.update_stats import get_stats
from django.db import connection

from django.test import TestCase
from projektrouska.updatecheck import UpdateCheck
from projektrouska.models import *

update_controller = UpdateCheck()


class UpdateStatsTest(TestCase):

    def test_query_equals_edge_values(self):
        date3 = (datetime.datetime.now() - datetime.timedelta(days=50)).replace(tzinfo=utc)
        date2 = (datetime.datetime.now() - datetime.timedelta(days=2)).replace(tzinfo=utc)

        UpdateLogs(
            date_updated=date2,
            checksum="test",
            comment="older one, displayed in groupby",
            up_to_date_percents=12).save()

        UpdateLogs(
            date_updated=date3,
            checksum="test3",
            comment="Too old to be displayed",
            up_to_date_percents=42).save()

        res1 = json.loads(get_stats(show_last_days=50))["data"]
        self.assertEqual(len(res1), 2)

    def test_query_equals_sql(self):
        date1 = (datetime.datetime.now()
                 - datetime.timedelta(days=1)).replace(tzinfo=utc)
        date2 = (datetime.datetime.now()
                 - datetime.timedelta(days=2)).replace(tzinfo=utc)
        date3 = (datetime.datetime.now()
                 - datetime.timedelta(days=50)).replace(tzinfo=utc)

        g1 = UpdateLogs(
            date_updated=date1,
            checksum="test",
            comment="older one, displayed in groupby",
            up_to_date_percents=12).save()

        g2 = UpdateLogs(
            date_updated=date2,
            checksum="test",
            comment="older one, displayed in groupby",
            up_to_date_percents=12).save()

        g3 = UpdateLogs(
            date_updated=date3,
            checksum="test3",
            comment="Too old to be displayed",
            up_to_date_percents=42).save()

        res1 = get_stats(show_last_days=14)
        show_from = (datetime.datetime.now()
                     - datetime.timedelta(days=14)).replace(tzinfo=utc)

        qu = '''
                select * from
                (
                select min(date_updated) as date_updated,
                    "checksum"    ,                
                    "comment", 
                    up_to_date_percents, 
                    missing_count, 
                    change_link_count,
                    outdated_count, 
                    total_changes
                from update_logs
                group by 
                    "checksum",
                    "comment", 
                    up_to_date_percents, 
                    missing_count, 
                    change_link_count, 
                    outdated_count, 
                    total_changes 
                order by  date_updated
                
                    ) as ali where  date_updated >= %s
                '''

        with connection.cursor() as cursor:
            cursor.execute(qu, [show_from])

            # res1 is returned exactly this way, so if data is the same, it should be equal
            res2 = json.dumps(
                {
                    "data": list(return_as_array(cursor.fetchall(), cursor.description))
                },
                sort_keys=True,
                indent=1,
                cls=DjangoJSONEncoder)

            self.assertEqual(res2, res1)


if __name__ == '__main__':
    unittest.main()
