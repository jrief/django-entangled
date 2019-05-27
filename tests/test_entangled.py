import pytest
from bs4 import BeautifulSoup
from django.forms import fields
from django.forms.models import ModelForm, ModelChoiceField
from entangled.forms import EntangledModelFormMixin
from .models import FreeModel, Title


@pytest.fixture(autouse=True)
def titles():
    Title.objects.create(identifier='Mrs.')
    Title.objects.create(identifier='Mr.')
    Title.objects.create(identifier='n/a')
    return Title.objects.all()


class MyForm(EntangledModelFormMixin, ModelForm):
    test = fields.CharField(initial='Y')
    on_off = fields.BooleanField()
    title = ModelChoiceField(queryset=Title.objects.all(), empty_label=None)
    field_order = ['test', 'anything', 'on_off', 'title']

    class Meta:
        model = FreeModel
        fields = ['anything']
        entangled_fields = {'glossary': ['test', 'on_off', 'title']}


@pytest.mark.django_db
def test_unbound_form(titles):
    my_form = MyForm()
    assert my_form.is_bound is False
    expected = BeautifulSoup("""
        <li><label for="id_test">Test:</label> <input type="text" name="test" value="Y" required id="id_test"></li>
        <li><label for="id_anything">Anything:</label> <input type="text" name="anything" maxlength="5" id="id_anything"></li>
        <li><label for="id_on_off">On off:</label> <input type="checkbox" name="on_off" required id="id_on_off"></li>
        <li><label for="id_title">Title:</label> <select name="title" id="id_title">
          <option value="1">Mrs.</option>        
          <option value="2">Mr.</option>
          <option value="3">n/a</option>
        </select></li>""", features='lxml')
    assert BeautifulSoup(my_form.as_ul(), features='lxml') == expected


@pytest.mark.django_db
def test_bound_form():
    data = {'test': "Test", 'on_off': True, 'title': 2}
    my_form = MyForm(data=data)
    assert my_form.is_bound
    print(my_form._errors)
    assert my_form.is_valid()
    instance = my_form.save()
    expected = dict(data, title={'model': 'tests.title', 'pk': data['title']})
    assert instance.glossary == expected


@pytest.mark.django_db
def test_invalid_form():
    data = {'test': "Test"}
    my_form = MyForm(data=data)
    assert my_form.is_bound
    assert my_form.is_valid() is False
    expected = {
        'on_off': ['This field is required.'],
        'title': ['This field is required.'],
    }
    assert my_form.errors == expected


@pytest.mark.django_db
def test_instance_form():
    glossary = {'test': "Test", 'on_off': True, 'title': {'model': 'tests.title', 'pk': 2}}
    instance = FreeModel.objects.create(glossary=glossary)
    my_form = MyForm(instance=instance)
    assert my_form.is_bound is False
    expected = BeautifulSoup("""
        <li><label for="id_test">Test:</label> <input type="text" name="test" value="Test" required id="id_test"></li>
        <li><label for="id_anything">Anything:</label> <input type="text" name="anything" maxlength="5" id="id_anything"></li>
        <li><label for="id_on_off">On off:</label> <input type="checkbox" name="on_off" required id="id_on_off" checked></li>
        <li><label for="id_title">Title:</label> <select name="title" id="id_title">
          <option value="1">Mrs.</option>
          <option value="2" selected>Mr.</option>
          <option value="3">n/a</option>
        </select></li>""", features='lxml')
    assert BeautifulSoup(my_form.as_ul(), features='lxml') == expected


@pytest.mark.django_db
def test_instance_form_with_fallback():
    instance = FreeModel.objects.create(glossary={'on_off': True})
    my_form = MyForm(instance=instance)
    assert my_form.is_bound is False
    expected = BeautifulSoup("""
        <li><label for="id_test">Test:</label> <input type="text" name="test" value="Y" required id="id_test"></li>
        <li><label for="id_anything">Anything:</label> <input type="text" name="anything" maxlength="5" id="id_anything"></li>
        <li><label for="id_on_off">On off:</label> <input type="checkbox" name="on_off" required id="id_on_off" checked></li>
        <li><label for="id_title">Title:</label> <select name="title" id="id_title">
          <option value="1">Mrs.</option>
          <option value="2">Mr.</option>
          <option value="3">n/a</option>
        </select></li>""", features='lxml')
    assert BeautifulSoup(my_form.as_ul(), features='lxml') == expected


@pytest.mark.django_db
def test_change_form():
    glossary = {'test': "Test", 'on_off': True, 'title': {'model': 'tests.title', 'pk': 2}}
    instance = FreeModel.objects.create(glossary=glossary)
    data = {'test': "XXX", 'on_off': True, 'title': 1}
    my_form = MyForm(data=data, instance=instance)
    assert my_form.is_bound is True
    assert my_form.is_valid() is True
    my_form.save()
    instance.refresh_from_db()
    expected = dict(data, title={'model': 'tests.title', 'pk': data['title']})
    assert instance.glossary == expected
