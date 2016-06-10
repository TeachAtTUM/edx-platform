"""
Test model class for deserialization tests.
See also test/data/data.json.
"""
from django.db import models
from config_models.models import ConfigurationModel


class ExampleDeserializeConfig(ConfigurationModel):
    """
    Test model for testing deserialization of ``ConfigurationModels`` with keyed configuration.
    """
    KEY_FIELDS = ('name',)

    name = models.TextField()
    int_field = models.IntegerField(default=10)
