"""Web arayüzünün çağırdığı Python arka ucu. Her yöntem JSON'a çevrilebilir bir sözlük döndürür:
{"ok": True, "durum": {...}, ...} ya da {"ok": False, "hata": "..."}."""
import base64
import functools
import io
import os
import sys
import traceback
from datetime import date

from . import cekirdek, okuma, rapor
from .okuma import GUN_ADLARI, seviye_adi, tarih_yaz

EXCEL = ("Excel dosyaları (*.xls;*.xlsx)", "Tüm dosyalar (*.*)")
TAKVIM = ("Takvim (*.pdf;*.xls;*.xlsx)", "Tüm dosyalar (*.*)")
LISTE = ("Liste (*.xls;*.xlsx;*.csv;*.txt)", "Tüm dosyalar (*.*)")
RESIM = ("Resim (*.png;*.jpg;*.jpeg;*.bmp)", "Tüm dosyalar (*.*)")
YEDEK = ("Kelebek yedeği (*.kelebek)", "Tüm dosyalar (*.*)")


def veri_klasoru():
    """Otomatik kaydın tutulduğu klasör (KELEBEK_VERI ortam değişkeniyle değiştirilebilir)."""
    ozel = os.environ.get("KELEBEK_VERI")
    if ozel:
        return ozel
    if sys.platform.startswith("win"):
        taban = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        taban = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        taban = os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(taban, "Kelebek")


class Dialoglar:
    """Gerçek pencerede dosya/klasör seçme kutuları (pywebview). Testlerde yerine sahtesi konur."""

    def __init__(self):
        self.pencere = None

    def _tip(self, ad):
        import webview
        fd = getattr(webview, "FileDialog", None)
        if fd is not None:
            return {"ac": fd.OPEN, "kaydet": fd.SAVE, "klasor": fd.FOLDER}[ad]
        return {"ac": webview.OPEN_DIALOG, "kaydet": webview.SAVE_DIALOG, "klasor": webview.FOLDER_DIALOG}[ad]

    def ac(self, turler, coklu=False):
        r = self.pencere.create_file_dialog(self._tip("ac"), allow_multiple=coklu, file_types=turler)
        return [str(x) for x in r] if r else []

    def kaydet(self, ad, turler):
        r = self.pencere.create_file_dialog(self._tip("kaydet"), save_filename=ad, file_types=turler)
        if isinstance(r, (list, tuple)):
            r = r[0] if r else None
        return str(r) if r else None

    def klasor(self):
        r = self.pencere.create_file_dialog(self._tip("klasor"))
        return str(r[0]) if r else None


def guvenli(fn):
    @functools.wraps(fn)
    def sarmal(self, *a, **k):
        try:
            return fn(self, *a, **k)
        except Exception as e:  # arayüze okunaklı hata, ayrıntı konsola
            traceback.print_exc()
            return {"ok": False, "hata": str(e) or e.__class__.__name__}
    return sarmal


class Api:
    def __init__(self, klasor=None, dialog=None):
        self.klasor = klasor or veri_klasoru()
        self.dialog = dialog or Dialoglar()
        self.proje = cekirdek.Proje()
        self.geri = []
        self.pencere = None
        self._yukle()

    # ---------------------------------------------------------------- kayıt
    @property
    def _dosya(self):
        return os.path.join(self.klasor, "proje.kelebek")

    def _yukle(self):
        if not os.path.exists(self._dosya):
            return
        try:
            self.proje = cekirdek.Proje.yukle(self._dosya)
        except Exception:
            try:
                os.replace(self._dosya, self._dosya + ".bozuk")
            except OSError:
                pass
            self.proje = cekirdek.Proje()

    def _kaydet(self):
        os.makedirs(self.klasor, exist_ok=True)
        gecici = self._dosya + ".tmp"
        self.proje.kaydet(gecici)
        os.replace(gecici, self._dosya)

    def _sonuc(self, **ek):
        self._kaydet()
        return {"ok": True, "durum": self._durum(), **ek}

    # ---------------------------------------------------------------- durum
    def _durum(self):
        p = self.proje
        siniflar = []
        for s in p.sinif_sirali():
            sl = s["salon"]
            siniflar.append({"anahtar": s["anahtar"], "ad": p.sinif_adi(s["anahtar"]), "seviye": s["seviye"],
                             "sube": s["sube"], "ogrenci": len(s["ogrenciler"]), "tur": sl["tur"],
                             "komsuluk": sl["komsuluk"], "sutun": int(sl.get("sutun") or 0),
                             "kapasite": p.kapasite(s["anahtar"]), "kapasite_ozel": bool(sl.get("kapasite"))})
        sinavlar = []
        for i, s in enumerate(p.sinavlar):
            sinavlar.append({"id": i, "tarih": s["tarih"], "tarih_yazi": tarih_yaz(s["tarih"]),
                             "oturum": s["oturum"], "seviye": s["seviye"], "seviye_adi": seviye_adi(s["seviye"]),
                             "ders": s["ders"], "liste": len(s["ogrenci_nolari"]) if s.get("ogrenci_nolari") else 0})
        oturumlar = []
        for k, sn in p.oturumlar().items():
            t, saat = k.split("|")
            y, a, g = (int(x) for x in t.split("-"))
            plan = p.oturum_plani(k)
            d = p.dagitimlar.get(k)
            seviyeler = [x["seviye"] for x in sn]
            sorular = []
            for q in p.ayni_ders_sorulari([k]):
                sorular.append({"ders": q["ders"], "seviyeler": q["seviyeler"], "uygulanabilir": q["uygulanabilir"],
                                "oran": round(q["oran"], 2), "secim": p.ayni_ders.get(f"{k}|{q['ders']}")})
            oturumlar.append({
                "anahtar": k, "tarih": t, "tarih_yazi": tarih_yaz(t), "gun": GUN_ADLARI[date(y, a, g).weekday()],
                "gun_no": date(y, a, g).weekday(), "oturum": saat, "saat_no": int("".join(c for c in saat if c.isdigit())),
                "sinavlar": [{"seviye": x["seviye"], "seviye_adi": seviye_adi(x["seviye"]), "ders": x["ders"],
                              "liste": len(x["ogrenci_nolari"]) if x.get("ogrenci_nolari") else 0} for x in sn],
                "salon": len(plan["salonlar"]), "ogrenci": len(plan["ogrenciler"]), "karildi": bool(d),
                "uyari": len(p.dogrula(k)) if d else 0,
                "haric": [a_ for a_ in p.haric.get(k, []) if a_ in p.siniflar],
                "siniflar": [{"anahtar": s["anahtar"], "ad": p.sinif_adi(s["anahtar"]), "seviye": s["seviye"]}
                             for s in p.sinif_sirali() if s["seviye"] in seviyeler],
                "sorular": sorular})
        kurum = dict(p.kurum)
        kurum.update({"okul_adi": p.okul_adi, "sinav_basligi": p.takvim_basligi})
        if not kurum.get("rapor_klasoru"):
            kurum["rapor_klasoru"] = os.path.join(os.path.expanduser("~"), "Documents", "KelebekRaporlar")
        return {"kurum": kurum, "siniflar": siniflar, "sinavlar": sinavlar, "oturumlar": oturumlar,
                "seviyeler": sorted({s["seviye"] for s in p.siniflar.values()}, key=okuma.seviye_sirala_anahtari)}

    @guvenli
    def durum(self):
        return {"ok": True, "durum": self._durum()}

    # ---------------------------------------------------------------- kurum
    @guvenli
    def kurum_kaydet(self, d):
        p = self.proje
        p.okul_adi = (d.get("okul_adi") or "").strip()
        p.takvim_basligi = (d.get("sinav_basligi") or "").strip()
        for k in ("alt_baslik", "mudur", "mudur_yrd", "rapor_klasoru"):
            if k in d:
                p.kurum[k] = (d.get(k) or "").strip()
        return self._sonuc()

    def _logo_yaz(self, yol):
        from PIL import Image
        im = Image.open(yol)
        im = im.convert("RGBA")
        im.thumbnail((400, 400))
        tampon = io.BytesIO()
        im.save(tampon, "PNG")
        self.proje.kurum["logo"] = "data:image/png;base64," + base64.b64encode(tampon.getvalue()).decode()

    @guvenli
    def kurum_logo_sec(self):
        yollar = self.dialog.ac(RESIM, False)
        return self.kurum_logo_yol(yollar[0]) if yollar else {"ok": True, "iptal": True, "durum": self._durum()}

    @guvenli
    def kurum_logo_yol(self, yol):
        self._logo_yaz(yol)
        return self._sonuc()

    @guvenli
    def kurum_logo_kaldir(self):
        self.proje.kurum["logo"] = ""
        return self._sonuc()

    # ---------------------------------------------------------------- sınıflar
    @guvenli
    def sinif_yukle(self):
        yollar = self.dialog.ac(EXCEL, True)
        return self.sinif_yukle_yollar(yollar) if yollar else {"ok": True, "iptal": True, "durum": self._durum()}

    @guvenli
    def sinif_yukle_yollar(self, yollar):
        tum, uyarilar = [], []
        for y in yollar:
            s, u = okuma.sinif_listesi_oku(y)
            tum += s
            uyarilar += u
        if not tum:
            return {"ok": False, "hata": "Dosyada sınıf listesi bulunamadı."}
        self.proje.siniflari_ekle(tum)
        self.proje.dagitimlar = {}
        return self._sonuc(uyarilar=uyarilar, eklenen=len(tum))

    @guvenli
    def salon_ayarla(self, anahtarlar, tur, komsuluk, sutun, kapasite):
        for a in anahtarlar:
            sl = self.proje.siniflar[a]["salon"]
            sl.update({"tur": tur, "komsuluk": komsuluk, "sutun": int(sutun or 0)})
            if len(anahtarlar) == 1 or not kapasite:
                sl["kapasite"] = int(kapasite) if kapasite else None
        self.proje.dagitimlar = {}
        return self._sonuc()

    # ---------------------------------------------------------------- takvim
    @guvenli
    def takvim_yukle(self):
        yollar = self.dialog.ac(TAKVIM, False)
        return self.takvim_yukle_yol(yollar[0]) if yollar else {"ok": True, "iptal": True, "durum": self._durum()}

    @guvenli
    def takvim_yukle_yol(self, yol):
        baslik, sinavlar = okuma.takvim_oku(yol)
        if not sinavlar:
            return {"ok": False, "hata": "Takvimde sınav bulunamadı. Tablo biçimi farklı olabilir; "
                                         "sınavları 'Sınav ekle' ile elle girebilirsiniz."}
        p = self.proje
        okul = p.okul_adi
        p.takvimi_degistir(sinavlar, " ".join(baslik[1:]) if len(baslik) > 1 else " ".join(baslik))
        if baslik and not okul:
            p.okul_adi = baslik[0]
        self.geri = []
        return self._sonuc(eklenen=len(sinavlar))

    def _sinav_degisti(self, anahtarlar):
        for k in anahtarlar:
            self.proje.dagitimlar.pop(k, None)
            for a in [a for a in self.proje.ayni_ders if a.startswith(k + "|")]:
                del self.proje.ayni_ders[a]

    @guvenli
    def sinav_ders_degistir(self, sid, ders):
        s = self.proje.sinavlar[int(sid)]
        ders = (ders or "").strip()
        if ders:
            s["ders"] = ders
            self._sinav_degisti({cekirdek.oturum_anahtari(s["tarih"], s["oturum"])})
        return self._sonuc()

    @guvenli
    def sinav_ekle(self, tarih, saat, seviye, ders):
        import re
        m = re.fullmatch(r"\s*(\d{4})-(\d{1,2})-(\d{1,2})\s*", tarih or "")
        if not m:
            return {"ok": False, "hata": "Tarih geçersiz."}
        iso = f"{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}"
        sn = re.search(r"\d+", str(saat) or "")
        if not sn or not (ders or "").strip():
            return {"ok": False, "hata": "Saat ve ders adı gerekli."}
        oturum = f"{int(sn[0])}. Saat"
        self.proje.sinavlar.append({"tarih": iso, "oturum": oturum, "seviye": seviye, "ders": ders.strip(),
                                    "ogrenci_nolari": None})
        self._sinav_degisti({cekirdek.oturum_anahtari(iso, oturum)})
        return self._sonuc()

    @guvenli
    def sinav_sil(self, idler):
        idler = {int(i) for i in idler}
        etkilenen = {cekirdek.oturum_anahtari(s["tarih"], s["oturum"])
                     for i, s in enumerate(self.proje.sinavlar) if i in idler}
        self.proje.sinavlar = [s for i, s in enumerate(self.proje.sinavlar) if i not in idler]
        self._sinav_degisti(etkilenen)
        return self._sonuc()

    @guvenli
    def secmeli_liste_sec(self, sid):
        yollar = self.dialog.ac(LISTE, False)
        return self.secmeli_liste_yol(sid, yollar[0]) if yollar else {"ok": True, "iptal": True, "durum": self._durum()}

    @guvenli
    def secmeli_liste_yol(self, sid, yol):
        s = self.proje.sinavlar[int(sid)]
        nolar = okuma.ogrenci_no_listesi_oku(yol)
        bilinen = {no for no, (a, _) in self.proje.ogrenci_tablosu().items()
                   if self.proje.siniflar[a]["seviye"] == s["seviye"]}
        gecerli = [n for n in nolar if n in bilinen]
        s["ogrenci_nolari"] = gecerli
        self._sinav_degisti({cekirdek.oturum_anahtari(s["tarih"], s["oturum"])})
        return self._sonuc(atlanan=len(nolar) - len(gecerli), yuklenen=len(gecerli))

    @guvenli
    def secmeli_liste_kaldir(self, sid):
        s = self.proje.sinavlar[int(sid)]
        s["ogrenci_nolari"] = None
        self._sinav_degisti({cekirdek.oturum_anahtari(s["tarih"], s["oturum"])})
        return self._sonuc()

    # ---------------------------------------------------------------- karma
    @guvenli
    def haric_ayarla(self, oturumlar, sinif_anahtarlari):
        self.proje.haric_ayarla(oturumlar, sinif_anahtarlari)
        return self._sonuc()

    @guvenli
    def haric_degistir(self, oturum, sinif):
        """Tek bir sınıfı o oturumda kelebek dışı yapar / geri alır."""
        mevcut = set(self.proje.haric.get(oturum, []))
        mevcut ^= {sinif}
        self.proje.haric_ayarla([oturum], sorted(mevcut))
        return self._sonuc()

    @guvenli
    def ayni_ders_ayarla(self, oturum, ders, secim):
        self.proje.ayni_ders[f"{oturum}|{ders}"] = "ayri" if secim == "ayri" else "serbest"
        self.proje.dagitimlar.pop(oturum, None)
        return self._sonuc()

    @guvenli
    def karistir(self, oturumlar, onay=False):
        p = self.proje
        oturumlar = sorted(oturumlar, key=cekirdek.oturum_sirasi)
        sorular = p.ayni_ders_sorulari(oturumlar)
        bekleyen = [q for q in sorular if q["uygulanabilir"] and f"{q['oturum']}|{q['ders']}" not in p.ayni_ders]
        if bekleyen and not onay and len(oturumlar) > 1:
            return {"ok": True, "sorular_gerekli": [
                {"oturum": q["oturum"], "tarih_yazi": tarih_yaz(q["oturum"].split("|")[0]),
                 "saat": q["oturum"].split("|")[1], "ders": q["ders"],
                 "seviyeler": [seviye_adi(s) for s in q["seviyeler"]]} for q in bekleyen]}
        sonuclar = []
        for k in oturumlar:
            try:
                uyari = cekirdek.oturumu_karistir(p, k)
                sonuclar.append({"anahtar": k, "uyarilar": uyari})
            except ValueError as e:
                sonuclar.append({"anahtar": k, "hata": str(e), "uyarilar": []})
        self.geri = []
        notlar = [f"{tarih_yaz(q['oturum'].split('|')[0])} {q['oturum'].split('|')[1]} · {q['ders']}: "
                  f"öğrencilerin %{round(q['oran'] * 100)}'ini kapsıyor, derse göre ayırmak mümkün değil; "
                  f"yalnız aynı seviye ayrıldı." for q in sorular if not q["uygulanabilir"]]
        return self._sonuc(sonuclar=sonuclar, notlar=notlar)

    @guvenli
    def karma_sil(self, oturumlar):
        for k in oturumlar:
            self.proje.dagitimlar.pop(k, None)
        self.geri = []
        return self._sonuc()

    # ---------------------------------------------------------------- yerleşim
    def _salon_ozeti(self, k):
        d = self.proje.dagitimlar[k]
        sorun = {}
        for s in self.proje.dogrula(k):
            if s["salon"]:
                sorun[s["salon"]] = sorun.get(s["salon"], 0) + 1
        return [{"anahtar": a, "ad": self.proje.sinif_adi(a), "seviye": self.proje.siniflar[a]["seviye"],
                 "dolu": sum(1 for x in ks if x), "kapasite": len(ks), "uyari": sorun.get(a, 0)}
                for a, ks in d["yerlesim"].items()]

    @guvenli
    def yerlesim(self, oturum, salon=None):
        p = self.proje
        if oturum not in p.dagitimlar:
            return {"ok": False, "hata": "Bu oturum henüz karılmamış."}
        salonlar = self._salon_ozeti(oturum)
        if salon not in p.dagitimlar[oturum]["yerlesim"]:
            salon = salonlar[0]["anahtar"] if salonlar else None
        koltuklar = []
        if salon:
            tablo = p.ogrenci_tablosu()
            mesaj = {}
            for s in p.dogrula(oturum):
                if s["salon"] == salon:
                    mesaj.setdefault(s["koltuk"], []).append(s["mesaj"])
                    if s.get("koltuk2") is not None:
                        mesaj.setdefault(s["koltuk2"], []).append(s["mesaj"])
            for i, no in enumerate(p.dagitimlar[oturum]["yerlesim"][salon]):
                if no:
                    sa, o = tablo[no]
                    koltuklar.append({"i": i, "no": no, "ad": rapor.ad_bicimle(f"{o['ad']} {o['soyad']}"),
                                      "sinif": p.sinif_adi(sa), "seviye": p.siniflar[sa]["seviye"],
                                      "uyari": mesaj.get(i, [])})
                else:
                    koltuklar.append({"i": i, "no": "", "ad": "", "sinif": "", "seviye": "", "uyari": mesaj.get(i, [])})
        return {"ok": True, "salonlar": salonlar, "salon": salon, "koltuklar": koltuklar,
                "geri_var": bool(self.geri)}

    @guvenli
    def yer_degistir(self, oturum, s1, k1, s2, k2, onay=False):
        p = self.proje
        onceki = cekirdek.dagitim_kopyasi(p, oturum)
        once_sayi = len(p.dogrula(oturum))
        cekirdek.yer_degistir(p, oturum, s1, int(k1), s2, int(k2))
        yeni = p.dogrula(oturum)
        if len(yeni) > once_sayi and not onay:
            mesajlar = [s["mesaj"] for s in yeni][:6]
            p.dagitimlar[oturum] = onceki
            return {"ok": True, "onay_gerekli": True, "mesajlar": mesajlar}
        self.geri.append((oturum, onceki))
        return self._sonuc(uygulandi=True)

    @guvenli
    def geri_al(self):
        if not self.geri:
            return {"ok": False, "hata": "Geri alınacak değişiklik yok."}
        k, onceki = self.geri.pop()
        self.proje.dagitimlar[k] = onceki
        return self._sonuc(oturum=k)

    @guvenli
    def ogrenci_bul(self, oturum, metin):
        aranan = okuma.tr_kucuk((metin or "").strip())
        if not aranan or oturum not in self.proje.dagitimlar:
            return {"ok": True, "bulunan": None}
        tablo = self.proje.ogrenci_tablosu()
        for salon, ks in self.proje.dagitimlar[oturum]["yerlesim"].items():
            for i, no in enumerate(ks):
                if no:
                    o = tablo[no][1]
                    if aranan == no or aranan in okuma.tr_kucuk(f"{o['ad']} {o['soyad']}"):
                        return {"ok": True, "bulunan": {"salon": salon, "koltuk": i}}
        return {"ok": True, "bulunan": None}

    # ---------------------------------------------------------------- rapor
    @guvenli
    def klasor_sec(self):
        y = self.dialog.klasor()
        if y:
            self.proje.kurum["rapor_klasoru"] = y
            return self._sonuc()
        return {"ok": True, "iptal": True, "durum": self._durum()}

    @guvenli
    def rapor_olustur(self, oturumlar, liste1=True, liste2=True, ayri=True):
        p = self.proje
        oturumlar = sorted(oturumlar, key=cekirdek.oturum_sirasi)
        klasor = p.kurum.get("rapor_klasoru") or os.path.join(os.path.expanduser("~"), "Documents", "KelebekRaporlar")
        eksik = [k for k in oturumlar if any(s["tur"] in ("eksik", "cift") for s in p.dogrula(k))]
        dosyalar = rapor.raporlari_olustur(p, oturumlar, klasor, liste1, liste2, ayri)
        return self._sonuc(dosyalar=dosyalar, klasor=klasor, eksik=eksik)

    @guvenli
    def klasor_ac(self, yol):
        try:
            if sys.platform.startswith("win"):
                os.startfile(yol)  # noqa
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", yol])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", yol])
        except Exception:
            pass
        return {"ok": True}

    # ---------------------------------------------------------------- yedek / yeni
    @guvenli
    def yedek_al(self):
        yol = self.dialog.kaydet("kelebek-yedek.kelebek", YEDEK)
        if not yol:
            return {"ok": True, "iptal": True, "durum": self._durum()}
        self.proje.kaydet(yol)
        return self._sonuc(yol=yol)

    @guvenli
    def yedek_ac(self):
        yollar = self.dialog.ac(YEDEK, False)
        if not yollar:
            return {"ok": True, "iptal": True, "durum": self._durum()}
        return self.yedek_ac_yol(yollar[0])

    @guvenli
    def yedek_ac_yol(self, yol):
        self.proje = cekirdek.Proje.yukle(yol)
        self.geri = []
        return self._sonuc()

    @guvenli
    def yeni_proje(self):
        kurum = dict(self.proje.kurum)
        okul = self.proje.okul_adi
        self.proje = cekirdek.Proje()
        self.proje.kurum.update(kurum)      # kurum bilgileri korunur
        self.proje.okul_adi = okul
        self.geri = []
        return self._sonuc()

    # ---------------------------------------------------------------- kabuk
    def selftest_modu(self):
        return os.environ.get("KELEBEK_SELFTEST") == "1"

    def selftest_bitir(self, ok, mesaj=""):
        """Derlenmiş uygulamanın CI'daki öz testi için: sonucu yazıp süreci kapatır."""
        satir = f"KELEBEK-SELFTEST {'OK' if ok else 'HATA'} {mesaj}"
        print(satir, flush=True)
        yol = os.environ.get("KELEBEK_SELFTEST_DOSYA")
        if yol:
            with open(yol, "w", encoding="utf-8") as f:
                f.write(satir)
        os._exit(0 if ok else 1)
