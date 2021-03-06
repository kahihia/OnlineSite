# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-10 12:26
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import interpay.models


class Migration(migrations.Migration):

    dependencies = [
        ('interpay', '0009_auto_20161110_1528'),
    ]

    operations = [
        migrations.AddField(
            model_name='deposit',
            name='cur_code',
            field=models.CharField(default=b'USD', max_length=3, unique=True, verbose_name='cur_code'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='account_id',
            field=models.BigIntegerField(default=interpay.models.make_id),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='when',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='date_joined',
            field=models.DateTimeField(default=datetime.datetime(2016, 11, 10, 15, 56, 27, 949792)),
        ),
    ]
