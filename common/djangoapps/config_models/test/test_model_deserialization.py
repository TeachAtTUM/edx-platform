"""
Tests of the populate_model management command.
"""

import textwrap
import os.path

from django.utils import timezone
from django.utils.six import BytesIO

from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.core.management.base import CommandError
from django.db import models

from config_models.management.commands import populate_model
from config_models.models import ConfigurationModel
from config_models.utils import deserialize_json


class ExampleDeserializeConfig(ConfigurationModel):
    """
    Test model for testing deserialization of ``ConfigurationModels`` with keyed configuration.
    """
    KEY_FIELDS = ('name',)

    name = models.TextField()
    int_field = models.IntegerField(default=10)

    def __unicode__(self):
        return "ExampleDeserializeConfig(enabled={}, name={}, int_field={})".format(
            self.enabled, self.name, self.int_field
        )


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
        self.assertGreater(betty.change_date, start_date)
        self.assertEquals(test_username, betty.changed_by.username)

        fred = ExampleDeserializeConfig.current('fred')
        self.assertFalse(fred.enabled)
        self.assertEquals(10, fred.int_field)
        self.assertGreater(fred.change_date, start_date)
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


class PopulateModelTestCase(TestCase):
    """
    Tests of populate model management command.
    """
    def setUp(self):
        super(PopulateModelTestCase, self).setUp()
        self.file_path = os.path.join(os.path.dirname(__file__), 'data', 'data.json')

    def test_run_command(self):
        """
        Tests the "happy path", where 2 instances of the test model should be created.
        A valid username is supplied for the operation.
        """
        test_username = 'test_management_worker'
        User.objects.create_user(username=test_username)
        _run_command(file=self.file_path, username=test_username)
        self.assertEquals(2, len(ExampleDeserializeConfig.objects.all()))

        betty = ExampleDeserializeConfig.current('betty')
        self.assertEquals(test_username, betty.changed_by.username)

        fred = ExampleDeserializeConfig.current('fred')
        self.assertEquals(test_username, fred.changed_by.username)

    @override_settings(
        CONFIG_MODEL_SERVICE_WORKER_USERNAME="worker_from_settings"
    )
    def test_no_user_specified(self):
        """
        Tests the case of no username being specified.
        In this case, settings.CONFIG_MODEL_SERVICE_WORKER_USERNAME will be used.
        """
        User.objects.create_user(username="worker_from_settings")
        _run_command(file=self.file_path)
        betty = ExampleDeserializeConfig.current('betty')
        self.assertEquals("worker_from_settings", betty.changed_by.username)

    def test_no_file_specified(self):
        """
        Tests the error handling when no JSON file is supplied.
        """
        with self.assertRaisesRegexp(CommandError, "A file containing JSON must be specified"):
            _run_command()

    def test_bad_file_specified(self):
        """
        Tests the error handling when the path to the JSON file is incorrect.
        """
        with self.assertRaisesRegexp(CommandError, "File does/not/exist.json does not exist"):
            _run_command(file="does/not/exist.json")


def _run_command(*args, **kwargs):
    """Run the management command to deserializer JSON ConfigurationModel data. """
    command = populate_model.Command()
    return command.handle(*args, **kwargs)
