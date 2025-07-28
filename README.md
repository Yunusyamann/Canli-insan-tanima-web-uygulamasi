# Canlı İnsan Tanıma Web Uygulaması

Bu proje, Django, Celery ve WebSockets kullanarak web arayüzü üzerinden gerçek zamanlı insan tespiti yapan bir uygulamadır. Kullanıcı, web arayüzündeki butona tıkladığında sunucu tarafında kamera aktif hale gelir, OpenCV ve YOLOv8 modeli ile tespit edilen insanlar canlı olarak video akışında bir kutu (bounding box) içine alınır ve algılanan insan sayısı anlık olarak güncellenir.

Proje, yoğun işlem gücü gerektiren görüntü işleme görevlerini web sunucusundan ayırarak ölçeklenebilir ve performanslı bir mimari sunar.

![Proje Ekran Görüntüsü](https://i.hizliresim.com/p14w2k9.png)
*(Projenin çalışan bir halinin ekran görüntüsünü veya GIF'ini buraya ekleyebilirsiniz.)*

## Kullanılan Teknolojiler

Bu projenin geliştirilmesinde aşağıdaki teknolojiler ve kütüphaneler kullanılmıştır:

* **Backend:**
    * [**Django**](https://www.djangoproject.com/): Ana web framework'ü.
    * [**Django Channels**](https://channels.readthedocs.io/en/latest/): WebSocket bağlantıları ve asenkron işlemler için.
* **Asenkron Görevler:**
    * [**Celery**](https://docs.celeryq.dev/en/stable/): Görüntü işleme gibi uzun süren görevleri arka planda çalıştırmak için.
    * [**RabbitMQ**](https://www.rabbitmq.com/): Celery için mesaj aracısı (message broker).
* **Veri Katmanı & Cache:**
    * [**Redis**](https://redis.io/): Django Channels için kanal katmanı (channel layer) arka planı.
* **Görüntü İşleme:**
    * [**OpenCV**](https://opencv.org/): Kameradan görüntü yakalama ve işleme için.
    * [**Ultralytics YOLOv8**](https://ultralytics.com/): Gerçek zamanlı nesne tespiti için.
* **ASGI Sunucusu:**
    * [**Daphne**](https://github.com/django/daphne): Django Channels için resmi ASGI sunucusu.
* **Frontend:**
    * HTML, CSS, Vanilla JavaScript

## Proje Mimarisi

Uygulama, görevleri birbirinden ayıran modern bir mimari üzerine kurulmuştur:

1.  **Kullanıcı Arayüzü (Browser):** Kullanıcı web sayfasını açar ve `ws://` üzerinden sunucuya bir WebSocket bağlantısı kurar.
2.  **Daphne (ASGI Sunucusu):** Gelen WebSocket bağlantısını kabul eder ve ilgili Django Channels Consumer'ına yönlendirir.
3.  **Django Channels Consumer (`consumers.py`):** Kullanıcı "Başlat" butonuna bastığında gelen mesajı alır ve `process_video_feed` görevini `.delay()` ile tetikler. Bu görev talebi RabbitMQ'ya bir mesaj olarak gönderilir.
4.  **RabbitMQ (Message Broker):** Görev mesajını alır ve uygun bir Celery worker'ına iletmek üzere kuyruğa ekler.
5.  **Celery Worker (`tasks.py`):** RabbitMQ'dan görevi alır. Kamerayı (`OpenCV`) başlatır ve `while` döngüsü içinde sürekli olarak kareleri okur. Her kareyi `YOLOv8` modeline göndererek insan tespiti yapar.
6.  **Geri Bildirim Döngüsü:**
    * Celery worker, işlediği (üzerine kutu çizilmiş) her kareyi ve insan sayısını **Redis** üzerinden kanal katmanına (channel layer) gönderir.
    * Channels Consumer, Redis'i dinler ve Celery'den gelen bu mesajı alır.
    * Consumer, mesajı WebSocket bağlantısı üzerinden anlık olarak kullanıcının tarayıcısına geri yollar.
7.  **Sonuç:** Tarayıcıdaki JavaScript, gelen veriyi alarak `<img>` etiketini ve insan sayısı metnini günceller, böylece canlı bir video akışı ve sayaç oluşturulur.

