import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time

def veritabanini_hazirla():
    conn = sqlite3.connect("daily_prices.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fiyatlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun_adi TEXT,
            fiyat REAL,
            tarih TEXT,
            UNIQUE(urun_adi, fiyat) ON CONFLICT IGNORE
        )
    """)
    conn.commit()
    return conn

def fiyat_temizle(fiyat_metni):
    try:
        temiz_fiyat = fiyat_metni.replace(".", "").replace(",", ".").replace("TL", "").strip()
        return float(temiz_fiyat)
    except:
        return None

def vatan_akilli_kaydedici():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }
    
    conn = veritabanini_hazirla()
    cursor = conn.cursor()
    su_an = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    sayfa = 1
    toplam_eklenen = 0
    seen_products = set() # 🧠 Akıllı hafıza: Daha önce gördüğümüz ürünleri burada tutacağız
    
    while True:
        if sayfa > 15: 
            print("🛑 Güvenlik Freni: Maksimum sayfa sınırına (15) ulaşıldı. Döngü durduruluyor.")
            break
            
        url = f"https://www.vatanbilgisayar.com/notebook/?page={sayfa}"
        print(f"🔄 Sayfa {sayfa} indiriliyor: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Sayfa {sayfa} indirilemedi. Döngü sonlandırılıyor.")
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            kartlar = soup.find_all("div", class_="product-list__content")
            
            if not kartlar:
                print(f"🏁 Sayfada ürün bulunamadı. Son sayfaya ulaşıldı.")
                break
            
            sayfa_ici_yeni_kayit = 0
            for urun in kartlar:
                isim_etiketi = urun.find("div", class_="product-list__product-name")
                fiyat_etiketi = urun.find("span", class_="product-list__price")
                
                if isim_etiketi and fiyat_etiketi:
                    urun_adi = isim_etiketi.text.strip()
                    temiz_fiyat = fiyat_temizle(fiyat_etiketi.text.strip())
                    
                    if temiz_fiyat:
                        # Ürün adı ve fiyatını birleştirip eşsiz bir kimlik (ID) oluşturuyoruz
                        urun_kimligi = f"{urun_adi}_{temiz_fiyat}"
                        
                        # 🧠 Eğer bu ürünü bu çalışma esnasında DAHA ÖNCE GÖRMEDİYSEK veritabanına ekle
                        if urun_kimligi not in seen_products:
                            cursor.execute("""
                                INSERT INTO fiyatlar (urun_adi, fiyat, tarih) 
                                VALUES (?, ?, ?)
                            """, (urun_adi, temiz_fiyat, su_an))
                            
                            seen_products.add(urun_kimligi) # Hafızaya kaydet ki bir daha eklemeyelim
                            sayfa_ici_yeni_kayit += 1
            
            conn.commit()
            toplam_eklenen += sayfa_ici_yeni_kayit
            print(f"📄 Sayfa {sayfa} tamamlandı. Bu sayfadan {sayfa_ici_yeni_kayit} YENİ ürün eklendi.")
            
            # 🚨 AKILLI FREN: Eğer bu sayfada bulduğumuz tüm ürünler zaten hafızada varsa (yeni ürün sayısı 0 ise)
            # site ya tamamen başa sarmıştır ya da gerçekten yeni ürün kalmamıştır.
            if sayfa_ici_yeni_kayit == 0:
                print("🛑 Akıllı Fren: Bu sayfadaki tüm ürünler zaten daha önce çekilmiş. Yeni ürün yok, döngü bitiriliyor.")
                break
            
            time.sleep(1)
            sayfa += 1
            
        except Exception as e:
            print(f"💥 Sayfa {sayfa}'da hata: {e}")
            break
            
    conn.close()
    print(f"\n🎯 İŞLEM TAMAMLANDI! Toplam {toplam_eklenen} adet benzersiz ürün veritabanına işlendi.")

if __name__ == "__main__":
    vatan_akilli_kaydedici()