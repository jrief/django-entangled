# django-entangled

Edit JSON-Model Fields using a Standard Django Form.

[![Build Status](https://travis-ci.org/jrief/django-entangled.svg?branch=master)](https://travis-ci.org/jrief/django-entangled)
[![PyPI](https://img.shields.io/pypi/pyversions/django-entangled.svg)]()
[![PyPI version](https://img.shields.io/pypi/v/django-entangled.svg)](https://https://pypi.python.org/pypi/django-entangled)
[![PyPI](https://img.shields.io/pypi/l/django-entangled.svg)]()
[![Twitter Follow](https://img.shields.io/twitter/follow/shields_io.svg?style=social&label=Follow&maxAge=2592000)](https://twitter.com/jacobrief)


## Use-Case

A Django Model may contain JSON fields. Django itself, provides a
[JSON field](https://docs.djangoproject.com/en/stable/ref/contrib/postgres/fields/#jsonfield) specific to Postgres.
For other database implementations, there are plenty of alternatives.

Typically, the widget to edit a JSON field is a `<textarea ...><textarea>`. This HTML element however is very
inpracticable for editing. One possibility is to use a generic [JSON editor](https://github.com/josdejong/jsoneditor).
This however prevents to use all the nice form validation features provided by Django forms. By using
**django-entangled**, one can use a slightly modifed Django `ModelForm`, and store all or a subset of that form fields
inside one or more JSON fields.


## Installation

Simply install this Django app, for instance using:

```bash
pip install django-entangled
```

There is not need to add any configurations directives to the project's `settings.py`.


## Example

Say, we have a Django model to describe a bunch of different products. Some fields are used by all products, whereas
others describe the properties of that product. Since we don't want to create a different product model for each
product type, we use a JSON field to store these arbitrary properties.

```python
from django.db import models
from django.contrib.postgres.fields import JSONField

class Product(models.Model):
    name = models.CharField(max_length=50)

    price = models.DecimalField(max_digits=5, decimal_places=2)
    
    properties = JSONField()
```

In a typical form editing view, we would create a form inheriting from
[ModelForm](https://docs.djangoproject.com/en/stable/topics/forms/modelforms/#modelform) and refer to this model using
the `model` attribute in the `Meta`-class. Here the `properties`-field would show up as unstructured JSON rendered
inside a `<textarea ...><textarea>`. This definitely is not what we want! Instead we create a typical form using the
special mixin class `EntangledModelFormMixin`.

```python
from django.forms import fields, models
from entangled.forms import EntangledModelFormMixin
from .models import Product

class ProductForm(EntangledModelFormMixin, models.ModelForm):
    color = fields.RegexField(
        regex=r'^#[0-9a-f]{6}$',
    )

    size = fields.ChoiceField(
        choices=[('s', "small"), ('m', "medium"), ('l', "large"), ('xl', "extra large")],
    )

    class Meta:
        model = Product
        fields = ['name', 'price']
        entangled_fields = {'properties': ['color', 'size']}
```

In addition to the mixin class `EntangledModelFormMixin` we add a special dictionary named `entangled_fields` to our
`Meta`-options. The key (here `'properties'`) in this dictionary refers to the JSON-field of our model. The value (here
`['color', 'size']`) is a list of named form fields, declared in our form- or base-class of therefore. This allows us,
to assign standard Django form fields to arbitrary JSON fields declared in our Django model.

We can use this form in any Django detail view. A typical use-case, is the built-in Django ModelAdmin:

```python
from django.contrib import admin
from .models import Product
from .forms import ProductForm

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
```

Since the form used by this `ModelAdmin`-class
[can not be created dynamically](https://docs.djangoproject.com/en/stable/ref/contrib/admin/#django.contrib.admin.ModelAdmin.form),
we have to declare it explicitly using the `form`-attribute. This is the only change which has to be performed, in
order to store arbitrary content inside our JSON model-fields.
