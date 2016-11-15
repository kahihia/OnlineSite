# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-10 11:13
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interpay', '0006_auto_20161109_2230'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bankaccount',
            name='owner_type',
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='method',
            field=models.PositiveSmallIntegerField(choices=[(1, b'Debit'), (2, b'Credit')], default=1),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='when_opened',
            field=models.DateField(default=datetime.datetime.now, verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='date_joined',
            field=models.DateTimeField(default=datetime.datetime(2016, 11, 10, 14, 43, 13, 94288)),
        ),
    ]
