import pytest

from core.celery import app


@pytest.fixture(autouse=True)
def celery_eager():
    """Run Celery tasks inline during tests, without a broker."""
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True
    yield
    app.conf.task_always_eager = False
