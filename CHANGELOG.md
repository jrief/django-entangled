## Changes

- 0.6.2
  * Fix regression introduced in 0.6: In `EntangledModelFormMixin` use `_clean_form` to untangle fields rather than
    `_post_clean` to remain compatible with Django's formsets.

- 0.6.1
  * Fix: Fully exclude fields not listed in `Meta.entangled_fields`, `Meta.untangled_field` or `Meta.fields`.

- 0.6
  * Add support for Django's `modelform_factory` and `Meta.fields` option.
  * Add support for Django 5.0, 5.1
  * Drop support for Django 4.1, 4.0, 3.2, 2.2

- 0.5.4
  * Add support for Django-4.1 and 4.2.
  * Confirm support for Python 3.11

- 0.5.3
  * Load external JSONField if used with Django-2.2.

- 0.5.2
  * Revert "Specify exceptions in helper functions". It introduced
    a regression in other packages using it.

- 0.5.1
  * Specify exceptions in helper functions.
  * Allow initial data to be missing from entangled fields.

- 0.5
  * Drop support for Django versions below 3.2.
  * Drop support for external jsonfield implementations.

- 0.4
  * Allow nested structures for stored JSON data.
  * Functions `get_related_object` and `get_related_queryset` have been moved from module
    `entangled.forms` into module `entangled.utils`.

- 0.3.1
  * No functional changes.
  * Add support for Django-3.1 and Python-3.8.
  * Drop support for Django<2.1 and Python-3.5.

- 0.3
  * Add support for `ModelMultipleChoiceField`.
  * Fix: Make a deep copy of `entangled_fields` and `untangled_fields` before merging.
  * Add covenience class `EntangledModelForm`.
  * Moving data from entangled fields onto their compressed representation, now is performed after
    the form has performed its own `clean()`-call, so that accessing form fields is more natural.
  * Add functions `get_related_object` and `get_related_queryset` to get the model object from its
    JSON representation.

- 0.2
  * Introduce `Meta`-option `untangled_fields`, because the approach in 0.1 didn't always work.
  * Use `formfield()`-method, for portability reasons with Django's Postgres JSON field.

- 0.1
  * Initial release.
