# django-entangled

Edit JSON-Model Fields using a Standard Django Form.

[![Build Status](https://travis-ci.org/jrief/django-entangled.svg?branch=master)](https://travis-ci.org/jrief/django-entangled)
[![Coverage](https://codecov.io/github/jrief/django-entangled/coverage.svg?branch=master)](https://codecov.io/github/jrief/django-entangled?branch=master)
[![PyPI](https://img.shields.io/pypi/pyversions/django-entangled.svg)]()
[![PyPI version](https://img.shields.io/pypi/v/django-entangled.svg)](https://https://pypi.python.org/pypi/django-entangled)
[![PyPI](https://img.shields.io/pypi/l/django-entangled.svg)]()


## Use-Case

A Django Model may contain fields which accept arbitrary data stored as JSON. Django itself, provides a
[JSON field](https://docs.djangoproject.com/en/stable/ref/models/fields/#django.db.models.JSONField) (it was
[specific to Postgres before Django-3.1](https://docs.djangoproject.com/en/3.1/ref/contrib/postgres/fields/#jsonfield)).

When creating a form from a model, the input field associated with a JSON field, typically is a `<textarea ...></textarea>`.
This textarea widget is very inpracticable for editing, because it just contains a textual representation of that
object notation. One possibility is to use a generic [JSON editor](https://github.com/josdejong/jsoneditor),
which with some JavaScript, transforms the widget into an attribute-value-pair editor. This approach however requires
to manage the field keys ourself. It furthermore prevents us from utilizing all the nice features provided by the Django
form framework, such as field validation, normalization of data and the usage of foreign keys.

By using **django-entangled**, one can use a Django `ModelForm`, and store all,
or a subset of that form fields in one or more JSON fields inside of the associated model.


## Installation

Simply install this Django app, for instance by invoking:

```bash
pip install django-entangled
```

There is no need to add any configuration directives to the project's `settings.py`.


## Example

Say, we have a Django model to describe a bunch of different products. The name and the price fields are common to all
products, whereas the properties can vary depending on its product type. Since we don't want to create a different
product model for each product type, we use a JSON field to store these arbitrary properties.

```python
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=50)

    price = models.DecimalField(max_digits=5, decimal_places=2)

    properties = models.JSONField()
```

In a typical form editing view, we would create a form inheriting from
[ModelForm](https://docs.djangoproject.com/en/stable/topics/forms/modelforms/#modelform) and refer to this model using
the `model` attribute in its `Meta`-class. Then the `properties`-field would show up as unstructured JSON, rendered
inside a `<textarea ...></textarea>`. This definitely is not what we want! Instead we create a typical Django Form using
the alternative class `EntangledModelForm`.

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

In case our form inherits from another `ModelForm`, rewrite the class declarartion as:

```python
class ProductForm(EntangledModelFormMixin, BaseProductForm):
    ...
```

In addition we add a special dictionary named `entangled_fields` to our `Meta`-options. In this dictionary, the key
(here `'properties'`) refers to the JSON-field in our model `Product`. The value (here `['color', 'size', 'tenant']`)
is a list of named form fields, declared in our form- or base-class of thereof. This allows us to assign all standard
Django form fields to arbitrary JSON fields declared in our Django model. Moreover, we can even use a `ModelChoiceField`
or a `ModelMultipleChoiceField` to refer to another model object using a
[generic relation](https://docs.djangoproject.com/en/stable/ref/contrib/contenttypes/#generic-relations)

Since in this form we also want to access the non-JSON fields from our Django model, we add a list named
`untangled_fields` to our `Meta`-options. In this list, (here `['name', 'price']`) we refer to the non-JSON fields
in our model `Product`. From both of these iterables, `entangled_fields` and `untangled_fields`, the parent class
`EntangledModelForm` then builds the `Meta`-option `fields`, otherwise required. Therefore you should not
use `fields` to declare this list, but rather rely on `entangled_fields` and `untangled_fields`.

We can use this form in any Django form view. A typical use-case, is the built-in Django `ModelAdmin`:

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


## Nested Data Structures

Sometimes it can be desirable to store the data in a nested hierarchie of dictionaries, rather than having all
attribute-value-pairs in the first level of our JSON field. This can for instance be handy when merging more than one
form, all themselves ineriting from `EntangledModelFormMixin`.

Say that we have different types of products, all of which share the same base product form:

```python
from django.contrib.auth import get_user_model
from django.forms import models
from entangled.forms import EntangledModelFormMixin
from .models import Product

class BaseProductForm(EntangledModelFormMixin):
    tenant = models.ModelChoiceField(
        queryset=get_user_model().objects.filter(is_staff=True),
    )

    class Meta:
        model = Product
        entangled_fields = {'properties': ['tenant']}
        untangled_fields = ['name', 'price']
```

In order to specialize our base product towards, say clothing, we typically would inherit from the base form
and add some additional fields, here `color` and `size`:

```python
from django.forms import fields
from .forms import BaseProductForm
from .models import Product

class ClothingProductForm(BaseProductForm):
    color = fields.RegexField(
        regex=r'^#[0-9a-f]{6}$',
    )

    size = fields.ChoiceField(
        choices=[('s', "small"), ('m', "medium"), ('l', "large"), ('xl', "extra large")],
    )

    class Meta:
        model = Product
        entangled_fields = {'properties': ['color', 'size']}
        retangled_fields = {'color': 'variants.color', 'size': 'variants.size'}
```

By adding a name mapping from our existing field names, we can group the fields `color` and `size`
into a sub-dictionary named `variants` inside our `properties` fields. Such a field mapping is
declared through the optional Meta-option `retangled_fields`. In this dictionary, all entries are
optional; if a field name is missing, it just maps to itself.

This mapping table can also be used to map field names to other keys inside the resulting JSON
datastructure. This for instance is handy to map fields containg an underscore into field-names
containing instead a dash. 


## Caveats

Due to the nature of JSON, indexing and thus building filters or sorting rules based on the fields content is not as
simple, as with standard model fields. Therefore, this approach is best suited, if the main focus is to store data,
rather than digging through data.

Foreign keys are stored as `"fieldname": {"model": "appname.modelname", "pk": 1234}` in our JSON field, meaning that
we have no database constraints. If a target object is deleted, that foreign key points to nowhere. Therefore always
keep in mind, that we don't have any referential integrity and hence must write our code in a defensive manner.


[![Twitter Follow](https://img.shields.io/twitter/follow/jacobrief?style=social)](https://twitter.com/jacobrief)
