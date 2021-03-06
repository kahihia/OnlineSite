# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-12 10:02
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('interpay', '0020_auto_20161204_1540'),
    ]

    operations = [
        migrations.CreateModel(
            name='Withdraw',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total', models.FloatField()),
                ('when', models.DateTimeField()),
                ('cur_code', models.CharField(default=b'USD', max_length=3, verbose_name='cur_code')),
            ],
        ),
        migrations.RemoveField(
            model_name='cashing',
            name='account',
        ),
        migrations.RemoveField(
            model_name='cashing',
            name='banker',
        ),
        migrations.AddField(
            model_name='deposit',
            name='status',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='deposit',
            name='tracking_code',
            field=models.IntegerField(default=b'123'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='w_accounts', to='interpay.UserProfile'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='spectators',
            field=models.ManyToManyField(related_name='r_accounts', to='interpay.UserProfile'),
        ),
        migrations.AlterField(
            model_name='deposit',
            name='banker',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='interpay.UserProfile'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='date_joined',
            field=models.DateTimeField(default=datetime.datetime(2016, 12, 12, 13, 32, 5, 142870)),
        ),
        migrations.DeleteModel(
            name='Cashing',
        ),
        migrations.AddField(
            model_name='withdraw',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='withdraw_set', to='interpay.BankAccount'),
        ),
        migrations.AddField(
            model_name='withdraw',
            name='banker',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
