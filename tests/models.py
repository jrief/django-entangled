from django.db import models
from jsonfield import JSONField


class FreeModel(models.Model):
    anything = models.CharField(
        max_length=5,
        blank=True,
        null=True,
    )

    glossary = JSONField(default={})
