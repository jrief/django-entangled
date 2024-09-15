import pytest

from django.contrib.auth import get_user_model
from django.forms import fields, widgets, ModelMultipleChoiceField, ModelChoiceField, modelform_factory

from entangled.forms import EntangledModelForm

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
def test_modelform_untangled_only():
    form = modelform_factory(Product, form=ProductForm, fields=('name',))

    expected_fields = (
        'name',
    )
    assert len(form.base_fields) == len(expected_fields), form.base_fields.keys()
    for field in expected_fields:
        assert field in form.base_fields



@pytest.mark.django_db
def test_modelform_entangled_only():
    form = modelform_factory(Product, form=ProductForm, fields=('active', 'tenant',))

    expected_fields = (
        'active',
        'tenant',
        'properties',
    )
    assert len(form.base_fields) == len(expected_fields), form.base_fields.keys()
    for field in expected_fields:
        assert field in form.base_fields


@pytest.mark.django_db
def test_modelform_exlude_untangled():
    form = modelform_factory(Product, form=ProductForm, exclude=('name',))

    expected_fields = (
        'active',
        'tenant',
        'description',
        'categories',
        'properties',
    )
    assert len(form.base_fields) == len(expected_fields), form.base_fields.keys()
    for field in expected_fields:
        assert field in form.base_fields


@pytest.mark.django_db
def test_modelform_exlude_entangled():
    form = modelform_factory(Product, form=ProductForm, exclude=('active',))

    expected_fields = (
        'name',
        'tenant',
        'description',
        'categories',
        'properties',
    )
    assert len(form.base_fields) == len(expected_fields), form.base_fields.keys()
    for field in expected_fields:
        assert field in form.base_fields
