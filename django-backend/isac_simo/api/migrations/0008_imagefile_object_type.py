# Generated by Django 2.0 on 2020-03-19 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_auto_20200219_1635'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagefile',
            name='object_type',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]