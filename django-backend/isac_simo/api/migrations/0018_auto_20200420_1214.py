# Generated by Django 2.0 on 2020-04-20 06:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_projects_detect_model'),
        ('api', '0017_image_project'),
    ]

    operations = [
        migrations.AddField(
            model_name='classifier',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='classifiers', to='projects.Projects'),
        ),
        migrations.AddField(
            model_name='objecttype',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='object_types', to='projects.Projects'),
        ),
    ]
