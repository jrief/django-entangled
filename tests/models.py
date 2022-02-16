from django.db.models import CharField, Model
try:
    from django.db.models import JSONField
except ImportError:  # Django<3.1
    from jsonfield import JSONField


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

    properties = JSONField()
