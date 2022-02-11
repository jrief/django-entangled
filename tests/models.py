from django.db import models


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

    properties = models.JSONField()
