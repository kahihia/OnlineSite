# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-14 15:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interpay', '0018_bankaccount_cur_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rule',
            name='deposit_charge_percent',
            field=models.FloatField(default=2),
        ),
    ]
