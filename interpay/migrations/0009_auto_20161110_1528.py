# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-10 11:58
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import interpay.models


class Migration(migrations.Migration):

    dependencies = [
        ('interpay', '0008_auto_20161110_1502'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='account_id',
            field=models.IntegerField(default=interpay.models.make_id),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='date_joined',
            field=models.DateTimeField(default=datetime.datetime(2016, 11, 10, 15, 28, 18, 897323)),
        ),
    ]
