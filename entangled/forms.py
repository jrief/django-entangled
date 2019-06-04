import re
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import ModelChoiceField, ModelFormMetaclass, ModelForm
from django.forms.fields import Field
from django.forms.widgets import Widget
from django.db.models import Model


class InvisibleWidget(Widget):
    @property
    def is_hidden(self):
        return True

    def value_omitted_from_data(self, data, files, name):
        return False

    def render(self, name, value, attrs=None, renderer=None):
        return ''


class EntangledField(Field):
    widget = InvisibleWidget


class EntangledFormMetaclass(ModelFormMetaclass):
    def __new__(cls, class_name, bases, attrs):
        def formfield_callback(modelfield, **kwargs):
            if modelfield.name in entangled_fields.keys():
                # there are so many different implementations for JSON fields, that we just check
                # if "json" is part of the formfield's classname.
                assert re.search('json', modelfield.formfield().__class__.__name__, re.IGNORECASE), \
                    "Field `{}.{}` doesn't seem to be JSON serializable.".format(class_name, modelfield.name)
                return EntangledField(required=False, show_hidden_initial=False)
            return modelfield.formfield(**kwargs)

        entangled_fields = getattr(attrs.get('Meta'), 'entangled_fields', None)
        if entangled_fields:
            fieldset = set(getattr(attrs['Meta'], 'fields', []))
            untangled_fields = getattr(attrs['Meta'], 'untangled_fields', [])
            fieldset.update(untangled_fields)
            fieldset.update(entangled_fields.keys())
            attrs['Meta'].fields = list(fieldset)
            attrs['formfield_callback'] = formfield_callback
        new_class = super(EntangledFormMetaclass, cls).__new__(cls, class_name, bases, attrs)
        if entangled_fields:
            for modelfield_name in entangled_fields.keys():
                for field_name in entangled_fields[modelfield_name]:
                    assert field_name in new_class.base_fields, \
                         "Field {} listed in `{}.Meta.entangled_fields['{}']` is missing in Form declaration".format(
                            field_name, class_name, modelfield_name)
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
                        if isinstance(self.base_fields[af], ModelChoiceField):
                            try:
                                Model = apps.get_model(reference[af]['model'])
                                initial[af] = Model.objects.get(pk=reference[af]['pk'])
                            except (KeyError, ObjectDoesNotExist, TypeError):
                                pass
                        else:
                            initial[af] = reference[af]
            kwargs.setdefault('initial', initial)
        super().__init__(*args, **kwargs)

    def clean(self):
        opts = self._meta
        cleaned_data = super().clean()
        result = {f: cleaned_data[f] for f in opts.untangled_fields if f in cleaned_data}
        for field_name, assigned_fields in opts.entangled_fields.items():
            result[field_name] = {}
            for af in assigned_fields:
                if af not in cleaned_data:
                    continue
                if isinstance(self.base_fields[af], ModelChoiceField) and isinstance(cleaned_data[af], Model):
                    opts = cleaned_data[af]._meta
                    result[field_name][af] = {
                        'model': '{}.{}'.format(opts.app_label, opts.model_name),
                        'pk': cleaned_data[af].pk,
                    }
                else:
                    result[field_name][af] = cleaned_data[af]
        return result


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
