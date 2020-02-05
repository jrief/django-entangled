import pytest
from bs4 import BeautifulSoup
from decimal import Decimal
from django.forms import fields
from django.forms.utils import ErrorDict

from entangled.fields import EntangledFormField
from entangled.forms import EntangledForm, EntangledModelForm

from .models import Product


@pytest.fixture(autouse=True)
def product():
    Product.objects.create(name='Primary')
    return Product.objects.first()


class InternalForm(EntangledForm):
    price = fields.DecimalField()


class DescriptionForm(EntangledForm):
    product_code = fields.IntegerField()
    product_name = fields.CharField()
    internal = EntangledFormField(InternalForm)


class ProductForm(EntangledModelForm):
    name = fields.CharField()
    active = fields.BooleanField(required=False)
    nested = EntangledFormField(DescriptionForm)
    field_order = ['name', 'flat', 'nested']

    class Meta:
        model = Product
        untangled_fields = ['name']
        entangled_fields = {'properties': ['active', 'nested']}


@pytest.mark.django_db
def test_unbound_form():
    product_form = ProductForm()
    assert product_form.is_bound is False
    expected = BeautifulSoup("""
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" id="id_active"></li>
        <li><label for="id_nested.product_code">Product code:</label> <input type="number" name="nested.product_code" required id="id_nested.product_code"></li>
        <li><label for="id_nested.product_name">Product name:</label> <input type="text" name="nested.product_name" required id="id_nested.product_name"></li>
        <li><label for="id_nested.internal.price">Price:</label> <input type="number" name="nested.internal.price" step="any" required id="id_nested.internal.price"></li>""",
        features='lxml')
    assert BeautifulSoup(product_form.as_ul(), features='lxml') == expected


@pytest.mark.django_db
def test_bound_form():
    data = {
        'name': "Colander",
        'flat': "Level",
        'active': 'on',
        'nested.product_code': "123",
        'nested.product_name': "Commodore",
        'nested.internal.price': "10.99",
    }
    product_form = ProductForm(data=data)
    assert product_form.is_bound
    assert product_form.is_valid()
    instance = product_form.save()
    assert instance.name == "Colander"
    assert instance.properties['active'] is True
    assert instance.properties['nested']['product_code'] == 123
    assert instance.properties['nested']['product_name'] == "Commodore"
    assert instance.properties['nested']['internal']['price'] == Decimal('10.99')


@pytest.mark.django_db
def test_invalid_form():
    product_form = ProductForm(data={'nested.product_name': "Commodore"})
    assert product_form.is_bound
    assert product_form.is_valid() is False
    expected = ErrorDict({
        'name': ['This field is required.'],
        'nested.product_code': ['This field is required.'],
        'nested.internal.price': ['This field is required.'],
    })
    assert product_form.errors == expected
