# Bu, Django başladığında app'in yüklenmesini sağlar,
# böylece @shared_task dekoratörü bu app'i kullanır.
from .celery import app as celery_app

__all__ = ('celery_app',)