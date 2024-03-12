from django.urls import path
from django.contrib.auth import views as auth_views
from .views import GymListView, GymDetailView, GymCreateView, GymUpdateView, GymDeleteView, MyGymsView, GymSearchView

app_name = 'gymFindr'

urlpatterns = [
    path('', GymListView.as_view(), name='gym_list'),
    path('gym/<int:pk>/', GymDetailView.as_view(), name='gym_detail'),
    path('gym/new/', GymCreateView.as_view(), name='gym_create'),
    path('gym/<int:pk>/edit/', GymUpdateView.as_view(), name='gym_edit'),
    path('gym/<int:pk>/delete/', GymDeleteView.as_view(), name='gym_delete'),
    path('my-gyms/', MyGymsView.as_view(), name='my_gyms'),
    path('search/', GymSearchView.as_view(), name='gym_search'),
]
