# Generated by Django 2.0 on 2020-04-03 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_auto_20200403_1038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='objecttype',
            name='name',
            field=models.CharField(max_length=500, unique=True),
        ),
    ]
