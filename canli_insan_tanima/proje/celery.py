import os
from celery import Celery

# Django 'settings' modülünü Celery için varsayılan olarak ayarla.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proje.settings')

app = Celery('proje')

# String kullanarak yapılandırma nesnesini yükle.
# 'CELERY' namespace'i ile başlayan tüm ayarları bulur.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Uygulamanızdaki tüm task modüllerini otomatik olarak bul.
app.autodiscover_tasks()