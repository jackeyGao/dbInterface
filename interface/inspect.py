# -*- coding: utf-8 -*-
'''
File Name: interface/test.py
Author: JackeyGao
mail: junqi.gao@shuyun.com
Created Time: 2015年07月27日 星期一 15时05分32秒
'''
from django.db import models
from django.db import connections


def convert_to_model(table_name):

    connection = connections["default"]
    cursor = connection.cursor()
    # Get the table relations, indexes, constraints
    try:
        relations = connection.introspection.get_relations(cursor, table_name)
    except NotImplementedError:
        relations = {}
    try:
        indexes = connection.introspection.get_indexes(cursor, table_name)
    except NotImplementedError:
        indexes = {}
    try:
        constraints = connection.introspection.get_constraints(cursor, table_name)
    except NotImplementedError:
        constraints = {}

    unique_together = []
    for index, params in constraints.items():
        if params['unique']:
            columns = params['columns']
            if len(columns) > 1:
                tup = tuple([ c for c in columns ])
                unique_together.append(tup)

    unique_together = tuple(unique_together)

    # Meta class 
    class Meta:
        db_table = table_name 

    if unique_together:
        setattr(Meta, 'unique_together', unique_together)

    setattr(Meta, 'app_label', 'interface')

    # fields > attrs 
    attrs = { '__module__': 'dbInterface.interface', 'Meta': Meta }
    fields = {}
    for row in connection.introspection.get_table_description(cursor, table_name):
        args = {}
        field_type = connection.introspection.get_field_type(row[1], row)

        # Add max_length to CharField
        if field_type == "CharField":
            args["max_length"] = getattr(row, 'internal_size', None)

        # Add null 
        if getattr(row, 'null_ok', None) == 1:
            args["null"] = True

        # Add primary_key if table name in indexes 
        if row.name in indexes:
            if indexes[row.name]['primary_key']:
                args["primary_key"] = True
            elif indexes[row.name]['unique']:
                args["unique"] = True
        
        # Will continue if field name is id and primary key in args
        if row.name == 'id' and args.has_key("primary_key"):
            if field_type == 'AutoField' and args.get("primary_key", None):
                continue
        
        field_cls = getattr(models, field_type)
        field = field_cls(**args)

        fields[row.name] = field

    if fields:
        attrs.update(fields)

    model = type(table_name, (models.Model,), attrs)

    return model




#for table in connection.introspection.get_table_list(cursor):
#
#    for row in connection.introspection.get_table_description(cursor, table.name):
#        try:
#            field_type = connection.introspection.get_field_type(row[1], row)
#        except KeyError as e:
#            field_type = 'TextField'
#    
#        print field_type


if __name__ == '__main__':
    auth_user = convert_to_model("auth_user")
    admin_log = convert_to_model("django_admin_log")
    content_type = convert_to_model("django_content_type")
    test = convert_to_model("interface_testmodel")

    print auth_user.objects.all()
    print admin_log.objects.all()
    for ob in content_type.objects.all():
        print ob.__dict__

    print dir(test)

    test(name="junqi.gao", description="a nice man.").save()
    test(name="junqi.gao", description="a nice man.").save()
    test(name="junqi.gao", description="a nice man.").save()
    test(name="junqi.gao", description="a nice man.").save()
    test(name="junqi.gao", description="a nice man.").save()
    test(name="junqi.gao", description="a nice man.").save()

    for ob in test.objects.all():
        print ob.__dict__
