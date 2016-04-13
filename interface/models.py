# -*- coding: utf-8 -*-
from django.db import models

class InterfaceEntry(models.Model):
    owner = models.ForeignKey("auth.User", related_name='interfaceentry')
    sql = models.TextField()
    tname = models.CharField(unique=True, max_length=255, null=False)

    def get_table_name(self):
        table_name = self.sql.split(' ')[2]
        # remote '`'
        table_name = table_name.replace('`', '')
        return table_name

    def get_absolute_url(self):
        return '/interface/%s' % self.tname


