## Changes

- 0.4
  * Allow nested structures for stored JSON data.

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
