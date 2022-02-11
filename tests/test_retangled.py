import pytest
from bs4 import BeautifulSoup

from django.contrib.auth import get_user_model
from django.forms import fields
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from django.utils.html import strip_spaces_between_tags

from entangled.forms import EntangledModelForm
from .models import Product, Category


class ProductForm(EntangledModelForm):
    name = fields.CharField()
    tenant = ModelChoiceField(queryset=get_user_model().objects.all(), empty_label=None)
    active = fields.BooleanField()
    color = fields.CharField()
    size = fields.ChoiceField(
        choices=[
            ('s', "Small"),
            ('m', "Medium"),
            ('l', "Large"),
        ]
    )
    categories = ModelMultipleChoiceField(queryset=Category.objects.all(), required=False)

    class Meta:
        model = Product
        untangled_fields = ['name']
        entangled_fields = {'properties': ['tenant', 'active', 'color', 'size', 'categories']}
        retangled_fields = {'color': 'extra.variants.color', 'size': 'extra.variants.size',
                            'tenant': 'ownership.tenant', 'categories': 'extra.categories'}


@pytest.mark.django_db
def test_unbound_form():
    product_form = ProductForm()
    assert product_form.is_bound is False
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_tenant">Tenant:</label> <select name="tenant" id="id_tenant">
          <option value="1">John</option>
          <option value="2">Mary</option>
        </select></li>
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active"></li>
        <li><label for="id_color">Color:</label> <input type="text" name="color" required id="id_color"></li>
        <li><label for="id_size">Size:</label> <select name="size" id="id_size">
          <option value="s">Small</option>
          <option value="m">Medium</option>
          <option value="l">Large</option>
        </select></li>
        <li><label for="id_categories">Categories:</label> <select name="categories" id="id_categories" multiple>
          <option value="1">Paraphernalia</option>
          <option value="2">Detergents</option>
        </select></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected


@pytest.mark.django_db
def test_bound_form():
    data = {'name': "Colander", 'tenant': 2, 'active': True, 'color': "red", 'size': "m", 'categories': [1, 2]}
    product_form = ProductForm(data=data)
    assert product_form.is_bound
    assert product_form.is_valid()
    instance = product_form.save()
    extra = {
        'categories': {'model': 'tests.category', 'p_keys': data.pop('categories')},
        'variants': {k: data.pop(k) for k in ['color', 'size']},
    }
    expected = dict(data, extra=extra, ownership={'tenant': {'model': 'auth.user', 'pk': data.pop('tenant')}})
    assert instance.name == expected.pop('name')
    assert instance.properties == expected


@pytest.mark.django_db
def test_instance_form():
    properties = {
        'active': True,
        'extra': {
            'variants': {
                'color': 'silver',
                'size': 's',
            },
            'categories': {'model': 'tests.category', 'p_keys': [1, 2]},
        },
        'ownership': {
            'tenant': {'model': 'auth.user', 'pk': 1},
        },
    }
    instance = Product.objects.create(name="Grater", properties=properties)
    product_form = ProductForm(instance=instance)
    assert product_form.is_bound is False
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_name">Name:</label> <input type="text" name="name" value="Grater" required id="id_name"></li>
        <li><label for="id_tenant">Tenant:</label> <select name="tenant" id="id_tenant">
          <option value="1" selected>John</option>
          <option value="2">Mary</option>
        </select></li>
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active" checked></li>
        <li><label for="id_color">Color:</label> <input type="text" name="color" value="silver" required id="id_color"></li>
        <li><label for="id_size">Size:</label> <select name="size" id="id_size">
          <option value="s" selected>Small</option>
          <option value="m">Medium</option>
          <option value="l">Large</option>
        </select></li>
        <li><label for="id_categories">Categories:</label> <select name="categories" id="id_categories" multiple>
          <option value="1" selected>Paraphernalia</option>
          <option value="2" selected>Detergents</option>
        </select></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected
