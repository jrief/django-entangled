import pytest
from bs4 import BeautifulSoup
from django.forms import fields

from entangled.fields import EntangledFormField
from entangled.forms import EntangledForm, EntangledModelForm

from .models import Product


@pytest.fixture(autouse=True)
def product():
    Product.objects.create(name='Primary')
    return Product.objects.first()


class DescriptionForm(EntangledForm):
    product_code = fields.IntegerField()
    product_name = fields.CharField()


class ProductForm(EntangledModelForm):
    name = fields.CharField()
    flat = fields.CharField(required=False)
    nested = EntangledFormField(DescriptionForm)
    field_order = ['name', 'flat', 'nested']

    class Meta:
        model = Product
        entangled_fields = {'properties': ['flat', 'nested']}
        untangled_fields = ['name']


@pytest.mark.django_db
def test_unbound_form():
    product_form = ProductForm()
    assert product_form.is_bound is False
    expected = BeautifulSoup("""
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_flat">Flat:</label> <input type="text" name="flat" id="id_flat"></li>
        <li><label for="id_nested.product_code">Product code:</label> <input type="number" name="nested.product_code" required id="id_nested.product_code"></li>
        <li><label for="id_nested.product_name">Product name:</label> <input type="text" name="nested.product_name" required id="id_nested.product_name"></li>""",
        features='lxml')
    assert BeautifulSoup(product_form.as_ul(), features='lxml') == expected


@pytest.mark.django_db
def test_bound_form():
    data = {'name': "Colander", 'flat': "Level", 'nested.product_code': 123, 'nested.product_name': "Commodore"}
    product_form = ProductForm(data=data)
    assert product_form.is_bound
    assert product_form.is_valid()
    instance = product_form.save()
    assert instance.name == "Colander"
    assert instance.properties['flat'] == "Level"
    assert instance.properties['nested']['product_code'] == 123
    assert instance.properties['nested']['product_name'] == "Commodore"
