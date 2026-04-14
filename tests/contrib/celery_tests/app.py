from celery import Celery

# Create a minimal Celery app for testing
app = Celery("test_celery")
app.conf.update(
    broker_url="memory://",
    result_backend="cache+memory://",
    task_always_eager=True,
    task_store_eager_result=True,
)


@app.task
def add(x, y):
    return x + y


@app.task
def multiply(x, y):
    return x * y


@app.task(name="tests.contrib.celery.test_celery.ignored_task")
def ignored_task():
    return "ignored"
