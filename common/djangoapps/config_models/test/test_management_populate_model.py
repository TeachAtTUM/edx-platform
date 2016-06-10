"""
Tests of the populate_model management command.
"""

import os.path

from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.core.management.base import CommandError

from config_models.test.models import ExampleDeserializeConfig
from config_models.management.commands import populate_model


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
