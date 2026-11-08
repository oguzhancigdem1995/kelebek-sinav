"""Gerçek veriyle uçtan uca test: python test_cekirdek.py <sinif_listesi.xls> <takvim.pdf>"""
import sys, time
from collections import Counter
from kelebek import okuma, cekirdek

def main(xls, pdf, ayni="serbest"):
    p = cekirdek.Proje()
    s, u = okuma.sinif_listesi_oku(xls); assert not u, u
    p.siniflari_ekle(s)
    b, e = okuma.takvim_oku(pdf)
    p.takvimi_degistir(e, " ".join(b))
    oturumlar = list(p.oturumlar())
    sorular = p.ayni_ders_sorulari(oturumlar)
    if ayni == "ayri":
        for q in sorular:
            if q["uygulanabilir"]:
                p.ayni_ders[f"{q['oturum']}|{q['ders']}"] = "ayri"
    t0 = time.time(); toplam_uyari = 0
    for k in oturumlar:
        uy = cekirdek.oturumu_karistir(p, k)
        sorun = p.dogrula(k)
        toplam_uyari += len(sorun)
        n = sum(1 for sl in p.dagitimlar[k]["yerlesim"].values() for x in sl if x)
        print(k, f"salon={len(p.dagitimlar[k]['yerlesim'])} ogr={n} ihlal={len(sorun)}", [x for x in uy if 'seçmeli' not in x][:2])
    print("süre", round(time.time() - t0, 1), "sn  toplam ihlal", toplam_uyari)
    # tekrar kontrolü
    ayni_yer = ayni_salon_ust_uste = 0; ust_uste = 0
    gecmis = {}
    for k in oturumlar:
        for sl, koltuklar in p.dagitimlar[k]["yerlesim"].items():
            for i, no in enumerate(koltuklar):
                if no:
                    if (sl, i) in gecmis.get(no, {}).values(): ayni_yer += 1
        # ardışık salon
    onceki = None
    for k in oturumlar:
        simdi = {no: sl for sl, ks in p.dagitimlar[k]["yerlesim"].items() for no in ks if no}
        if onceki:
            ortak = [no for no in simdi if no in onceki]
            ust_uste += sum(simdi[no] == onceki[no] for no in ortak)
        onceki = simdi
    tum = defaultdict = None
    yer = Counter()
    for k in oturumlar:
        for sl, ks in p.dagitimlar[k]["yerlesim"].items():
            for i, no in enumerate(ks):
                if no: yer[(no, sl, i)] += 1
    print("aynı öğrenci-salon-sıra tekrarı:", sum(1 for v in yer.values() if v > 1),
          "| üst üste aynı salon (öğrenci-sayısı):", ust_uste)
    return p

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "serbest")
