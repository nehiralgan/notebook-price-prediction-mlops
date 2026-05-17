from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import sqlite3
import re
from sklearn.ensemble import RandomForestRegressor

# FastAPI uygulamasını başlatıyoruz
app = FastAPI(title="Notebook Fiyat Tahmin API Hizmeti")

# ==========================================
# 🧠 MODELİ ARKA PLANDA HAZIRLAMA
# ==========================================
print("⏳ Yapay zeka modeli veritabanından beslenerek API için hazırlanıyor...")
conn = sqlite3.connect("daily_prices.db")
df = pd.read_sql_query("SELECT * FROM fiyatlar", conn)
conn.close()

# train.py'da yaptığımız özellik mühendisliğinin aynısını burada da yapıyoruz
df['marka'] = df['urun_adi'].apply(lambda x: x.split()[0].upper())

def ram_bul(metin):
    match = re.search(r'(\d+)\s*(?:Gb|GB|gb)-(?:\d+)', metin)
    if match: return int(match.group(1))
    match_alt = re.search(r'(\d+)\s*(?:Gb|GB|gb)', metin)
    return int(match_alt.group(1)) if match_alt else 8
df['ram'] = df['urun_adi'].apply(ram_bul)

def ssd_bul(metin):
    match = re.search(r'-(\d+)\s*(?:Gb|GB|gb)\s*(?:Ssd|SSD)', metin, re.IGNORECASE)
    if match: return int(match.group(1))
    if "1Tb" in metin.upper() or "1TB" in metin.upper(): return 1024
    return 512
df['ssd'] = df['urun_adi'].apply(ssd_bul)

def islemci_bul(metin):
    metin_ust = metin.upper()
    if "CORE I5" in metin_ust: return "Intel Core i5"
    if "CORE I7" in metin_ust: return "Intel Core i7"
    if "CORE I3" in metin_ust: return "Intel Core i3"
    if "CORE I9" in metin_ust: return "Intel Core i9"
    if "RYZEN 5" in metin_ust: return "AMD Ryzen 5"
    if "RYZEN 7" in metin_ust: return "AMD Ryzen 7"
    return "Diğer"
df['islemci'] = df['urun_adi'].apply(islemci_bul)

X_raw = df[['marka', 'islemci', 'ram', 'ssd']]
X = pd.get_dummies(X_raw, columns=['marka', 'islemci'])
y = df['fiyat']

# Modelimizi API ayağa kalkarken eğitiyoruz
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)
print("✅ Yapay zeka modeli canlı istekleri almaya hazır!")

# ==========================================
# 📥 KULLANICIDAN GELECEK VERİNİN ŞABLONU
# ==========================================
class NotebookIstek(BaseModel):
    marka: str     # Örn: "LENOVO"
    islemci: str   # Örn: "Intel Core i5"
    ram: int       # Örn: 16
    ssd: int       # Örn: 512

# ==========================================
# 🚀 CANLI TAHMİN ADRESİ (Endpoint)
# ==========================================
@app.post("/tahmin-et")
def fiyat_tahmin_et(istek: NotebookIstek):
    # Gelen veriyi yapay zekanın anlayacağı formata sokuyoruz
    yeni_veri = pd.DataFrame([{
        'marka': istek.marka.upper(),
        'islemci': istek.islemci,
        'ram': istek.ram,
        'ssd': istek.ssd
    }])
    
    yeni_veri_encoded = pd.get_dummies(yeni_veri)
    yeni_veri_encoded = yeni_veri_encoded.reindex(columns=X.columns, fill_value=0)
    
    # Canlı tahmin üretiliyor
    tahmin_edilen_fiyat = model.predict(yeni_veri_encoded)[0]
    
    return {
        "durum": "Başarılı",
        "girilen_ozellikler": istek,
        "tahmin_edilen_piyasa_degeri_tl": round(tahmin_edilen_fiyat, 2)
    }