"""Web arayüzünü gerçek Api ile Playwright üzerinde uçtan uca dener.
pywebview yerine küçük bir HTTP köprüsü: window.pywebview.api.<yontem>(...) -> POST /api/<yontem>"""
import glob, json, os, sys, tempfile, threading, http.server, functools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kelebek.web_api import Api

KOK = os.path.dirname(os.path.abspath(__file__))
CIKTI = os.environ.get("KELEBEK_SS", tempfile.mkdtemp())


class SahteDialog:
    def __init__(self):
        self.sonraki = []
    def ac(self, turler, coklu=False):
        return self.sonraki.pop(0)
    def kaydet(self, ad, turler):
        return self.sonraki.pop(0)
    def klasor(self):
        return self.sonraki.pop(0)


def sunucu(api):
    kilit = threading.Lock()

    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(s, *a, **k):
            super().__init__(*a, directory=os.path.join(KOK, "web"), **k)
        def log_message(s, *a): pass
        def do_POST(s):
            ad = s.path.split("/api/")[1]
            n = int(s.headers.get("Content-Length", 0))
            args = json.loads(s.rfile.read(n) or b"[]")
            with kilit:
                r = getattr(api, ad)(*args)
            b = json.dumps(r).encode()
            s.send_response(200); s.send_header("Content-Type", "application/json"); s.send_header("Content-Length", str(len(b))); s.end_headers(); s.wfile.write(b)
    sv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=sv.serve_forever, daemon=True).start()
    return sv

INIT = """
window.pywebview = {api: new Proxy({}, {get: (t, ad) => (...a) => fetch('/api/' + ad, {method:'POST', body: JSON.stringify(a)}).then(r => r.json())})};
window.dispatchEvent(new Event('pywebviewready'));
"""


def main():
    from playwright.sync_api import sync_playwright
    veri = tempfile.mkdtemp()
    os.environ["KELEBEK_VERI"] = veri
    dlg = SahteDialog()
    api = Api(klasor=veri, dialog=dlg)
    sv = sunucu(api)
    url = f"http://127.0.0.1:{sv.server_address[1]}/index.html"
    xls = glob.glob("/mnt/user-data/attachments/*/*.xls")
    pdf = glob.glob("/mnt/user-data/attachments/*/*.pdf")[0]
    logo = glob.glob(os.path.join(KOK, "assets", "kelebek.png"))[0]
    rap = tempfile.mkdtemp()
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
        hatalar = []
        pg.on("pageerror", lambda e: hatalar.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and hatalar.append(m.text))
        pg.add_init_script(INIT)
        pg.goto(url)
        pg.wait_for_selector("#icerik .t")
        def ss(ad): pg.screenshot(path=os.path.join(CIKTI, ad + ".png"))
        assert "Kurum" in pg.inner_text("#icerik .t")
        # kurum
        pg.fill("#k-okul", "Deneme Anadolu Lisesi"); pg.fill("#k-alt", "Ankara · 2026-2027"); pg.fill("#k-yrd", "Ali Veli"); pg.fill("#k-mudur", "Ayşe Yılmaz")
        pg.click("#k-kaydet")
        dlg.sonraki.append([logo]); pg.click("#k-logo"); pg.wait_for_selector(".logo-kutu img"); ss("1_kurum")
        # sınıflar
        pg.click("[data-sayfa=siniflar]"); dlg.sonraki.append(xls); pg.click("#s-yukle"); pg.wait_for_selector("tbody tr"); ss("2_siniflar")
        assert len(pg.query_selector_all("tbody tr")) == 15
        pg.click("tbody tr:nth-child(1)"); pg.click("#s-duzen"); pg.select_option("#m-tur", "ikili"); pg.click(".modal .btn:not(.g)")
        pg.wait_for_selector(".modal-kap", state="hidden")
        pg.wait_for_function("document.querySelector('tbody tr').innerText.includes('İkili')")
        # takvim
        pg.click("[data-sayfa=takvim]"); dlg.sonraki.append([pdf]); pg.click("#t-yukle"); pg.wait_for_selector("tbody tr"); ss("3_takvim")
        assert len(pg.query_selector_all("tbody tr")) == 66
        # karma
        pg.click("[data-sayfa=karma]"); pg.wait_for_selector(".hucre[data-k]"); ss("4_karma")
        pg.click(".hucre[data-k] >> nth=0"); pg.wait_for_selector("#d-karistir"); ss("5_cekmece")
        pg.click("#d-karistir"); pg.wait_for_selector(".pill.ok, .pill.uyari >> nth=0"); ss("6_karildi")
        pg.click("#h-karistir")
        pg.wait_for_selector(".modal")  # aynı ders sorusu
        ss("7_soru"); pg.click(".modal .seg button[data-v=ayri] >> nth=0"); pg.click(".modal .btn:not(.g)")
        pg.wait_for_timeout(1500)
        if pg.is_visible(".modal"):
            ss("7b_bilgi"); pg.click(".modal .btn")
        pg.wait_for_selector(".modal-kap", state="hidden"); pg.wait_for_timeout(300)
        # kelebek dışı
        pg.click(".hucre[data-k] >> nth=0"); pg.click("#d-haric .chip >> nth=0"); pg.wait_for_selector("#d-haric .chip.x"); ss("8_haric")
        pg.click("#d-karistir")
        for _ in range(3):
            pg.click("#h-ileri") if pg.is_enabled("#h-ileri") else None
            pg.wait_for_timeout(150)
        # yerleşim
        pg.click("[data-sayfa=yerlesim]"); pg.wait_for_selector(".koltuk"); ss("9_yerlesim")
        pg.click(".koltuk >> nth=0"); pg.click(".koltuk >> nth=3"); pg.wait_for_timeout(500)
        if pg.query_selector(".modal"):
            pg.click(".modal .btn:not(.g)")
        pg.wait_for_timeout(300); ss("10_degisti")
        pg.fill("#y-ara", "a"); pg.press("#y-ara", "Enter")
        # raporlar
        pg.click("[data-sayfa=raporlar]"); pg.wait_for_selector("#r-hepsi"); pg.click("#r-hepsi")
        api.proje.kurum["rapor_klasoru"] = rap
        pg.click("[data-sayfa=kurum]"); pg.click("[data-sayfa=raporlar]")
        pg.click("#r-olustur"); pg.wait_for_selector("#r-sonuc .s", timeout=120000); ss("11_raporlar")
        assert glob.glob(os.path.join(rap, "*.pdf")), "PDF yok"
        pg.click("[data-sayfa=kurum]"); pg.wait_for_selector("#k-okul")
        assert pg.input_value("#k-okul") == "Deneme Anadolu Lisesi"
        b.close()
    # kalıcılık
    a2 = Api(klasor=veri)
    assert a2.proje.kurum["alt_baslik"] == "Ankara · 2026-2027" and a2.proje.dagitimlar
    ihlal = [s for k in a2.proje.dagitimlar for s in a2.proje.dogrula(k) if s["tur"] in ("yanyana", "eksik", "cift")]
    print("sayfa hataları:", hatalar)
    print("kalan ihlal:", len(ihlal), "PDF:", len(glob.glob(os.path.join(rap, '*.pdf'))), "ekran görüntüleri:", CIKTI)
    assert not hatalar


if __name__ == "__main__":
    main()
