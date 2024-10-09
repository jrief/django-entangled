from django.db.models import CharField, JSONField, Model


class Category(Model):
    identifier = CharField(
        max_length=10,
    )

    def __str__(self):
        return self.identifier


class Product(Model):
    name = CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    dummy_field = CharField(max_length=42, blank=True, null=True)
    properties = JSONField()
