from django.forms.fields import Field
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


class EntangledBoundField(BoundField):
    label = None

    def __init__(self, form, field, name):
        self.form = form
        self.field = field
        self.name = name
        self.html_name = form.add_prefix(name)
        self.html_initial_name = form.add_initial_prefix(name)
        self.html_initial_id = form.add_initial_prefix(self.auto_id)
        self.help_text = field.help_text or ''

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        """
        Render the EntangledFormField by rendering its subfields as form.
        """
        output = []
        subform = self.field.subform
        subform.prefix = self.name
        normal_row, error_row, row_ender, help_text_html, errors_on_separate_row = self.field._html_output_kwargs.values()
        for field_name, subfield in subform.fields.items():
            html_class_attr = ''
            bf = subfield.get_bound_field(subform, field_name) # subform[field_name]
            bf_errors = subform.error_class(bf.errors)
            # Create a 'class="..."' attribute if the row should have any
            # CSS classes applied.
            css_classes = bf.css_classes()
            if css_classes:
                html_class_attr = ' class="%s"' % css_classes

            if errors_on_separate_row and bf_errors:
                output.append(error_row % str(bf_errors))

            if bf.label:
                label = conditional_escape(bf.label)
                label = bf.label_tag(label) or ''
            else:
                label = ''

            if subfield.help_text:
                help_text = help_text_html % subfield.help_text
            else:
                help_text = ''

            output.append(normal_row % {
                'errors': bf_errors,
                'label': label,
                'field': bf,
                'help_text': help_text,
                'html_class_attr': html_class_attr,
                'css_classes': css_classes,
                'field_name': bf.html_name,
            })
        return mark_safe('\n'.join(output))

    def build_widget_attrs(self, attrs, widget=None):
        attrs = super().build_widget_attrs(attrs, widget)
        return attrs


class EntangledFormField(Field):
    """
    A special field used to nest forms of type EntangledForm into an other field.
    """
    def __init__(self, form, *args, **kwargs):
        from entangled.forms import EntangledForm

        if issubclass(form, EntangledForm):
            self.subform = form()
        elif isinstance(form, EntangledForm):
            self.subform = form
        else:
            raise FieldError("The first parameter of an EntangledFormField must be of type EntangledModelForm.")
        # kwargs.setdefault('widget', EntangledFormWidget(self))
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value

    def get_bound_field(self, form, field_name):
        return EntangledBoundField(form, self, field_name)
