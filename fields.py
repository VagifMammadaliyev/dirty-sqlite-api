import sqlite3

class Field:
    def __init__(self, name, is_pk=False, required=True, default=None):
        self.name = name.lower()
        self.is_pk = is_pk
        self.required = required
        self.type = self.__class__.__name__
        self.type = self.type[:self.type.index('F')].upper()
        self.default = default

class TextField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class IntegerField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class RealField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BlobField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

