import re
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import ModelChoiceField, ModelFormMetaclass
from django.forms.fields import Field
from django.forms.widgets import Widget


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
                assert re.search('json', modelfield.formfield().__class__.__name__, re.IGNORECASE), \
                    "Field `{}.{}` doesn't seem to be JSON serializable".format(class_name, modelfield.name)
                return EntangledField(required=False, show_hidden_initial=False)
            return modelfield.formfield(**kwargs)

        if 'Meta' in attrs and hasattr(attrs['Meta'], 'entangled_fields'):
            entangled_fields = attrs['Meta'].entangled_fields
            untangled_fields = list(attrs['Meta'].fields)
            attrs['formfield_callback'] = formfield_callback
        else:
            entangled_fields, untangled_fields = {}, []
        new_class = super(EntangledFormMetaclass, cls).__new__(cls, class_name, bases, attrs)
        for modelfield_name in entangled_fields.keys():
            for field_name in entangled_fields[modelfield_name]:
                assert field_name in new_class.base_fields, \
                     "Field {} listed in `{}.Meta.entangled_fields['{}']` is missing in Form declaration".format(
                        field_name, class_name, modelfield_name)
        for field_name in entangled_fields.keys():
            new_class._meta.fields.append(field_name)
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
                            except (KeyError, ObjectDoesNotExist):
                                pass
                        else:
                            initial[af] = reference[af]
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean(self):
        opts = self._meta
        cleaned_data = super().clean()
        result = {f: cleaned_data[f] for f in opts.untangled_fields}
        for field_name, assigned_fields in opts.entangled_fields.items():
            result[field_name] = {}
            for af in assigned_fields:
                if af not in cleaned_data:
                    continue
                if isinstance(self.base_fields[af], ModelChoiceField):
                    opts = cleaned_data[af]._meta
                    result[field_name][af] = {
                        'model': '{}.{}'.format(opts.app_label, opts.model_name),
                        'pk': cleaned_data[af].pk,
                    }
                else:
                    result[field_name][af] = cleaned_data[af]
        return result
