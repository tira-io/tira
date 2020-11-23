from django.urls import path

from . import views

app_name = 'tira'
urlpatterns = [
    path('', views.index, name='index'),
    path('task', views.task_list, name='task'),
    path('dataset', views.dataset_list, name='dataset'),
    path('dataset/<str:dataset_name>', views.dataset_detail, name='dataset-detail'),
    path('software', views.software_detail, name='software-detail'),
]