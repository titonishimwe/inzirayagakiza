from django.urls import path
from . import views

urlpatterns = [
    path('',views.home, name='home'),
    path('sermon/',views.sermon, name='sermon'),
    path('book/',views.books, name='book'),

]