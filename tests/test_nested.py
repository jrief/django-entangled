import pytest
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


@pytest.mark.django_db
def test_unbound_form():
    product_form = ProductForm()
    assert product_form.is_bound is False
    print(product_form.as_ul())
