"""Kelebek Sınav Dağıtım Programı - başlatıcı (web arayüzü + yerel pencere).
Çalıştırmak için: python kelebek_baslat.py   |   CI öz testi: Kelebek.exe --selftest"""
import os
import sys
import tempfile
import threading


def kaynak(*parca):
    taban = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(taban, *parca)


def hata_goster(metin):
    try:
        if sys.platform.startswith("win"):
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, metin, "Kelebek", 0x10)
            return
    except Exception:
        pass
    print(metin)


def main():
    selftest = "--selftest" in sys.argv
    if selftest:
        os.environ["KELEBEK_SELFTEST"] = "1"
        os.environ.setdefault("KELEBEK_VERI", tempfile.mkdtemp(prefix="kelebek_test_"))
        sonuc_dosyasi = os.environ.setdefault("KELEBEK_SELFTEST_DOSYA", os.path.join(tempfile.gettempdir(), "kelebek_selftest.txt"))
        try:
            os.remove(sonuc_dosyasi)
        except OSError:
            pass
    try:
        import webview
        from kelebek.web_api import Api, veri_klasoru
    except ImportError as e:
        hata_goster(f"Eksik paket: {e}\nKurmak için: pip install -r requirements.txt")
        return 1

    api = Api()

    class Kopru:  # pywebview yalnız bu nesnenin yöntemlerini sayfaya açar (iç veriler görünmez)
        pass
    kopru = Kopru()
    for ad in dir(api):
        oge = getattr(api, ad)
        if not ad.startswith("_") and callable(oge):
            setattr(kopru, ad, oge)

    pencere = webview.create_window("Kelebek", url=kaynak("web", "index.html"), js_api=kopru,
                                    width=1360, height=860, min_size=(1100, 680), background_color="#161f2e")
    api.dialog.pencere = pencere

    if selftest:
        def bekci():
            with open(os.environ["KELEBEK_SELFTEST_DOSYA"], "w", encoding="utf-8") as f:
                f.write("KELEBEK-SELFTEST HATA zaman asimi: sayfa 90 sn icinde sonuc vermedi")
            os._exit(2)
        t = threading.Timer(90, bekci)
        t.daemon = True
        t.start()

    kwargs = {"storage_path": os.path.join(veri_klasoru(), "webview")}
    try:
        webview.start(gui="edgechromium" if sys.platform.startswith("win") else None, **kwargs)
    except Exception as e:
        hata_goster(f"Uygulama penceresi açılamadı.\nMicrosoft Edge WebView2 gerekli olabilir.\n\n{e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
