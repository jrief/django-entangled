# django-entangled

Edit JSON-Model Fields using a Standard Django Form.

[![Build Status](https://travis-ci.org/jrief/django-entangled.svg?branch=master)](https://travis-ci.org/jrief/django-entangled)
[![PyPI](https://img.shields.io/pypi/pyversions/django-entangled.svg)]()
[![PyPI version](https://img.shields.io/pypi/v/django-entangled.svg)](https://https://pypi.python.org/pypi/django-entangled)
[![PyPI](https://img.shields.io/pypi/l/django-entangled.svg)]()
[![Twitter Follow](https://img.shields.io/twitter/follow/shields_io.svg?style=social&label=Follow&maxAge=2592000)](https://twitter.com/jacobrief)


## Use-Case

A Django Model may contain fields which accept arbitrary data stored as JSON. Django itself, provides a
[JSON field](https://docs.djangoproject.com/en/stable/ref/contrib/postgres/fields/#jsonfield) specific to Postgres.
For other database implementations, there are plenty of alternatives.

When creating a form from a models, the input field associated with a JSON field, typically is a `<textarea ...><textarea>`.
This textarea widget is very inpracticable for editing, because it just contains a textual representation of that
object notation. One possibility is to use a generic [JSON editor](https://github.com/josdejong/jsoneditor),
which with some JavaScript, transforms the widget into an attribute-value-pair editor. This approach however prevents
us from utilizing all the nice features provided by the Django form framework, such as field validation, normalization
of data and the usage of foreign keys. By using **django-entangled**, one can use a Django `ModelForm`, and store all,
or a subset of that form fields in one or more JSON fields inside of the associated model.


## Installation

Simply install this Django app, for instance by invoking:

```bash
pip install django-entangled
```

There is no need to add any configurations directives to the project's `settings.py`.


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
inside a `<textarea ...><textarea>`. This definitely is not what we want! Instead we create a typical Django Form using
the special mixin class `EntangledModelFormMixin`.

```python
from django.contrib.auth import get_user_model
from django.forms import fields, models
from entangled.forms import EntangledModelForm
from .models import Product

class ProductForm(EntangledModelForm):
    color = fields.RegexField(
        regex=r'^#[0-9a-f]{6}$',
    )

    size = fields.ChoiceField(
        choices=[('s', "small"), ('m', "medium"), ('l', "large"), ('xl', "extra large")],
    )

    tenant = models.ModelChoiceField(
        queryset=get_user_model().objects.filter(is_staff=True),
    )

    class Meta:
        model = Product
        entangled_fields = {'properties': ['color', 'size', 'tenant']}  # fields provided by this form
        untangled_fields = ['name', 'price']  # these fields are provided by the Product model
```

In addition to the mixin class `EntangledModelFormMixin` we add a special dictionary named `entangled_fields` to our
`Meta`-options. In this dictionary, the key (here `'properties'`) refers to the JSON-field in our model `Product`.
The value (here `['color', 'size', 'tenant']`) is a list of named form fields, declared in our form- or base-class of
therefore. This allows us, to assign all standard Django form fields to arbitrary JSON fields declared in our Django
model. Moreover, we can even use a `ModelChoiceField` to refer to another model object using a
[generic relation](https://docs.djangoproject.com/en/stable/ref/contrib/contenttypes/#generic-relations)

Since in this form we also want to access the non-JSON fields from our Django model, we add a list named
`untangled_fields` to our `Meta`-options. In this list, (here `['name', 'price']`) we refer to the non-JSON fields
in our model `Product`. From both of these iterables, `entangled_fields` and `untangled_fields`, the mixin class
`EntangledModelFormMixin` then builds the `Meta`-option `fields`, otherwise required. Therefore there is no need
to explicitly declare this list.

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


## Caveats

Due to the nature of JSON, indexing and thus building filters or sorting rules based on the fields content is not as
simple, as with standard model fields. Therefore, this approach is best suited, if the main focus is to store data,
rather than digging through data.

Foreign keys are stored as `"fieldname": {"model": "appname.modelname", "pk": 1234}` in our JSON field, meaning that
we have no database constraints. If a target object is deleted, that foreign key points to nowhere. Therefore always
keep in mind, that we don't have any referential integrity and hence must writing our code in a defensive manner.


## Changes

- 0.3
  * Add support for `ModelMultipleChoiceField`.
  * Fix: Make a deep copy of `entangled_fields` and `untangled_fields` before merging.
  * Add covenience class `EntangledModelForm`.
  * Moving data from entangled fields onto their compressed representation, now is performed in
    after the form has performed its own `clean()`, so that accessing form fields is more natural.
  * Add functions `get_related_object` and `get_related_queryset` to get the model object from its
    JSON representation.

- 0.2
  * Introduce `Meta`-option `untangled_fields`, because the approach in 0.1 didn't always work.
  * Use `formfield()`-method, for portability reasons with Django's Postgres JSON field.

- 0.1
  * Initial release.
