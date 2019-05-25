import pytest
from django.forms import fields
from django.forms.models import ModelForm
from entangled.models import EntangledModelFormMixin
from .models import FreeModel


class MyForm(EntangledModelFormMixin, ModelForm):
    test = fields.CharField()
    on_off = fields.BooleanField()
    field_order = ['test', 'anything', 'on_off']

    class Meta:
        model = FreeModel
        fields = ['anything']
        entangled_fields = {'glossary': ['test', 'on_off']}


def test_unbound_form():
    my_form = MyForm()
    assert my_form.is_bound is False
    expected = """
<li><label for="id_test">Test:</label> <input type="text" name="test" required id="id_test"></li>
<li><label for="id_anything">Anything:</label> <input type="text" name="anything" maxlength="5" id="id_anything"></li>
<li><label for="id_on_off">On off:</label> <input type="checkbox" name="on_off" required id="id_on_off"></li>
    """.strip()
    assert my_form.as_ul() == expected


@pytest.mark.django_db
def test_bound_form():
    data = {'test': "Test", 'on_off': True}
    my_form = MyForm(data=data)
    assert my_form.is_bound
    assert my_form.is_valid()
    instance = my_form.save()
    assert instance.glossary == data


def test_invalid_form():
    data = {'test': "Test"}
    my_form = MyForm(data=data)
    assert my_form.is_bound
    assert my_form.is_valid() is False
    expected = {
        'on_off': ['This field is required.']
    }
    assert my_form.errors == expected


@pytest.mark.django_db
def test_instance_form():
    instance = FreeModel.objects.create(glossary={'test': "Test", 'on_off': True})
    my_form = MyForm(instance=instance)
    assert my_form.is_bound is False
    expected = """
<li><label for="id_test">Test:</label> <input type="text" name="test" value="Test" required id="id_test"></li>
<li><label for="id_anything">Anything:</label> <input type="text" name="anything" maxlength="5" id="id_anything"></li>
<li><label for="id_on_off">On off:</label> <input type="checkbox" name="on_off" required id="id_on_off" checked></li>
    """.strip()
    assert my_form.as_ul() == expected
