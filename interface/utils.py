# -*- coding: utf-8 -*-
'''
File Name: interface/utils.py
Author: JackeyGao
mail: junqi.gao@shuyun.com
Created Time: 2015年07月28日 星期二 14时44分25秒
'''
from rest_framework.views import exception_handler
from rest_framework import exceptions

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.

    if response is not None:
        if isinstance(response.data, dict):
            response.data['status_code'] = response.status_code
        elif isinstance(response.data, list):
            default_detail = response.data[0]
            response.data = {}
            response.data["status_code"] = 500
            response.data["default_detail"] = default_detail
    return response
