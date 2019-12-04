from django.forms.widgets import Widget


class InvisibleWidget(Widget):
    @property
    def is_hidden(self):
        return True

    def value_omitted_from_data(self, data, files, name):
        return False

    def render(self, name, value, attrs=None, renderer=None):
        return ''


class EntangledFormWidget(Widget):
    def __init__(self, form, attrs=None):
        self._entangled_form = form
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        return 'render EntangledFormWidget'
