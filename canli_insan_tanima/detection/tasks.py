# detection/tasks.py

import cv2
import base64
import time
from celery import shared_task
from celery.result import AsyncResult # GÖREV DURUMUNU SORGULAMAK İÇİN
from ultralytics import YOLO
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

try:
    model = YOLO('insan.pt')
except Exception as e:
    print(f"HATA: YOLO modeli yüklenemedi. 'insan.pt' dosyasının doğru yolda olduğundan emin olun. Hata: {e}")
    model = None

CONFIDENCE_THRESHOLD = 0.45


@shared_task(bind=True)
def process_video_feed(self, group_name):
    """
    Kamera görüntüsünü alan, YOLOv8 ile insan tespiti yapan ve işlenmiş görüntüyü
    ilgili WebSocket grubuna gönderen Celery görevi.
    """
    if not model:
        print("Model yüklenemediği için görev çalıştırılamıyor.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("HATA: Kamera açılamadı.")
        return

    channel_layer = get_channel_layer()
    print(f"[{group_name}] Görüntü işleme görevi başladı. ID: {self.request.id}")
    
    while True:
        # --- NİHAİ HATA DÜZELTMESİ ---
        # Görevin iptal edilip edilmediğini kontrol etmenin en güvenilir yolu,
        # sonucunu doğrudan backend'den (Redis) sorgulamaktır.
        task_result = AsyncResult(self.request.id)
        if task_result.state == 'REVOKED':
            print(f"[{group_name}] Görev 'REVOKED' olarak işaretlendi, döngü sonlandırılıyor.")
            break

        ret, frame = cap.read()
        if not ret:
            print(f"[{group_name}] Kamera görüntüsü alınamadı.")
            break

        human_count = 0
        
        results = model(frame, verbose=False)

        for result in results:
            boxes = result.boxes
            for box in boxes:
                conf = box.conf.item()
                if conf >= CONFIDENCE_THRESHOLD:
                    cls_id = int(box.cls)
                    label = model.names[cls_id]

                    if label == 'Human':
                        human_count += 1
                        xyxy = box.xyxy[0].cpu().numpy()
                        cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 0), 2)
                        cv2.putText(frame, f'{label} {conf:.2f}', (int(xyxy[0]), int(xyxy[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')

        payload = {
            'type': 'celery_message_handler',
            'image': jpg_as_text,
            'human_count': human_count
        }
        
        async_to_sync(channel_layer.group_send)(group_name, payload)
        
        time.sleep(0.05)

    cap.release()
    print(f"[{group_name}] Kamera serbest bırakıldı ve görev normal bir şekilde tamamlandı.")