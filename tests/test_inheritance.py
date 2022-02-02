import pytest
from bs4 import BeautifulSoup

from django.forms import fields, widgets
from django.utils.html import strip_spaces_between_tags

from entangled.forms import EntangledModelForm, EntangledModelFormMixin
from .models import Product


class ProductForm(EntangledModelForm):
    name = fields.CharField()
    active = fields.BooleanField()
    description = fields.CharField(required=False, widget=widgets.Textarea)

    class Meta:
        model = Product
        untangled_fields = ['name']
        entangled_fields = {'properties': ['active', 'description']}


@pytest.mark.django_db
def test_unsorted_form():
    product_form = ProductForm()
    assert product_form.is_bound is False
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active"></li>
        <li><label for="id_description">Description:</label> <textarea name="description" cols="40" rows="10" id="id_description">
</textarea></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected


class SortedProductForm(ProductForm):
    field_order = ['active', 'description', 'name']

    class Meta:
        model = Product
        entangled_fields = {'properties': ['active', 'description']}


@pytest.mark.django_db
def test_sorted_form():
    product_form = SortedProductForm()
    assert product_form.is_bound is False
    print(product_form.as_ul())
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active"></li>
        <li><label for="id_description">Description:</label> <textarea name="description" cols="40" rows="10" id="id_description">
</textarea></li>
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected


class UnsortedBookForm(ProductForm):
    author = fields.CharField()

    class Meta:
        model = Product
        entangled_fields = {'properties': ['author']}


@pytest.mark.django_db
def test_simple_inheritance_unsorted():
    product_form = UnsortedBookForm()
    assert product_form.is_bound is False
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active"></li>
        <li><label for="id_description">Description:</label> <textarea name="description" cols="40" rows="10" id="id_description">
</textarea></li>
        <li><label for="id_author">Author:</label> <input type="text" name="author" required id="id_author"></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected


class SortedBookForm(ProductForm):
    author = fields.CharField()
    field_order = ['author', 'active', 'name', 'description']

    class Meta:
        model = Product
        entangled_fields = {'properties': ['author']}


@pytest.mark.django_db
def test_simple_inheritance_sorted():
    product_form = SortedBookForm()
    assert product_form.is_bound is False
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_author">Author:</label> <input type="text" name="author" required id="id_author"></li>
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active"></li>
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_description">Description:</label> <textarea name="description" cols="40" rows="10" id="id_description">
</textarea></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected


class QuantityMixin(EntangledModelFormMixin):
    quantity = fields.IntegerField()

    class Meta:
        entangled_fields = {'properties': ['quantity']}


class QuantifiedUnsortedProductForm(QuantityMixin, ProductForm):
    unit = fields.CharField()

    class Meta:
        model = Product
        entangled_fields = {'properties': ['unit']}


@pytest.mark.django_db
def test_multiple_inheritance_unsorted():
    product_form = QuantifiedUnsortedProductForm()
    assert product_form.is_bound is False
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active"></li>
        <li><label for="id_description">Description:</label> <textarea name="description" cols="40" rows="10" id="id_description">
</textarea></li>
        <li><label for="id_quantity">Quantity:</label> <input type="number" name="quantity" required id="id_quantity"></li>
        <li><label for="id_unit">Unit:</label> <input type="text" name="unit" required id="id_unit"></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected


class QuantifiedSortedProductForm(QuantityMixin, ProductForm):
    unit = fields.CharField()
    field_order = ['active', 'unit', 'name', 'quantity', 'description']

    class Meta:
        model = Product
        entangled_fields = {'properties': ['unit']}


@pytest.mark.django_db
def test_multiple_inheritance_sorted():
    product_form = QuantifiedSortedProductForm()
    assert product_form.is_bound is False
    expected = BeautifulSoup(strip_spaces_between_tags("""
        <li><label for="id_active">Active:</label> <input type="checkbox" name="active" required id="id_active"></li>
        <li><label for="id_unit">Unit:</label> <input type="text" name="unit" required id="id_unit"></li>
        <li><label for="id_name">Name:</label> <input type="text" name="name" required id="id_name"></li>
        <li><label for="id_quantity">Quantity:</label> <input type="number" name="quantity" required id="id_quantity"></li>
        <li><label for="id_description">Description:</label> <textarea name="description" cols="40" rows="10" id="id_description">
</textarea></li>"""),
        features='lxml',
    )
    assert BeautifulSoup(strip_spaces_between_tags(product_form.as_ul()), features='lxml') == expected
