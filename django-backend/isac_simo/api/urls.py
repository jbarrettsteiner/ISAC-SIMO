from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('image', views.images, name="images"),
    path('image/add', views.addImage, name="images.add"),
    path('image/update/<int:id>', views.updateImage, name="images.update"),
    path('image/delete/<int:id>', views.deleteImage, name="images.delete"),
    path('image/image_file/delete/<int:id>', views.deleteImageFile, name="images.image_file.delete")
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)