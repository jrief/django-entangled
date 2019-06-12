import re
from copy import deepcopy
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField, ModelFormMetaclass, ModelForm
from django.forms.fields import Field
from django.forms.widgets import Widget
from django.db.models import Model
from django.db.models.query import QuerySet


class InvisibleWidget(Widget):
    @property
    def is_hidden(self):
        return True

    def value_omitted_from_data(self, data, files, name):
        return False

    def render(self, name, value, attrs=None, renderer=None):
        return ''


class EntangledField(Field):
    """
    A pseudo field, which can be used to mimic a field value, which actually is not rendered inside the form.
    """
    widget = InvisibleWidget

    def __init__(self, required=False, *args, **kwargs):
        super().__init__(required=required, *args, **kwargs)


class EntangledFormMetaclass(ModelFormMetaclass):
    def __new__(cls, class_name, bases, attrs):
        def formfield_callback(modelfield, **kwargs):
            if modelfield.name in entangled_fields.keys():
                # there are so many different implementations for JSON fields,
                # that we just check if "json" is part of the formfield's classname.
                assert re.search('json', modelfield.formfield().__class__.__name__, re.IGNORECASE), \
                    "Field `{}.{}` doesn't seem to be JSON serializable.".format(class_name, modelfield.name)
                return EntangledField(show_hidden_initial=False)
            return modelfield.formfield(**kwargs)

        if 'Meta' in attrs:
            untangled_fields = list(getattr(attrs['Meta'], 'untangled_fields', []))
            entangled_fields = deepcopy(getattr(attrs['Meta'], 'entangled_fields', {}))
        else:
            untangled_fields, entangled_fields = [], {}
        if entangled_fields:
            fieldset = set(getattr(attrs['Meta'], 'fields', []))
            fieldset.update(untangled_fields)
            fieldset.update(entangled_fields.keys())
            attrs['Meta'].fields = list(fieldset)
            attrs['formfield_callback'] = formfield_callback
        new_class = super().__new__(cls, class_name, bases, attrs)

        # perform some model checks
        for modelfield_name in entangled_fields.keys():
            for field_name in entangled_fields[modelfield_name]:
                assert field_name in new_class.base_fields, \
                     "Field {} listed in `{}.Meta.entangled_fields['{}']` is missing in Form declaration".format(
                        field_name, class_name, modelfield_name)

        # merge untangled and entangled fields from base classes
        for base in bases:
            if hasattr(base, '_meta'):
                untangled_fields.extend(getattr(base._meta, 'untangled_fields', []))
                for key, fields in getattr(base._meta, 'entangled_fields', {}).items():
                    entangled_fields.setdefault(key, [])
                    entangled_fields[key].extend(fields)
        new_class._meta.entangled_fields = entangled_fields
        new_class._meta.untangled_fields = untangled_fields
        return new_class


class EntangledModelFormMixin(metaclass=EntangledFormMetaclass):
    def __init__(self, *args, **kwargs):
        opts = self._meta
        if 'instance' in kwargs and kwargs['instance']:
            initial = kwargs['initial'] if 'initial' in kwargs else {}
            for field_name, assigned_fields in opts.entangled_fields.items():
                reference = getattr(kwargs['instance'], field_name)
                for af in assigned_fields:
                    if af in reference:
                        if isinstance(self.base_fields[af], ModelMultipleChoiceField):
                            try:
                                Model = apps.get_model(reference[af]['model'])
                                initial[af] = Model.objects.filter(pk__in=reference[af]['p_keys'])
                            except (KeyError, TypeError):
                                pass
                        elif isinstance(self.base_fields[af], ModelChoiceField):
                            try:
                                Model = apps.get_model(reference[af]['model'])
                                initial[af] = Model.objects.get(pk=reference[af]['pk'])
                            except (KeyError, ObjectDoesNotExist, TypeError):
                                pass
                        else:
                            initial[af] = reference[af]
            kwargs.setdefault('initial', initial)
        super().__init__(*args, **kwargs)

    def _clean_form(self):
        opts = self._meta
        super()._clean_form()
        cleaned_data = {f: self.cleaned_data[f] for f in opts.untangled_fields if f in self.cleaned_data}
        for field_name, assigned_fields in opts.entangled_fields.items():
            cleaned_data[field_name] = {}
            for af in assigned_fields:
                if af not in self.cleaned_data:
                    continue
                if isinstance(self.base_fields[af], ModelMultipleChoiceField) and isinstance(self.cleaned_data[af], QuerySet):
                    opts = self.cleaned_data[af].model._meta
                    cleaned_data[field_name][af] = {
                        'model': '{}.{}'.format(opts.app_label, opts.model_name),
                        'p_keys': list(self.cleaned_data[af].values_list('pk', flat=True)),
                    }
                elif isinstance(self.base_fields[af], ModelChoiceField) and isinstance(self.cleaned_data[af], Model):
                    opts = self.cleaned_data[af]._meta
                    cleaned_data[field_name][af] = {
                        'model': '{}.{}'.format(opts.app_label, opts.model_name),
                        'pk': self.cleaned_data[af].pk,
                    }
                else:
                    cleaned_data[field_name][af] = self.cleaned_data[af]
        self.cleaned_data = cleaned_data


class EntangledModelForm(EntangledModelFormMixin, ModelForm):
    """
    A convenience class to create entangled model forms.
    """


def get_related_object(scope, field_name):
    """
    Returns the related field, referenced by the content of a ModelChoiceField.
    """
    try:
        Model = apps.get_model(scope[field_name]['model'])
        relobj = Model.objects.get(pk=scope[field_name]['pk'])
    except (KeyError, ObjectDoesNotExist, TypeError):
        relobj = None
    return relobj


def get_related_queryset(scope, field_name):
    """
    Returns the related queryset, referenced by the content of a ModelChoiceField.
    """
    try:
        Model = apps.get_model(scope[field_name]['model'])
        queryset = Model.objects.filter(pk__in=scope[field_name]['p_keys'])
    except (KeyError, TypeError):
        queryset = None
    return queryset
