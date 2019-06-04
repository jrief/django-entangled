from django.db import models
from jsonfield import JSONField


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
