from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.fileUp,name='fileUp'),
    path('upload',views.upload,name="upload"),
    path('local_html',views.local_html,name='local_html'),
    path('local_html2',views.local_html2,name='local_html2'),
    path('predict',views.predict,name='predict')
]