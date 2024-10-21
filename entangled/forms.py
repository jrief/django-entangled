import itertools
import traceback
from copy import deepcopy, copy
from warnings import warn

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.forms.models import (
    ModelChoiceField,
    ModelMultipleChoiceField,
    ModelFormMetaclass,
    ModelForm,
)
from django.forms.fields import Field
from django.forms.widgets import Widget
from django.db.models import JSONField, Model, QuerySet


class InvisibleWidget(Widget):
    @property
    def is_hidden(self):
        return True

    def value_omitted_from_data(self, data, files, name):
        return False

    def render(self, name, value, attrs=None, renderer=None):
        return ""


class EntangledField(Field):
    """
    A pseudo field, which can be used to mimic a field value, which actually is not rendered inside the form.
    """
    widget = InvisibleWidget

    def __init__(self, required=False, *args, **kwargs):
        # EntangledField is not required by default
        super().__init__(required=required, *args, **kwargs)


class EntangledFormMetaclass(ModelFormMetaclass):
    def __new__(cls, class_name, bases, attrs):
        attrs.setdefault("Meta", type("Meta", (), {}))
        untangled_fields = list(getattr(attrs["Meta"], "untangled_fields", []))
        entangled_fields = deepcopy(getattr(attrs["Meta"], "entangled_fields", {}))
        retangled_fields = deepcopy(getattr(attrs["Meta"], "retangled_fields", {}))

        # Merge untangled and entangled fields from base classes
        for base in bases:
            if hasattr(base, "_meta"):
                untangled_fields = getattr(base._meta, "untangled_fields", []) + untangled_fields
                for key, fields in getattr(base._meta, "entangled_fields", {}).items():
                    existing_fields = entangled_fields.setdefault(key, [])
                    entangled_fields[key] = [
                                                field for field in fields if field not in existing_fields
                                            ] + existing_fields
        for entangled_list in entangled_fields.values():
            for ef in entangled_list:
                if ef not in retangled_fields:
                    retangled_fields[ef] = ef

        # Modify entangled fields to respect Meta.fields and Meta.exclude
        fields = getattr(attrs["Meta"], "fields", None)
        # Adjust fields
        if entangled_fields:
            if fields == forms.ALL_FIELDS or fields is None:
                # This includes the case where no Meta.fields is specified
                # Explicitly list the entangled and untangled fields - remove excluded fields

                fields_to_delete = set(getattr(attrs["Meta"], "exclude", []))
                for field_name in entangled_fields.keys():
                    entangled_fields[field_name] = [
                        field for field in entangled_fields[field_name] if field not in fields_to_delete
                    ]
                    attrs[field_name] = EntangledField()
                attrs["Meta"].fields = (
                    fields or
                    cls._create_fields_option(untangled_fields, entangled_fields, fields_to_delete)
                )
            else:
                fieldset = list(fields)  # Create a copy
                # Alter remove fields not listed in Meta.fields
                fields_to_delete = set(itertools.chain(*entangled_fields.values())) - set(fieldset)
                fields_to_delete.update(set(untangled_fields) - set(fieldset))
                # Remove fields not listed in Meta.fields from entangled_fields
                for field_name in entangled_fields.keys():
                    entangled_fields[field_name] = [
                        field for field in entangled_fields[field_name] if field in fieldset
                    ]
                    # Ensure the JSON field is declared as EntangledField
                    attrs[field_name] = EntangledField() if entangled_fields[field_name] else None
                # Add the json fields needed to the fieldset
                for field, field_list in entangled_fields.items():
                    if field_list:
                        fieldset.append(field)
                attrs["Meta"].fields = fieldset

            # Shadow fields not listed in Meta.fields
            for field_name in fields_to_delete:
                attrs[field_name] = None

        new_class = super().__new__(cls, class_name, bases, attrs)

        # perform some model checks
        for modelfield_name in entangled_fields.keys():
            for field_name in entangled_fields[modelfield_name]:
                assert (
                    field_name in new_class.base_fields
                ), "Field {} listed in `{}.Meta.entangled_fields['{}']` is missing in Form declaration".format(
                    field_name, class_name, modelfield_name
                )

        new_class._meta.entangled_fields = entangled_fields
        new_class._meta.untangled_fields = untangled_fields
        new_class._meta.retangled_fields = retangled_fields
        return new_class

    @classmethod
    def _create_fields_option(cls, untangled_fields, entangled_fields, fields_to_delete):
        fields = list(untangled_fields)  # creates a copy for modification
        for entangled in entangled_fields.values():
            fields += entangled
        fields += list(entangled_fields.keys())
        for field in fields_to_delete:
            if field in fields:
                fields.remove(field)
        return fields


class EntangledModelFormMixin(metaclass=EntangledFormMetaclass):
    def __init__(self, *args, **kwargs):
        opts = self._meta
        if "instance" in kwargs and kwargs["instance"]:
            initial = kwargs.get("initial", {})
            for field_name, assigned_fields in opts.entangled_fields.items():
                for af in assigned_fields:
                    reference = getattr(kwargs["instance"], field_name)
                    try:
                        for part in opts.retangled_fields[af].split("."):
                            reference = reference[part]
                    except (KeyError, TypeError):
                        continue
                    if isinstance(self.base_fields[af], ModelMultipleChoiceField):
                        try:
                            Model = apps.get_model(reference["model"])
                            initial[af] = Model.objects.filter(
                                pk__in=reference["p_keys"]
                            )
                        except (KeyError, TypeError):
                            pass
                    elif isinstance(self.base_fields[af], ModelChoiceField):
                        try:
                            Model = apps.get_model(reference["model"])
                            initial[af] = Model.objects.get(pk=reference["pk"])
                        except (KeyError, ObjectDoesNotExist, TypeError):
                            pass
                    else:
                        initial[af] = reference
            kwargs.setdefault("initial", initial)
        super().__init__(*args, **kwargs)

    def _clean_form(self):
        opts = self._meta
        super()._clean_form()
        cleaned_data = {
            f: self.cleaned_data[f]
            for f in opts.untangled_fields
            if f in self.cleaned_data
        }
        for field_name, assigned_fields in opts.entangled_fields.items():
            # Keep other fields in JSON
            if self.instance and hasattr(self.instance, field_name):
                cleaned_data[field_name] = getattr(self.instance, field_name) or {}
            else:
                cleaned_data[field_name] = {}
            for af in assigned_fields:
                if af not in self.cleaned_data:
                    continue
                bucket = cleaned_data[field_name]
                af_parts = opts.retangled_fields[af].split(".")
                for part in af_parts[:-1]:
                    bucket = bucket.setdefault(part, {})
                part = af_parts[-1]
                if isinstance(
                    self.base_fields[af], ModelMultipleChoiceField
                ) and isinstance(self.cleaned_data[af], QuerySet):
                    meta = self.cleaned_data[af].model._meta
                    value = {
                        "model": "{}.{}".format(meta.app_label, meta.model_name),
                        "p_keys": list(
                            self.cleaned_data[af].values_list("pk", flat=True)
                        ),
                    }
                elif isinstance(self.base_fields[af], ModelChoiceField) and isinstance(
                    self.cleaned_data[af], Model
                ):
                    meta = self.cleaned_data[af]._meta
                    value = {
                        "model": "{}.{}".format(meta.app_label, meta.model_name),
                        "pk": self.cleaned_data[af].pk,
                    }
                else:
                    value = self.cleaned_data[af]
                bucket[part] = value
        self.cleaned_data = cleaned_data


class EntangledModelForm(EntangledModelFormMixin, ModelForm):
    """
    A convenience class to create entangled model forms.
    """


def get_related_object(scope, field_name):
    from . import utils

    warn("Please import 'get_related_object' from entangled.utils", DeprecationWarning)
    return utils.get_related_object(scope, field_name)


def get_related_queryset(scope, field_name):
    from . import utils

    warn(
        "Please import 'get_related_queryset' from entangled.utils", DeprecationWarning
    )
    return utils.get_related_queryset(scope, field_name)
