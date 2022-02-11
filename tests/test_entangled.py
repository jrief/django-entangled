import pytest
from bs4 import BeautifulSoup

from django.contrib.auth import get_user_model
from django.forms import fields, widgets
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from django.utils.html import strip_spaces_between_tags

from entangled.forms import EntangledModelForm
from entangled.utils import get_related_object, get_related_queryset
from .models import Product, Category


class ProductForm(EntangledModelForm):
    name = fields.CharField()
    active = fields.BooleanField()
    tenant = ModelChoiceField(queryset=get_user_model().objects.all(), empty_label=None)
    description = fields.CharField(required=False, widget=widgets.Textarea)
    categories = ModelMultipleChoiceField(queryset=Category.objects.all(), required=False)
    field_order = ['active', 'name', 'tenant', 'description', 'categories']

    class Meta:
        model = Product
        untangled_fields = ['name']
        entangled_fields = {'properties': ['active', 'tenant', 'description', 'categories']}


@pytest.mark.django_db
def test_unbound_form():
    product_form = ProductForm()
    assert product_form.is_bound is False
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active"></li>
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_tenant">Tenant:</label> <select name="tenant" id="id_tenant">
          <option value="1">John</option>
          <option value="2">Mary</option>
        </select></li>
        <li><label for="id_description">Description:</label> <textarea name="description" cols="40" rows="10" id="id_description">
</textarea></li>
        <li><label for="id_categories">Categories:</label> <select name="categories" id="id_categories" multiple>
          <option value="1">Paraphernalia</option>
          <option value="2">Detergents</option>
        </select></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected


@pytest.mark.django_db
def test_bound_form():
    data = {'name': "Colander", 'active': True, 'tenant': 2, 'categories': [1, 2]}
    product_form = ProductForm(data=data)
    assert product_form.is_bound
    assert product_form.is_valid()
    instance = product_form.save()
    tenant = {'model': 'auth.user', 'pk': 2}
    categories = {'model': 'tests.category', 'p_keys': [1, 2]}
    expected = dict(data, tenant=tenant, categories=categories, description='')
    assert instance.name == expected.pop('name')
    assert instance.properties == expected


@pytest.mark.django_db
def test_invalid_form():
    product_form = ProductForm(data={})
    assert product_form.is_bound
    assert product_form.is_valid() is False
    expected = {
        'name': ['This field is required.'],
        'active': ['This field is required.'],
        'tenant': ['This field is required.'],
    }
    assert product_form.errors == expected


@pytest.mark.django_db
def test_instance_form():
    properties = {
        'active': True,
        'tenant': {'model': 'auth.user', 'pk': 1},
        'description': "Cleaning tool consisting of stiff fibers",
        'categories': {'model': 'tests.category', 'p_keys': [1, 2]},
    }
    instance = Product.objects.create(name="Broom", properties=properties)
    product_form = ProductForm(instance=instance)
    assert product_form.is_bound is False
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active" checked></li>
        <li><label for="id_name">Name:</label> <input type="text" name="name" value="Broom" required id="id_name"></li>
        <li><label for="id_tenant">Tenant:</label> <select name="tenant" id="id_tenant">
          <option value="1" selected>John</option>
          <option value="2">Mary</option>
        </select></li>
        <li><label for="id_description">Description:</label> <textarea name="description" cols="40" rows="10" id="id_description">
Cleaning tool consisting of stiff fibers</textarea></li>
        <li><label for="id_categories">Categories:</label> <select name="categories" id="id_categories" multiple>
          <option value="1" selected>Paraphernalia</option>
          <option value="2" selected>Detergents</option>
        </select></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected


@pytest.mark.django_db
def test_change_form():
    properties = {
        'active': True,
        'tenant': {'model': 'auth.user', 'pk': 1},
        'categories': {'model': 'tests.category', 'p_keys': [1]},
    }
    instance = Product.objects.create(name="Broom", properties=properties)
    data = {
        'name': "Brush",
        'active': True,
        'tenant': 2,
        'description': "Cleaning tool with bristles",
        'categories': [2],
    }
    product_form = ProductForm(data=data, instance=instance)
    assert product_form.is_bound is True
    assert product_form.is_valid() is True
    product_form.save()
    instance.refresh_from_db()
    tenant = {'model': 'auth.user', 'pk': 2}
    categories = {'model': 'tests.category', 'p_keys': [2]}
    expected = dict(data, tenant=tenant, categories=categories)
    assert instance.name == expected.pop('name')
    assert instance.properties == expected


@pytest.mark.django_db
def test_form_inheritance():
    class HeavyProductForm(ProductForm):
        weight = fields.DecimalField(max_digits=6, decimal_places=1)
        description = fields.Field(widget=widgets.HiddenInput, initial='XY')

        class Meta:
            model = Product
            entangled_fields = {'properties': ['weight']}

        field_order = ['name', 'tenant', 'active', 'weight']

    product_form = HeavyProductForm()
    product_form._meta.untangled_fields == ['name']
    product_form._meta.entangled_fields == {'properties': ['active', 'tenant', 'description', 'weight']}
    assert product_form.is_bound is False
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_tenant">Tenant:</label> <select name="tenant" id="id_tenant">
          <option value="1">John</option>
          <option value="2">Mary</option>
        </select></li>
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active"></li>
        <li><label for="id_weight">Weight:</label> <input type="number" name="weight" step="0.1" required id="id_weight"></li>
        <li><label for="id_categories">Categories:</label> <select name="categories" id="id_categories" multiple>
          <option value="1">Paraphernalia</option>
          <option value="2">Detergents</option>
        </select><input type="hidden" name="description" value="XY" id="id_description"></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected


@pytest.mark.django_db
def test_get_related_object():
    properties = {
        'tenant': {'model': 'auth.user', 'pk': 2},
    }
    tenant = get_related_object(properties, 'tenant')
    assert isinstance(tenant, get_user_model())
    assert tenant.username == "Mary"
    assert get_related_object(properties, 'xyz') is None


@pytest.mark.django_db
def test_get_related_object_deprecated():
    from entangled.forms import get_related_object

    properties = {
        'tenant': {'model': 'auth.user', 'pk': 2},
    }
    with pytest.deprecated_call():
        tenant = get_related_object(properties, 'tenant')
        assert isinstance(tenant, get_user_model())


@pytest.mark.django_db
def test_get_related_queryset():
    properties = {
        'categories': {'model': 'tests.category', 'p_keys': [1, 2]},
    }
    categories = get_related_queryset(properties, 'categories')
    assert issubclass(categories.model, Category)
    assert categories.count() == 2
    assert get_related_queryset(properties, 'xyz') is None


@pytest.mark.django_db
def test_get_related_queryset_deprecated():
    from entangled.forms import get_related_queryset

    properties = {
        'categories': {'model': 'tests.category', 'p_keys': [1, 2]},
    }
    with pytest.deprecated_call():
        categories = get_related_queryset(properties, 'categories')
        assert issubclass(categories.model, Category)
        assert categories.count() == 2
