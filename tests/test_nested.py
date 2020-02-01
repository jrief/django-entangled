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


@pytest.mark.django_db
def test_unbound_form():
    product_form = ProductForm()
    assert product_form.is_bound is False
    expected = BeautifulSoup("""    
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_flat">Flat:</label> <input type="text" name="flat" id="id_flat"></li>
        <li><label for="id_nested_0">Nested:</label>
            <ul>
                <li><label for="id_nested.product_code">Product code:</label> <input type="number" name="nested.product_code" id="id_nested.product_code"></li>
                <li><label for="id_nested.product_name">Product name:</label> <input type="text" name="nested.product_name" id="id_nested.product_name"></li>
            </ul>
        </li>
    """, features='lxml')
    print(product_form.as_p())
    print("============")
    print(product_form.as_ul())
    print("============")
    #print(product_form.as_table())
    other = BeautifulSoup(product_form.as_ul(), features='lxml')
    assert expected == other
