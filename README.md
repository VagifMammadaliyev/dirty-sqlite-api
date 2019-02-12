# Dirty SQLite Api

### Disclaimer

This is a very dirty and fast implementation of interface for SQLite Database. Don't rely on this for big applications. But this can make a deal for smaller applications!

Note: This code is tested with Python 3.7

## Quick help

Main code is in `api.py` file. This interface supposed to make easier and not so boring some SQL routines, like creating tables, adding columns, inserting data. It is something like ORM from Django.

### Tutorial

For example if you want to create table with name Person and columns for id, name and age, then:
```python
class Person:
    id = fields.IntegerField('id', is_pk=True) # primary key column
    name = fields.TextField('name', required=True) # required column
    age = fields.IntegerField('age', required=True)
    money = fields.RealField('money', required=True, default=55.5) # column with default value

# Now connect to database and create that table
db = SQLDatabase('test.db')
db.table(Person) 
```

By passing class as argument you are adding a new attribute - `objects` (which is set of queries).
If you already have Person table in your database, then `table()` method will simply add `objects` attribute if it does not exist
You now can use `objects` to interact with database:

```python
Person.objects.all() # Returns list of QueryObject's 
                     # which is python objects with columns' values as its attributes
Person.objects.create(name='Mike', age=20, money=300.5)
mike = Person.objects.get('name="Mike" and age=20')
```

Here `get()` method returns only one `QueryObject` that is first of rows satisfied condition in parentheses.
If you want to get multiple rows as `QueryObject` then use `Person.objects.filter()` method. It must return a list.

You also can update row of data:

```python
Person.objects.update('name="Mike"', name='John')
```

First argument is which element to update, it will be passed to `get()` method, so you already know, that if multiple rows satisfies condition, only the first one is updated. To update multiple rows, you can use very inefficient way (because it is the only one :D):

```python
objects = SomeTable.objects.filter('age > 10')

for obj in objects:
    if obj.name == 'Someone':
        SomeTable.objects.update('name="Someone"', name='NotSomeone')
```

You also can add some columns to your already existing table:

```python
# Add attribute to your table-class
# Be sure to mention default value for column if you add new column that is required
Person.new_column = fields.TextField('new', required=True, default='default value')

db.table(Person, update_table=True)
```

There is also a method for deleting row called `delete()` and it also can delete only one row at a time. So you can use the same tactic used for updating rows to delete multiple rows.

You are not able to fully interact with database, but at least you can. And it is very unefficient implementation and not suitable for big projects!

Note: Be sure to escape passed values manually! :(