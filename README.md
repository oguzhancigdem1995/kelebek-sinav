# Kelebek

Sınıf listelerini (e-Okul Excel) ve sınav takvimini (PDF/Excel) okuyup her sınav oturumu için öğrencileri
salonlara karıştırır; aynı sınıf seviyesindeki öğrenciler yan yana oturmaz. Çıktı iki PDF listesidir.

## Kurulum
Elinizde `Kelebek_Kurulum.exe` varsa çift tıklayıp sihirbazı izlemeniz yeterlidir; başka hiçbir şey kurmanız gerekmez.

Kurulum dosyasını üretmek için (bir kez):
- **GitHub ile (bilgisayara bir şey kurmadan):** bu klasörü bir GitHub deposuna yükleyin, Actions sekmesinden
  "Setup.exe olustur" akışını çalıştırın, bitince `Kelebek_Kurulum` dosyasını indirin.
- **Kendi bilgisayarınızda:** Python 3.9+ ve Inno Setup 6 kurun, `setup_olustur.bat` dosyasını çalıştırın.
  Sonuç `cikti\Kelebek_Kurulum.exe` olur.

Geliştirme amaçlı çalıştırma: `pip install -r requirements.txt` ardından `python kelebek_baslat.py`.

## Kullanım
0. **Kurum:** okul adı, alt başlık, müdür/müdür yardımcısı, logo ve rapor klasörünü girin; raporlarda kullanılır (farklı okullarda kullanmak için burası değiştirilir).
1. **Sınıflar:** e-Okul listesini yükleyin. Her sınıf bir salondur. "Salon düzeni" ile tekli/ikili sıra,
   yan yana kuralı ve ön/arka komşuluk ayarlanır.
2. **Takvim:** PDF/Excel takvimi yükleyin; ders adına çift tıklayıp düzeltin. Seçmeli sınavlara öğrenci listesi eklenebilir.
3. **Karma:** haftalık takvim panosunda bir oturuma tıklayın; sağdaki panelden aynı ders kuralını ve kelebek dışı sınıfları
   ayarlayıp karıştırın, ya da "Haftayı karıştır".
4. **Yerleşim:** iki sırayı seçip yer değiştirin; kural bozulursa uyarır.
5. **Raporlar:** Liste 1 (öğrenci bazlı) ve Liste 2 (salon bazlı + seviye özeti) PDF.

## Kurallar
- Aynı seviyeden iki öğrenci yan yana oturmaz ("oturmasın" seçilen derslerde aynı dersi alan tüm öğrenciler).
- Bir öğrenci hiçbir sınavda aynı salonda aynı sırada oturmaz; üst üste iki sınavda mümkünse farklı salona düşer.
- Sınavı olmayan seviyenin salonları o oturumda kullanılmaz.
- Kural matematiksel olarak sağlanamıyorsa (bir grup öğrencilerin yarısından fazlası) program uyarır.

Arayüz web teknolojisiyle (HTML/CSS/JS) yazılmıştır ve Windows'ta WebView2 penceresinde açılır (kurulum sihirbazı gerekirse otomatik kurar).
Testler: `test_cekirdek.py <sinif.xls...>`, `test_web.py` (Playwright ile uçtan uca).
