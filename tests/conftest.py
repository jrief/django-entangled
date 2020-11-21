import pytest

from django.contrib.auth import get_user_model

from .models import Category


@pytest.fixture(autouse=True)
def tenants():
    User = get_user_model()
    User.objects.create(username='John')
    User.objects.create(username='Mary')
    return User.objects.all()


@pytest.fixture(autouse=True)
def categories():
    Category.objects.create(identifier='Paraphernalia')
    Category.objects.create(identifier='Detergents')
    return Category.objects.all()
