"""
Tests of ConfigurationModel utilities.
"""
import textwrap
import os.path

from django.test import TestCase
from django.utils import timezone
from django.utils.six import BytesIO
from django.contrib.auth.models import User

from config_models.test.models import ExampleDeserializeConfig
from config_models.utils import deserialize_json


class DeserializeJSONTests(TestCase):
    """
    Tests of deserializing the JSON representation of ConfigurationModels.
    """
    def setUp(self):
        super(DeserializeJSONTests, self).setUp()

    def test_deserialize_models(self):
        """
        Tests the "happy path", where 2 instances of the test model should be created.
        A valid username is supplied for the operation.
        """
        test_username = 'test_worker'
        User.objects.create_user(username=test_username)
        start_date = timezone.now()
        fixture_path = os.path.join(os.path.dirname(__file__), 'data', 'data.json')
        with open(fixture_path) as data:
            deserialize_json(data, test_username)

        self.assertEquals(2, len(ExampleDeserializeConfig.objects.all()))

        betty = ExampleDeserializeConfig.current('betty')
        self.assertTrue(betty.enabled)
        self.assertEquals(5, betty.int_field)
        self.assertTrue(betty.change_date > start_date)
        self.assertEquals(test_username, betty.changed_by.username)

        fred = ExampleDeserializeConfig.current('fred')
        self.assertFalse(fred.enabled)
        self.assertEquals(10, fred.int_field)
        self.assertTrue(fred.change_date > start_date)
        self.assertEquals(test_username, fred.changed_by.username)

    def test_no_username(self):
        """
        Tests that if no username is specified, changed_by is set to None.
        """
        test_json = textwrap.dedent("""
            {
                "model": "config_models.exampledeserializeconfig",
                "data": [{ "name": "dino" }]
            }
            """)
        stream = BytesIO(test_json)
        deserialize_json(stream)

        self.assertEquals(1, len(ExampleDeserializeConfig.objects.all()))
        dino = ExampleDeserializeConfig.current('dino')
        self.assertFalse(dino.enabled)
        self.assertIsNone(dino.changed_by)

    def test_bad_username(self):
        """
        Tests the error handling when the specified user does not exist.
        """
        test_json = textwrap.dedent("""
            {
                "model": "config_models.exampledeserializeconfig",
                "data": [{"name": "dino"}]
            }
            """)
        with self.assertRaisesRegexp(Exception, "User matching query does not exist"):
            deserialize_json(BytesIO(test_json), "unknown_username")

    def test_invalid_json(self):
        """
        Tests the error handling when there is invalid JSON.
        """
        test_json = textwrap.dedent("""
            {
                "model": "config_models.exampledeserializeconfig",
                "data": [{"name": "dino"
            """)
        with self.assertRaisesRegexp(Exception, "JSON parse error"):
            deserialize_json(BytesIO(test_json))

    def test_invalid_model(self):
        """
        Tests the error handling when the configuration model specified does not exist.
        """
        test_json = textwrap.dedent("""
            {
                "model": "xxx.yyy",
                "data":[{"name": "dino"}]
            }
            """)
        with self.assertRaisesRegexp(Exception, "No installed app"):
            deserialize_json(BytesIO(test_json))
