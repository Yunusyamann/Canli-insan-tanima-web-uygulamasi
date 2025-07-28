# detection/consumers.py

import json
from celery.result import AsyncResult
from channels.generic.websocket import AsyncWebsocketConsumer
from .tasks import process_video_feed
from proje.celery import app as celery_app

class DetectionConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        raw_channel_name = self.channel_name
        self.group_name = raw_channel_name.replace('!', '_').replace('.', '_')
        self.task_id = None
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket bağlantısı kabul edildi. Grup Adı: '{self.group_name}'")

    async def disconnect(self, close_code):
        print(f"WebSocket bağlantısı '{self.group_name}' için kapatılıyor.")
        if self.task_id:
            celery_app.control.revoke(self.task_id, terminate=True)
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        İstemciden bir mesaj alındığında çağrılır.
        'start_detection' ve 'stop_detection' mesajlarını işler.
        """
        data = json.loads(text_data)
        message_type = data.get('type')

        # --- YENİ EKLENEN MANTIK BAŞLANGICI ---
        if message_type == 'start_detection':
            # Halihazırda çalışan bir görev varsa yenisini başlatma
            if self.task_id and AsyncResult(self.task_id).state not in ['SUCCESS', 'FAILURE', 'REVOKED']:
                print(f"Zaten çalışan bir görev var: {self.task_id}. Yeni görev başlatılmadı.")
                return

            # Yeni görevi başlat
            task = process_video_feed.delay(self.group_name)
            self.task_id = task.id
            print(f"Yeni görev başlatıldı: {self.task_id}")

        elif message_type == 'stop_detection':
            # Durdurulacak bir görev varsa işlemi yap
            if self.task_id:
                print(f"Durdurma komutu alındı. Görev sonlandırılıyor: {self.task_id}")
                # Görevi sonlandır ve iptal et
                celery_app.control.revoke(self.task_id, terminate=True)
                self.task_id = None # Görev ID'sini temizle
            else:
                print("Durdurma komutu alındı ancak aktif bir görev bulunmuyor.")
        # --- YENİ EKLENEN MANTIK SONU ---

    async def celery_message_handler(self, event):
        await self.send(text_data=json.dumps({
            'image': event['image'],
            'human_count': event['human_count']
        }))