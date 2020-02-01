from django.forms.widgets import Widget, MultiWidget
from django.utils.html import format_html


class InvisibleWidget(Widget):
    @property
    def is_hidden(self):
        return True

    def value_omitted_from_data(self, data, files, name):
        return False

    def render(self, name, value, attrs=None, renderer=None):
        return ''


class EntangledFormWidget(MultiWidget):
    def __init__(self, form, widgets, attrs=None):
        super().__init__(widgets, attrs)
        self._entangled_form = form

    def render(self, name, value, attrs=None, renderer=None):
        kwargs = dict(self._html_field_kwargs)
        if kwargs['normal_row'].endswith('</td></tr>'):
            # prevent nesting of table elements.
            kwargs['normal_row'] = '<th>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td>'
        elif kwargs['normal_row'].endswith('</p>'):
            # prevent nesting of paragraph elements.
            kwargs['normal_row'] = '%(label)s %(field)s%(help_text)s'
        output = self._entangled_form._html_output(**kwargs)
        if self._html_field_kwargs['normal_row'].endswith('</li>'):
            # wrap nested entangled fields into an <ul>-element.
            output = format_html('<ul>{}</ul>', output)
        return output

    def decompress(self, value):
        if value:
            return [value[0], value[1]]
        return [None, None]
