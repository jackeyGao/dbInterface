# -*- coding: utf-8 -*-
import traceback, sys, functools
from django.db import connection
from django.contrib.auth.models import User, Group
from django.forms.models import model_to_dict
from django.core.exceptions import *
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ParseError
from rest_framework.exceptions import APIException
from rest_framework.exceptions import PermissionDenied
from rest_framework import status

from models import InterfaceEntry
from serializers import UserSerializer, GroupSerializer
from serializers import InterfaceEntrySerializer
from serializers import convert_to_serializer
from inspect import convert_to_model

reload(sys)
sys.setdefaultencoding('utf-8')


def request_content_error_handler(func):
    @functools.wraps(func)
    def deco(*args, **kwargs):
        try:
            request = args[1]
            if not request.data:
                assert False, 'No json be encoded'

            assert isinstance(request.data, dict), 'expected string or buffer'
            return func(*args, **kwargs)
        except AssertionError as e:
            raise ParseError(e.args[0])
    return deco


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class InterfaceListCreateViewSet(viewsets.ModelViewSet):
    """
    数据表创建以及查看数据表数据，和推送数据表数据.
    """
    permission_classes = (IsAuthenticated,)
    queryset = InterfaceEntry.objects.all()
    serializer_class = InterfaceEntrySerializer

    def sql_validate(self, sql):
        """SQL校验， 对不是create table 开头的sql直接拒绝"""
        action, object = sql.split(' ')[0:2]
        if 'CREATE' == action.upper() and 'TABLE' == object.upper():
            return True
        return False
    
    def create_table(self, sql):
        """执行创建语句方法"""
        try:
            cursor = connection.cursor()
            result = cursor.execute(sql)
            if 'primary key' not in sql.lower():
                table_name = self.parse_sql_table_name(sql)
                sql = "ALTER TABLE %s ADD id int(11) AUTO_INCREMENT PRIMARY KEY;"\
                        % table_name
                result = cursor.execute(sql)
        except Exception as e:
            raise APIException("Create table error. E:%s" % str(e))
        return True

    def parse_sql_table_name(self, sql):
        """解析SQL中table_name"""
        # Get table name in sql and remote '`'
        table_name = sql.split(' ')[2]
        table_name = table_name.replace('`', '')
        return table_name

    @request_content_error_handler
    def create(self, request):
        """可以通过此接口创建一张数据表, 只需要在POST需要时定义`sql`键值."""
        user = User.objects.filter(username=request.user)[0]

        # Request validate
        try:
            sql = request.data.get('sql', None)
            if sql is None:
                raise ParseError("Sql not privote")
        except:
            raise ParseError("Sql 获取失败")

        # table name
        table_name = self.parse_sql_table_name(sql)
        if not self.sql_validate(sql):
            raise ParseError("Sql not a create table sql")
        
        # Save the object
        data = { "owner": user.id, "sql": sql, "tname": table_name }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Create table using request sql
        self.create_table(sql) 

        headers = self.get_success_headers(serializer.data)
        return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED, 
                headers=headers)

    def validate_model(self, request, table_name):
        """获取model"""
        table_entrys = InterfaceEntry.objects.filter(tname=table_name)
        user = User.objects.filter(username=request.user)[0]

        # 如果没有
        if not table_entrys:
            raise APIException(
                    u"%s 没找到, 或者不是动态表" % table_name
                    )

        if len(table_entrys) == 1:
            table_entry = table_entrys[0]
        else:
            raise APIException(u"关系表异常, 存在多个%s" % table_name)

        # Permission validate
        if table_entry.owner_id <> int(user.id):
            raise PermissionDenied

        try:
            model = convert_to_model(table_name)
            return model
        except Exception as e:
            raise APIException("Convert to model error. E:%s" % str(e))

    @request_content_error_handler
    def push(self, request, pk, format=None):
        """可以通过此接口推送数据到一张表, 需要定义数据字段和对应值."""
        try:
            model = self.validate_model(request, str(pk))
            serializer_class = convert_to_serializer(str(pk + 'serializer'), model)
            setattr(self, 'serializer_class', serializer_class)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            raise APIException("ValidationError E:%s" % str(e))
        except TypeError as e:
            raise APIException("TypeError E:%s" % str(e))

    def pull(self, request, pk):
        """可以通过此接口查看一张表数据, 注意由于数据不固定，目前仅提供100条."""
        model = self.validate_model(request, str(pk))
        serializer_class = convert_to_serializer(str(pk + 'serializer'), model)

        setattr(self, 'serializer_class', serializer_class)
        setattr(self, 'queryset', model.objects.all())

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route()
    def attribute(self, request, pk):
        try:
            model = self.validate_model(request, str(pk))
            ret = {}
            for i in model._meta.get_fields():
                ret[i.get_attname_column()[1]] = i.get_internal_type()
            return Response({"attributes": ret})
        except Exception as e:
            raise APIException(u"Convert to model error. E:%s" % str(e))


