import jsonfield
from django.forms.models import ModelFormMetaclass
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
                assert isinstance(modelfield, jsonfield.fields.JSONField), \
                    "Field `{}.{}` must be JSON serializable".format(class_name, modelfield.name)
                for field_name in entangled_fields[modelfield.name]:
                    assert field_name in attrs['declared_fields'], \
                        "Field {} listed in `{}.Meta.entangled_fields` is missing".format(field_name, class_name)
                return EntangledField(required=False, show_hidden_initial=False)
            return modelfield.formfield(**kwargs)

        if 'Meta' in attrs and hasattr(attrs['Meta'], 'entangled_fields'):
            entangled_fields = attrs['Meta'].entangled_fields
            if not hasattr(attrs['Meta'], 'fields'):
                attrs['Meta'].fields = []
            for field_name in entangled_fields.keys():
                attrs['Meta'].fields.append(field_name)
            attrs['formfield_callback'] = formfield_callback
        else:
            entangled_fields = None
        new_class = super(EntangledFormMetaclass, cls).__new__(cls, class_name, bases, attrs)
        new_class._meta.entangled_fields = entangled_fields
        return new_class


class EntangledModelFormMixin(metaclass=EntangledFormMetaclass):
    def __init__(self, instance=None, initial=None, *args, **kwargs):
        if instance:
            initial = {} if initial is None else initial
            for field_name in self._meta.entangled_fields:
                initial.update(getattr(instance, field_name))
        super().__init__(instance=instance, initial=initial, *args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        result = {}
        for field_name, assigned_fields in self._meta.entangled_fields.items():
            result[field_name] = {af: cleaned_data[af] for af in assigned_fields if af in cleaned_data}
        return result
