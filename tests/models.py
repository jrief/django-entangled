from django.db import models
from jsonfield import JSONField


class Title(models.Model):
    identifier = models.CharField(
        max_length=10,
    )

    def __str__(self):
        return self.identifier


class FreeModel(models.Model):
    anything = models.CharField(
        max_length=5,
        blank=True,
        null=True,
    )

    glossary = JSONField(default={})
