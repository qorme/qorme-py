from django.http import JsonResponse
from django.shortcuts import render
from django.template.response import TemplateResponse

from tests.test_app.models import Film, Store


def films(request):
    return render(request, "test_app/films.html", {"films": Film.objects.all()})


def films_json(request):
    return JsonResponse({"films": list(Film.objects.values())})


def stores(request):
    return TemplateResponse(request, "test_app/stores.html", {"stores": Store.objects.all()})


def error(request):
    # Perform some queries before raising an exception
    num_films = Film.objects.count()
    raise ValueError(f"Test error: {num_films} films")
