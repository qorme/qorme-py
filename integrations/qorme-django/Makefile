test:
	uv run $(if $(DJANGO_VERSION),--with "django==$(DJANGO_VERSION)") --package=qorme-django python manage.py test

coverage:
	uv run --package=qorme-django coverage run manage.py test
	uv run --package=qorme-django coverage report -m
