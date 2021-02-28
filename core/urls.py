from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('newlive/', views.new_live, name='new_live'),
    path('editlive/', views.edit_live, name='edit_live'),
    path('removelive/', views.remove_live, name='remove_live'),
    path('vtblist/', views.vtb_list, name='vtb_list'),
    path('vtbadd/', views.vtb_add, name='vtb_add'),
    path('vtbedit/', views.vtb_edit, name='vtb_edit'),
    path('vtbremove/', views.vtb_remove, name='vtb_remove'),
    path('notify/', views.notify, name='notify'),
    path('useredit/', views.user_edit, name='user_edit'),
    path('logout/', views.logout, name='logout'),
]