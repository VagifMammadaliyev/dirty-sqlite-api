import os
import fields
import sqlite3
import exceptions
from api import SQLDatabase as database

DB_FILENAME = 'test_database'

def setup(func):
    def wrapped(*args, **kwargs):
        d = open(DB_FILENAME, 'x')
        func(*args, **kwargs)
        d.close()
        os.remove(DB_FILENAME)
    return wrapped

@setup
def test_create_table():
    db = database(DB_FILENAME)
    class Person:
        id = fields.IntegerField('id', is_pk=True)
        name = fields.TextField('name', required=True)
        age = fields.IntegerField('age', required=True)
        money = fields.RealField('money', required=False, default=0.0)
        item_amount = fields.IntegerField('i_amount', required=True, default=100)
    db.table(Person)
    assert hasattr(Person, 'objects') == True
    db.cursor.execute('PRAGMA table_info(Person)')
    info = db.cursor.fetchall()
    assert len(info) == 5
    names = [item[1] for item in info]
    assert 'id' in names
    assert 'name' in names
    assert 'age' in names
    assert 'money' in names
    assert 'i_amount' in names
    types = [item[2] for item in info]
    assert 'integer' == types[0].lower()
    assert 'text' == types[1].lower()
    assert 'integer' == types[2].lower()
    assert 'real' == types[3].lower()
    assert 'integer' == types[4].lower()
    notnulls = [item[3] for item in info]
    assert notnulls[0] == 0
    assert notnulls[1] == 1
    assert notnulls[2] == 1
    assert notnulls[3] == 0
    assert notnulls[4] == 1
    defaults = [item[4] for item in info]
    assert defaults[0] == None
    assert defaults[1] == None
    assert defaults[2] == None
    assert defaults[3] == str(0.0)
    assert defaults[4] == str(100)
    is_pks = [item[5] for item in info]
    assert is_pks[0] == 1
    assert is_pks[1] == 0
    assert is_pks[2] == 0
    assert is_pks[3] == 0
    assert is_pks[4] == 0

@setup
def test_add_column():
    db = database(DB_FILENAME)
    class Person:
        id = fields.IntegerField('id', is_pk=True)
    db.table(Person)
    db.cursor.execute('PRAGMA table_info(Person)')
    info = db.cursor.fetchall()
    assert len(info) == 1
    Person.name = fields.TextField('name', required=False)
    db.table(Person, update_table=True)
    db.cursor.execute('PRAGMA table_info(Person)')
    info = db.cursor.fetchall()
    assert len(info) == 2

@setup
def test_add_column_without_default():
    db = database(DB_FILENAME)
    class Person:
        id = fields.IntegerField('id', is_pk=True)
    db.table(Person)
    Person.name = fields.TextField('name', required=True, default=None)
    try:
        db.table(Person, update_table=True)
    except exceptions.NewColumnWithoutDefault:
        assert True
    else:
        assert False

@setup
def test_create_object():
    db = database(DB_FILENAME)
    class Person:
        id = fields.IntegerField('id', is_pk=True)
        name = fields.TextField('name', required=True)
        age = fields.IntegerField('age', required=False, default=20)
    db.table(Person)
    assert len(Person.objects.all()) == 0
    Person.objects.create(name='mike', age=10)
    assert len(Person.objects.all()) == 1

@setup
def test_create_object_without_required_column():
    db = database(DB_FILENAME)
    class Person:
        id = fields.IntegerField('id', is_pk=True)
        name = fields.TextField('name', required=False)
        age = fields.IntegerField('age', required=True)
    db.table(Person)
    try:
        Person.objects.create(name='mike')
    except sqlite3.IntegrityError:
        assert True
    else:
        assert False

@setup
def test_update_object():
    db = database(DB_FILENAME)
    class Person:
        id = fields.IntegerField('id', is_pk=True)
        name = fields.TextField('name', required=False)
    db.table(Person)
    Person.objects.create(name='john')
    assert len(Person.objects.all()) == 1
    Person.objects.update('name="john"', name='mike')
    assert len(Person.objects.all()) == 1
    assert Person.objects.all()[0].name == 'mike'

@setup
def test_delete_object():
    db = database(DB_FILENAME)
    class Person:
        id = fields.IntegerField('id', is_pk=True)
        name = fields.TextField('name')
    db.table(Person)
    Person.objects.create(name='mike')
    assert len(Person.objects.all()) == 1
    Person.objects.delete('name="mike"')
    assert len(Person.objects.all()) == 0

@setup
def test_update_delete_unexisting_row():
    db = database(DB_FILENAME)
    class Person:
        id = fields.IntegerField('id', is_pk=True)
        name = fields.TextField('name')
    db.table(Person)
    try:
        Person.objects.update('id=1', name='mike')
    except exceptions.DoesNotExists:
        assert True
    else:
        assert False
    try:
        Person.objects.delete('id=1')
    except exceptions.DoesNotExists:
        assert True
    else:
        assert False

if __name__ == '__main__':
    tests = [globals()[key] for key in globals().keys() if key.startswith('test_')]
    count = 0
    for test in tests:
        test()
        count += 1
    print('Ran {0} {1}'.format(count, 'test' if count == 1 else 'tests'))
