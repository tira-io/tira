from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('task', views.index, name='tasks'),
    path('tasks', views.index, name='tasks'),
    path('task/<str:task_id>', views.task_detail, name='task-detail'),
    path('task/<str:task_id>/dataset/<str:dataset_id>', views.dataset_detail, name='dataset-detail'),
    path('task/<str:task_id>/user/<str:vm_id>', views.software_detail, name='software-detail'),
    path('task/<str:task_id>/user/<str:vm_id>/dataset/<str:dataset_id>/run/<str:run_id>', views.review, name='review'),
    path('dataset', views.dataset_list, name='dataset'),
    # path('software/<str:user_id>', views.software_detail, name='software-detail'),  # show all vms on tasks of a user
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('tira/admin', views.admin, name='tira-admin'),
    path('tira/admin/reload-data', views.admin_reload_data, name='tira-admin-reload-data'),
    path('tira/admin/create-vm', views.admin_create_vm, name='tira-admin-create-vm'),
]
app_name = 'tira'
