# Generated by Django 2.0 on 2020-04-07 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_auto_20200403_1632'),
    ]

    operations = [
        migrations.AlterField(
            model_name='objecttype',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]
