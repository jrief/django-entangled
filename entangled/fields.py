from django.forms.fields import Field
from django.core.exceptions import FieldError

from entangled.forms import EntangledModelFormMixin


class EntangledFormField(Field):
    def __init__(self, form_class, *args, **kwargs):
        if not issubclass(form_class, EntangledModelFormMixin):
            raise FieldError("The first parameter of an EntangledFormField must be of type EntangledModelForm.")
        self._entangled_form_class = form_class
        super().__init__(*args, **kwargs)
