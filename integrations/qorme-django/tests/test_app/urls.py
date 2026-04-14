from django.urls import path

from tests.test_app import views

urlpatterns = [
    path("films/", views.films, name="films"),
    path("films_json/", views.films_json, name="films_json"),
    path("stores/", views.stores, name="stores"),
    path("error/", views.error, name="error"),
]
