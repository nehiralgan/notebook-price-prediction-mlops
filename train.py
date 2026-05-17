import sqlite3
import pandas as pd
import re
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import mlflow # MLflow kütüphanesini dahil ettik

# ==========================================
# MLFLOW DENEY BAŞLATMA
# ==========================================
# Deney adını belirliyoruz
mlflow.set_experiment("Notebook_Fiyat_Tahmin_Projesi")

with mlflow.start_run(run_name="Random_Forest_Temel_Model"):
    
    print("📦 Veritabanından veriler çekiliyor...")
    conn = sqlite3.connect("daily_prices.db")
    df = pd.read_sql_query("SELECT * FROM fiyatlar", conn)
    conn.close()

    # ÖZELLİK MÜHENDİSLİĞİ
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

    # VERİ HAZIRLIK VE ENCODING
    X = df[['marka', 'islemci', 'ram', 'ssd']]
    X = pd.get_dummies(X, columns=['marka', 'islemci'])
    y = df['fiyat']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # MODEL EĞİTİMİ
    print("🤖 Model eğitiliyor...")
    n_estimators_degeri = 100
    model = RandomForestRegressor(n_estimators=n_estimators_degeri, random_state=42)
    model.fit(X_train, y_train)

    # PERFORMANS ÖLÇÜMÜ
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("\n📊 MODEL PERFORMANS RAPORU:")
    print(f"💵 Ortalama Hata Payı (MAE): {mae:.2f} TL")
    print(f"📈 Model Başarı Skoru (R2 Score): {r2:.4f}")

    # ==========================================
    # MLFLOW LOGLAMA (Mühendislik Kaydı)
    # ==========================================
    # 1. Modelin parametrelerini kaydediyoruz
    mlflow.log_param("model_tipi", "RandomForest")
    mlflow.log_param("n_estimators", n_estimators_degeri)
    mlflow.log_param("kullanilan_ozellikler", "marka, islemci, ram, ssd")
    
    # 2. Modelin başarı metriklerini kaydediyoruz
    mlflow.log_metric("MAE", mae)
    mlflow.log_metric("R2_Score", r2)
    
    # 3. Eğitilen modeli fiziksel olarak MLflow hafızasına kaydediyoruz (Versiyonlama)
    mlflow.sklearn.log_model(model, "fiyat_tahmin_modeli")
    
    print("\n🚀 Tebrikler! Model parametreleri ve metrikleri MLflow sistemine başarıyla kaydedildi.")