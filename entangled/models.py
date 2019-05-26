import jsonfield
from django.contrib.contenttypes.models import ContentType, ContentTypeManager
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
        opts = self._meta
        if instance:
            initial = {} if initial is None else initial
            for field_name, assigned_fields in opts.entangled_fields.items():
                for af in assigned_fields:
                    if isinstance(self.base_fields[af], ModelChoiceField):
                        reference = getattr(instance, field_name)[af]
                        app_label, model_name = reference['model'].split('.')
                        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                        try:
                            initial[af] = content_type.get_object_for_this_type(pk=reference['pk'])
                        except ContentType.DoesNotExist:
                            pass
                    else:
                        initial[af] = getattr(instance, field_name)[af]
        super().__init__(instance=instance, initial=initial, *args, **kwargs)

    def clean(self):
        opts = self._meta
        cleaned_data = super().clean()
        result = {}
        for field_name, assigned_fields in opts.entangled_fields.items():
            result[field_name] = {}
            for af in assigned_fields:
                if af not in cleaned_data:
                    continue
                if isinstance(self.base_fields[af], ModelChoiceField):
                    content_type = ContentType.objects.get_for_model(cleaned_data[af])
                    result[field_name][af] = {
                        'model': '{}.{}'.format(content_type.app_label, content_type.model),
                        'pk': cleaned_data[af].pk,
                    }
                else:
                    result[field_name][af] = cleaned_data[af]
        return result
