# -*- coding: utf-8 -*-
'''
File Name: interface/serializers.py
Author: JackeyGao
mail: junqi.gao@shuyun.com
Created Time: 2015年07月28日 星期二 11时20分11秒
'''


from django.contrib.auth.models import User, Group
from models import InterfaceEntry
from rest_framework import serializers
from rest_framework import fields


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class InterfaceEntrySerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    #url = serializers.URLField(source='get_absolute_url', read_only=True)
    tname = serializers.CharField(required=False)

    class Meta:
        model = InterfaceEntry
        fields = ('owner', 'owner_name', 'sql', 'tname')


def convert_to_serializer(serializer_name, model_object):
    class Meta:
        model = model_object

    attrs = { 'Meta': Meta }
    serializer = type(serializer_name, (serializers.ModelSerializer,), attrs)

    return serializer
