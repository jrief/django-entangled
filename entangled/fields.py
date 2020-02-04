from django.forms.fields import Field
from django.forms.widgets import Widget
from django.core.exceptions import FieldError


class InvisibleWidget(Widget):
    @property
    def is_hidden(self):
        return True

    def value_omitted_from_data(self, data, files, name):
        return False

    def render(self, name, value, attrs=None, renderer=None):
        return ''


class EntangledInvisibleField(Field):
    """
    A pseudo field, which can be used to mimic a field value, which actually is not rendered inside the form.
    """
    widget = InvisibleWidget

    def __init__(self, required=False, *args, **kwargs):
        super().__init__(required=required, *args, **kwargs)


class EntangledFormField(Field):
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
        super().__init__(*args, **kwargs)
        self._entangled_form = form
