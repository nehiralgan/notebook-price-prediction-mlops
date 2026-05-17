# 1. Resmi hafif bir Python imajı kullanarak başlıyoruz
FROM python:3.10-slim

# 2. Konteyner içinde 'app' adında bir çalışma klasörü açıyoruz
WORKDIR /app

# 3. Bilgisayarımızdaki gerekli dosyaları konteynerin içine kopyalıyoruz
COPY requirements.txt .
COPY daily_prices.db .
COPY api.py .

# 4. Kütüphaneleri konteyner içinde yüklüyoruz
RUN pip install --no-cache-dir -r requirements.txt

# 5. FastAPI'nin dışarıya açılacağı 8000 portunu serbest bırakıyoruz
EXPOSE 8000

# 6. Konteyner ayağa kalktığında otomatik çalışacak komut
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]