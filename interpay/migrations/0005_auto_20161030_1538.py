# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-30 12:08
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interpay', '0004_auto_20161019_1857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='date_joined',
            field=models.DateTimeField(default=datetime.datetime(2016, 10, 30, 15, 38, 51, 156782)),
        ),
    ]
