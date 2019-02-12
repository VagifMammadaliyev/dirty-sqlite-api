import sqlite3
import exceptions

def get_fields(table_class):
    """Returns a list of attributes if they are instances of fields.Field subclasses."""
    fd = table_class.__dict__
    fields = [fd[key] for key in fd.keys() if not key.startswith('__') and not callable(fd[key])]
    fields = [field for field in fields if 'Field' in field.__class__.__name__]
    return fields

def make_placeholders(placeholder, count, delimiter=','):
    """Return string of placeholders seperated by delimiter to be formatted later.
    placeholder - string used as placeholder.
    count - count of placeholders in resulting string.
    """
    placeholders = ''
    for i in range(count - 1):
        placeholders += '{}{}'.format(placeholder, delimiter)
    placeholders += '{}'.format(placeholder)
    return placeholders

class QuerySet:
    """Class used to make queries for performing CRUD operations."""
    def __init__(self, table_class, connection, cursor):
        self.table_class = table_class
        self.table_name = table_class.__name__
        self.conn = connection
        self.cursor = cursor
        self.cursor.execute('PRAGMA table_info({})'.format(self.table_name))
        self.cols = self.cursor.fetchall()

    def map(self, rows, cols):
        """
        Returns list of QueryObject's that have the same attributes
        as columns of table QueryObject belongs to.
        """
        objects = []
        d = dict()

        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                d.update({col[1]: row[j]})
            obj = type('QueryObject', (object,), d)
            objects.append(obj())

        return objects

    def commit(self):
        """Commits changes to database"""
        self.conn.commit()

    def all(self):
        """Returns list of all QueryObject's (rows) from table"""
        self.cursor.execute('SELECT * FROM {}'.format(self.table_name))         
        rows = self.cursor.fetchall()
        return self.map(rows, self.cols)

    def create(self, **kwargs):
        """
        Inserts one row of data into table.
        Raises exceptions.NotEnoughValues if no column data is provided
        and there is no columns with default values to insert.
        Raises sqlite3.IntegrityError if not mentioned column with NOT NULL constraint
        """
        passed_count = 0
        keys = [key for key in kwargs.keys()]

        fields = get_fields(self.table_class)
        fields = [field for field in fields if not field.is_pk]
            
        # If no arguments are provided then try to insert row
        # with default values if they exist
        fields_with_default = [field for field in fields if field.default]
        if len(keys) == 0 and not len(fields_with_default) == 0:
            query = 'INSERT INTO {} ({}) VALUES ({!r})'.format(
                self.table_name, 
                fields_with_default[0].name, 
                fields_with_default[0].default
            )
        elif len(keys) == 0 and len(fields_with_default) == 0:
            raise exceptions.NotEnoughValues
            return
        else:
            for passed in kwargs.keys():
                if passed in [field.name for field in fields]:
                    passed_count += 1

            placeholders = make_placeholders('{}', passed_count)
            
            query = 'INSERT INTO {0} ({1})'.format(
                self.table_name, placeholders)
            query = query.format(*keys)

            placeholders = placeholders.format(
                *['?' for i in range(passed_count)])
            query += ' VALUES ({})'.format(placeholders)

        self.cursor.execute(query, [kwargs[key] for key in keys])
        self.commit()

    def get(self, expr):
        """
        Returns one row of data as QueryObject.
        Raises exceptions.DoesNotExists if no row of table satisfies condition.
        """
        query = 'SELECT * FROM {} WHERE {}'.format(self.table_name, expr)
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        try:
            obj = self.map(rows, self.cols)[0]
        except IndexError:
            raise exceptions.DoesNotExists

        return obj

    def filter(self, expr):
        """
        Returns list of rows of data as QueryObject's.
        Returns empty list if no row of table satisfies condition.
        """
        query = 'SELECT * FROM {} WHERE {}'.format(self.table_name, expr)
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        objects = self.map(rows, self.cols)
        return objects

    def update(self, which, **kwargs):
        """
        Updates one row of data from table. Row is selected using get() method.
        which - passed to get().
        kwargs - used to update row data.
        """
        to_update = self.get(which)
        keys = [key for key in kwargs.keys()]
        query = 'UPDATE {} SET {}'.format(self.table_name, '{}');
        placeholders = make_placeholders('{}', len(keys))
        query = query.format(placeholders)
        set_exprs = ['{}={!r}'.format(key, kwargs[key]) for key in keys]
        query = query.format(*set_exprs)
        query += ' WHERE {}'
        fields = get_fields(self.table_class)
        placeholders = make_placeholders('{}', len(fields), delimiter=' and ')
        placeholders = placeholders.format(
            *['{}={!r}'.format(
                field.name, getattr(to_update, field.name)) 
                    for field in fields])
        query = query.format(placeholders)
        self.cursor.execute(query)
        self.commit()

    def delete(self, which):
        """
        Deletes one row of data from table. Row is selected using get() method.
        which - passed to get()
        """
        to_delete = self.get(which)
        query = 'DELETE FROM {} WHERE {}'.format(self.table_name, '{}')
        fields = get_fields(self.table_class)
        placeholders = make_placeholders('{}', len(fields), delimiter=' and ')
        placeholders = placeholders.format(
            *['{}={!r}'.format(
                field.name, getattr(to_delete, field.name))
                    for field in fields])
        query = query.format(placeholders)
        self.cursor.execute(query)
        self.commit()


class SQLDatabase:
    """Class used to create tables"""
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

    def table(self, table_class, update_table=False):
        """
        Adds table_class to database as table. Adds objects attribute to table_class 
        that is instance of api.QuerySet. If table_class already exists as table in database, only
        adds mentioned objects attribute if table_class has not.
        If update_table is True, then that means table_class already exists as table 
        in database and you have additional columns to add to that table.
        """
        table_name = table_class.__name__

        fields = get_fields(table_class)

        if update_table:
            query = 'ALTER TABLE {} ADD COLUMN {}'.format(table_name, '{}')
            self.cursor.execute('PRAGMA table_info({})'.format(table_name))
            response = self.cursor.fetchall()
        
            old_field_names = [row[1] for row in response]
            class_field_names = [f.name for f in fields]
            new_field_names = [f for f in class_field_names if not f in old_field_names]
            new_fields = [f for f in fields if f.name in new_field_names]

            for field in new_fields:
                if field.required and not field.default and not field.is_pk:
                    message = 'Cannot add not null column without default value for column {0}'
                    message = message.format(field.name)
                    raise exceptions.NewColumnWithoutDefault(message)

            for field in new_fields:
                param = self.cook_params([field,])
                new_query = query.format(*param)
                self.cursor.execute(new_query)          

        else:       
            placeholders = make_placeholders('{}', len(fields))
            query = 'CREATE TABLE IF NOT EXISTS {} ({})'.format(
                table_name, placeholders)
            params =self.cook_params(fields)

            self.cursor.execute(query.format(*params))

        self.commit()
        self.add_query_set(table_class)

    def cook_params(self, fields):
        """Makes column definitions out of fields and returns them as list."""
        params = []
        for field in fields:
            param = '{0} {1}'.format(field.name, field.type)
            if field.required and not field.is_pk:
                param += ' NOT NULL'
            if field.default is not None:
                param += ' DEFAULT {!r}'.format(field.default)
            if field.is_pk:
                param += ' PRIMARY KEY'
            params.append(param)
        return params

    def add_query_set(self, table_class):
        """Adds instance of api.QuerySet class as attribute to table_class."""
        table_class.objects = QuerySet(table_class, self.conn, self.cursor)

    def commit(self):
        """Commits changes to database."""
        self.conn.commit()

    def close(self):
        """Closes connection to database."""
        self.conn.close()

