from django import VERSION as DJANGO_VERSION
from django.db import models

if DJANGO_VERSION < (3, 1):
    from jsonfield import JSONField
else:
    from django.db.models import JSONField


class Category(models.Model):
    identifier = models.CharField(
        max_length=10,
    )

    def __str__(self):
        return self.identifier


class Product(models.Model):
    name = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    properties = JSONField()
