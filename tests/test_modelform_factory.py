import pytest

from django.forms import modelform_factory

from .models import Product
from .test_inheritance import QuantifiedUnsortedProductForm


@pytest.mark.django_db
def test_modelform_untangled_only():
    form = modelform_factory(Product, form=QuantifiedUnsortedProductForm, fields=('name',))

    expected_fields = (
        'name',
    )
    assert len(form.base_fields) == len(expected_fields), form.base_fields.keys()
    for field in expected_fields:
        assert field in form.base_fields



@pytest.mark.django_db
def test_modelform_entangled_only():
    form = modelform_factory(Product, form=QuantifiedUnsortedProductForm, fields=('active',))

    expected_fields = (
        'active',
        'properties',
    )
    assert len(form.base_fields) == len(expected_fields), form.base_fields.keys()
    for field in expected_fields:
        assert field in form.base_fields


@pytest.mark.django_db
def test_modelform_exclude_untangled():
    form = modelform_factory(Product, form=QuantifiedUnsortedProductForm, fields="__all__", exclude=('name',))

    expected_fields = (
        'dummy_field',
        'active',
        'description',
        'quantity',
        'unit',
        'properties',
    )
    assert len(form.base_fields) == len(expected_fields), form.base_fields.keys()
    for field in expected_fields:
        assert field in form.base_fields


@pytest.mark.django_db
def test_modelform_exclude_entangled():
    form = modelform_factory(Product, form=QuantifiedUnsortedProductForm, fields="__all__", exclude=('active',))

    expected_fields = (
        'name',
        'dummy_field',
        'description',
        'quantity',
        'unit',
        'properties',
    )
    assert len(form.base_fields) == len(expected_fields), form.base_fields.keys()
    for field in expected_fields:
        assert field in form.base_fields

