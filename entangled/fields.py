from django.forms.fields import Field, MultiValueField
from django.forms.boundfield import BoundField, BoundWidget
from django.core.exceptions import FieldError
from django.utils.html import conditional_escape, mark_safe

from entangled.widgets import InvisibleWidget, EntangledFormWidget


class EntangledInvisibleField(Field):
    """
    A pseudo field, which can be used to mimic a field value, which actually is not rendered inside the form.
    """
    widget = InvisibleWidget

    def __init__(self, required=False, *args, **kwargs):
        super().__init__(required=required, *args, **kwargs)


class EntangledFormField(MultiValueField):
    """
    A special field used to nest forms of type EntangledForm into a field used by
    a parent form of type EntangledForm.

    @:param form: A form of type :class:`entangled.forms.EntangledForm`
    """
    def __init__(self, form, *args, **kwargs):
        from entangled.forms import EntangledForm

        if issubclass(form, EntangledForm):
            form = form()
        if not isinstance(form, EntangledForm):
            raise FieldError("The first parameter of an EntangledFormField must be of type EntangledModelForm.")
        fields = form.fields.values()
        widgets = [f.widget for f in fields]
        kwargs.setdefault('widget', EntangledFormWidget(form, widgets))
        super().__init__(fields, *args, **kwargs)

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value

    def get_bound_field(self, form, field_name):
        bf = super().get_bound_field(form, field_name)
        if not bf.field.widget._html_field_kwargs['normal_row'].endswith('</li>'):
            # prevent printing the nested label
            bf.label = None
        return bf
