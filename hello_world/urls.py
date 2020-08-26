from django.urls import path

from hello_world import views

urlpatterns = [
    path('', views.home, name='home'),
    path('o-projektu/', views.about, name='about'),
    path('opatreni/', views.opatreni, name='opatreni'),
    path('api/search', views.najdi_mesto, name='najdi_mesto'),

]