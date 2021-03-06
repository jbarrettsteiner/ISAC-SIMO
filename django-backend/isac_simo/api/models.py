import os
import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.deconstruct import deconstructible

from main.models import User
from projects.models import Projects


@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        return os.path.join(self.path, filename)

path_and_rename = PathAndRename("image")
path_and_rename_offline_models = PathAndRename("offline_models")

class Image(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=500,blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='user')
    lat = models.FloatField(validators=[MinValueValidator(-90), MaxValueValidator(90)],max_length=100,null=True,blank=True)
    lng = models.FloatField(validators=[MinValueValidator(-180), MaxValueValidator(180)],max_length=100,null=True,blank=True)
    project = models.ForeignKey(Projects, on_delete=models.SET_NULL, blank=True, null=True, related_name='project')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ImageFile(models.Model):
    image = models.ForeignKey(Image, related_name='image_files', on_delete=models.CASCADE)
    file = models.ImageField(upload_to=path_and_rename)
    tested = models.BooleanField(default=False)
    result = models.CharField(blank=True, null=True, max_length=500)
    score = models.FloatField(validators=[MinValueValidator(-1), MaxValueValidator(1)],max_length=10,null=True,blank=True)
    object_type = models.CharField(blank=True, null=True, max_length=500)
    retrained = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    pipeline_status = models.TextField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file.url

class ObjectType(models.Model):
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, related_name='object_types', on_delete=models.SET_NULL, blank=True, null=True)
    project = models.ForeignKey(Projects, related_name='object_types', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Classifier(models.Model):
    name = models.CharField(max_length=200)
    given_name = models.CharField(max_length=200, blank=True, null=True)
    classes = models.CharField(max_length=200, blank=True, null=True)
    project = models.ForeignKey(Projects, related_name='classifiers', on_delete=models.CASCADE, blank=True, null=True)
    object_type = models.ForeignKey(ObjectType, related_name='classifiers', on_delete=models.SET_NULL, blank=True, null=True)
    order = models.IntegerField("Order", default=0, blank=False, null=False)
    offline_model = models.ForeignKey('OfflineModel', on_delete=models.SET_NULL, related_name='classifiers', blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='classifiers', on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']  # order is the field holding the order

class OfflineModel(models.Model):
    name = models.CharField(max_length=200)
    model_type = models.CharField(max_length=200)
    model_format = models.CharField(max_length=50)
    file = models.FileField(upload_to=path_and_rename_offline_models)
    offline_model_labels = models.CharField(max_length=200, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='offline_models', on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.name and self.model_format:
            return self.name + ' - ' + self.model_format
        else:
            return ''

    def isObjectDetect(self):
        return True if self.model_type == 'OBJECT_DETECT' else False

    def isClassifier(self):
        return True if self.model_type == 'CLASSIFIER' else False

    def filename(self):
        try:
            return self.file.url.replace('/media/offline_models/','')
        except Exception as e:
            return ''