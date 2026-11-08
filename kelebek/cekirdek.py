"""Proje verisi, komşuluk kuralları, kelebek (karma) algoritması ve doğrulama."""
import copy
import json
import random
import re
from collections import Counter, defaultdict

from .okuma import seviye_adi, seviye_sirala_anahtari

VARSAYILAN_SALON = {"tur": "tekli", "komsuluk": "ardarda", "sutun": 0, "kapasite": None}


def oturum_anahtari(tarih, oturum):
    return f"{tarih}|{oturum}"


def oturum_sirasi(anahtar):
    tarih, oturum = anahtar.split("|")
    return (tarih, int(re.search(r"\d+", oturum)[0]))


def sinif_anahtari(seviye, sube):
    return f"{seviye}-{sube}"


def komsuluklar(n, salon):
    """Bir salondaki (0'dan başlayan) koltuk indeksleri arasındaki 'yan yana' çiftleri."""
    tur = salon.get("tur", "tekli")
    kural = salon.get("komsuluk", "ardarda")
    sutun = int(salon.get("sutun") or 0)
    kenar = set()
    for i in range(n - 1):
        if tur == "ikili" and kural == "masa":
            if i % 2 == 0:
                kenar.add((i, i + 1))
        else:
            if sutun > 0 and (i + 1) % sutun == 0:
                continue  # satır sonu: bir sonraki satırın başıyla yan yana değil
            kenar.add((i, i + 1))
    if sutun > 0:
        for i in range(n - sutun):
            kenar.add((i, i + sutun))
    return kenar


class Proje:
    def __init__(self):
        self.okul_adi = ""
        self.takvim_basligi = ""
        self.siniflar = {}      # anahtar -> sınıf sözlüğü
        self.sinavlar = []      # takvim satırları
        self.ayni_ders = {}     # "oturum|ders" -> "serbest" | "ayri"
        self.dagitimlar = {}    # oturum anahtarı -> {"tohum", "yerlesim", "salonlar"}
        self.haric = {}         # oturum anahtarı -> kelebek dışı bırakılan sınıf anahtarları
        self.kurum = {"alt_baslik": "", "mudur": "", "mudur_yrd": "", "logo": "", "rapor_klasoru": ""}

    # ------------------------------------------------------------ sınıflar
    def siniflari_ekle(self, okunan):
        """okuma.sinif_listesi_oku çıktısını ekler/değiştirir."""
        for s in okunan:
            anahtar = sinif_anahtari(s["seviye"], s["sube"])
            eski = self.siniflar.get(anahtar)
            salon = dict(VARSAYILAN_SALON)
            if eski:
                salon = eski["salon"]
            yeni = {"anahtar": anahtar, "seviye": s["seviye"], "sube": s["sube"],
                    "ogrenciler": s["ogrenciler"], "salon": salon}
            if not self.okul_adi and s.get("okul"):
                self.okul_adi = s["okul"]
            self.siniflar[anahtar] = yeni

    def sinif_sirali(self):
        return sorted(self.siniflar.values(),
                      key=lambda s: (seviye_sirala_anahtari(s["seviye"]), s["sube"]))

    def sinif_adi(self, anahtar):
        s = self.siniflar[anahtar]
        return f"{seviye_adi(s['seviye'])} {s['sube']}"

    def kapasite(self, anahtar):
        s = self.siniflar[anahtar]
        k = s["salon"].get("kapasite")
        return int(k) if k else len(s["ogrenciler"])

    def ogrenci_tablosu(self):
        """ogr_no -> (sınıf anahtarı, öğrenci sözlüğü)"""
        t = {}
        for s in self.siniflar.values():
            for o in s["ogrenciler"]:
                t[o["no"]] = (s["anahtar"], o)
        return t

    # ------------------------------------------------------------ oturumlar
    def oturumlar(self):
        """Takvimdeki oturumlar: {anahtar: [sınav, ...]} tarih/saat sırasıyla."""
        g = defaultdict(list)
        for s in self.sinavlar:
            g[oturum_anahtari(s["tarih"], s["oturum"])].append(s)
        return {k: sorted(g[k], key=lambda x: seviye_sirala_anahtari(x["seviye"]))
                for k in sorted(g, key=oturum_sirasi)}

    def oturum_plani(self, anahtar):
        """Oturumun katılımcı sınıflarını, öğrencilerini ve etiketlerini hesaplar."""
        sinavlar = self.oturumlar()[anahtar]
        seviye_ders = {s["seviye"]: s for s in sinavlar}
        dis = set(self.haric.get(anahtar, []))
        siniflar = [s for s in self.sinif_sirali()
                    if s["seviye"] in seviye_ders and s["anahtar"] not in dis]
        ogrenciler = []   # (ogr_no, sınıf anahtarı, seviye)
        filtre_var = False
        for s in siniflar:
            sinav = seviye_ders[s["seviye"]]
            izinli = set(sinav["ogrenci_nolari"]) if sinav.get("ogrenci_nolari") else None
            if izinli is not None:
                filtre_var = True
            for o in s["ogrenciler"]:
                if izinli is None or o["no"] in izinli:
                    ogrenciler.append((o["no"], s["anahtar"], s["seviye"]))
        salonlar = [s["anahtar"] for s in siniflar]
        if filtre_var:  # seçmeli alt grup: yalnız gereken salonları kullan
            gerekli = len(ogrenciler)
            salonlar = sorted(salonlar, key=lambda a: -self.kapasite(a))
            secili, toplam = [], 0
            for a in salonlar:
                if toplam >= gerekli:
                    break
                secili.append(a)
                toplam += self.kapasite(a)
            salonlar = [s["anahtar"] for s in self.sinif_sirali() if s["anahtar"] in secili]
        return {"sinavlar": seviye_ders, "salonlar": salonlar, "ogrenciler": ogrenciler,
                "filtre_var": filtre_var}

    def haric_ayarla(self, oturumlar, sinif_anahtarlari):
        """Verilen oturumlarda bu sınıfları kelebek dışı bırakır; değişen oturumların karması silinir."""
        yeni = sorted(set(sinif_anahtarlari))
        for k in oturumlar:
            if sorted(self.haric.get(k, [])) != yeni:
                self.dagitimlar.pop(k, None)
            if yeni:
                self.haric[k] = list(yeni)
            else:
                self.haric.pop(k, None)

    def etiketler(self, anahtar, plan=None):
        """Öğrenci no -> 'yan yana olmamalı' grubu (seviye; ya da seçilmişse ders adı)."""
        plan = plan or self.oturum_plani(anahtar)
        eslesme = {}
        for sev, sinav in plan["sinavlar"].items():
            ayar = self.ayni_ders.get(f"{anahtar}|{sinav['ders']}", "serbest")
            eslesme[sev] = f"ders:{sinav['ders']}" if ayar == "ayri" else f"seviye:{sev}"
        return {no: eslesme[sev] for no, _, sev in plan["ogrenciler"]}

    def ayni_ders_sorulari(self, anahtarlar):
        """Aynı dersin birden fazla seviyede yapıldığı oturumlar ve kuralın uygulanabilirliği."""
        sorular = []
        for anahtar in anahtarlar:
            plan = self.oturum_plani(anahtar)
            ders_seviye = defaultdict(list)
            for sev, sinav in plan["sinavlar"].items():
                if any(o[2] == sev for o in plan["ogrenciler"]):
                    ders_seviye[sinav["ders"]].append(sev)
            toplam = len(plan["ogrenciler"])
            for ders, sev_listesi in ders_seviye.items():
                if len(sev_listesi) < 2:
                    continue
                say = sum(1 for o in plan["ogrenciler"] if o[2] in sev_listesi)
                oran = say / toplam if toplam else 1
                sorular.append({"oturum": anahtar, "ders": ders, "seviyeler": sev_listesi,
                                "uygulanabilir": oran <= 0.5, "oran": oran, "sayi": say})
        return sorular

    # ------------------------------------------------------------ doğrulama
    def baska_oturum_koltuklari(self, anahtar):
        """ogr_no -> [(oturum, salon, koltuk)] diğer oturumlardaki yerleri."""
        gecmis = defaultdict(list)
        for k, d in self.dagitimlar.items():
            if k == anahtar:
                continue
            for salon, koltuklar in d["yerlesim"].items():
                for i, no in enumerate(koltuklar):
                    if no:
                        gecmis[no].append((k, salon, i))
        return gecmis

    def dogrula(self, anahtar):
        """Bir oturumdaki ihlalleri döndürür: yan yana, tekrar eden yer, eksik/fazla öğrenci."""
        d = self.dagitimlar.get(anahtar)
        if not d:
            return []
        plan = self.oturum_plani(anahtar)
        etiket = self.etiketler(anahtar, plan)
        tablo = self.ogrenci_tablosu()
        gecmis = self.baska_oturum_koltuklari(anahtar)
        sorunlar = []
        gorulen = Counter()
        for salon, koltuklar in d["yerlesim"].items():
            for i, j in komsuluklar(len(koltuklar), self.siniflar[salon]["salon"]):
                a, b = koltuklar[i], koltuklar[j]
                if a and b and etiket.get(a) is not None and etiket.get(a) == etiket.get(b):
                    sorunlar.append({"tur": "yanyana", "salon": salon, "koltuk": i, "koltuk2": j,
                                     "mesaj": f"{self.sinif_adi(salon)} salonunda {i+1}. ve {j+1}. "
                                              f"sıradaki öğrenciler aynı grupta "
                                              f"({self._etiket_yaz(etiket[a])})."})
            for i, no in enumerate(koltuklar):
                if not no:
                    continue
                gorulen[no] += 1
                if any(s == salon and k == i for _, s, k in gecmis.get(no, [])):
                    ad = tablo[no][1]
                    sorunlar.append({"tur": "tekrar", "salon": salon, "koltuk": i,
                                     "mesaj": f"{ad['ad']} {ad['soyad']} ({no}) başka bir sınavda "
                                              f"da {self.sinif_adi(salon)} salonunda {i+1}. sırada."})
        beklenen = {no for no, _, _ in plan["ogrenciler"]}
        for no in beklenen - set(gorulen):
            ad = tablo[no][1]
            sorunlar.append({"tur": "eksik", "salon": None, "koltuk": None,
                             "mesaj": f"{ad['ad']} {ad['soyad']} ({no}) yerleştirilmemiş."})
        for no, c in gorulen.items():
            if c > 1:
                sorunlar.append({"tur": "cift", "salon": None, "koltuk": None,
                                 "mesaj": f"{no} numaralı öğrenci {c} kez yerleştirilmiş."})
        return sorunlar

    @staticmethod
    def _etiket_yaz(e):
        t, deger = e.split(":", 1)
        return seviye_adi(deger) if t == "seviye" else deger

    # ------------------------------------------------------------ kayıt
    def kaydet(self, yol):
        veri = {"okul_adi": self.okul_adi, "takvim_basligi": self.takvim_basligi,
                "siniflar": list(self.siniflar.values()), "sinavlar": self.sinavlar,
                "ayni_ders": self.ayni_ders, "dagitimlar": self.dagitimlar,
                "haric": self.haric, "kurum": self.kurum}
        with open(yol, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=1)

    @classmethod
    def yukle(cls, yol):
        with open(yol, encoding="utf-8") as f:
            v = json.load(f)
        p = cls()
        p.okul_adi = v.get("okul_adi", "")
        p.takvim_basligi = v.get("takvim_basligi", "")
        p.siniflar = {s["anahtar"]: s for s in v.get("siniflar", [])}
        p.sinavlar = v.get("sinavlar", [])
        p.ayni_ders = v.get("ayni_ders", {})
        p.dagitimlar = v.get("dagitimlar", {})
        p.haric = v.get("haric", {})
        p.kurum.update(v.get("kurum", {}))
        eski = [a for a, s in p.siniflar.items() if s.pop("haric", False)]  # eski sürüm: genel hariç listesi
        if eski:
            for k in p.oturumlar():
                p.haric[k] = sorted(set(p.haric.get(k, [])) | set(eski))
        return p

    def takvimi_degistir(self, sinavlar, baslik=""):
        """Yeni sınav programı yüklenir: eski dağıtımlar ve ders seçimleri sıfırlanır."""
        self.sinavlar = sinavlar
        self.takvim_basligi = baslik
        self.ayni_ders = {}
        self.dagitimlar = {}
        self.haric = {}


# ====================================================================== algoritma
def _kotalar(etiket_sayilari, kapasiteler, rng):
    """Her etiket (ve boş koltuk) için salonlara orantılı pay: {(etiket, salon): adet}.

    En büyük kalan yöntemi; salon toplamları kapasiteye, etiket toplamları sayıya eşittir."""
    salonlar = list(kapasiteler)
    toplam_kap = sum(kapasiteler.values())
    kalan = dict(kapasiteler)
    kota = {}
    etiketler = sorted(etiket_sayilari, key=lambda e: (-etiket_sayilari[e], str(e)))
    for idx, e in enumerate(etiketler):
        n = etiket_sayilari[e]
        if idx == len(etiketler) - 1:
            for s in salonlar:
                kota[(e, s)] = kalan[s]
            break
        ham = {s: n * kapasiteler[s] / toplam_kap for s in salonlar}
        taban = {s: min(int(ham[s]), kalan[s]) for s in salonlar}
        eksik = n - sum(taban.values())
        sira = sorted(salonlar, key=lambda s: -(ham[s] - int(ham[s]) + rng.random() * 1e-6))
        k = 0
        guvenlik = 0
        while eksik > 0 and guvenlik < 10000:
            s = sira[k % len(sira)]
            k += 1
            guvenlik += 1
            if taban[s] < kalan[s]:
                taban[s] += 1
                eksik -= 1
        for s in salonlar:
            kota[(e, s)] = taban[s]
            kalan[s] -= taban[s]
    return kota


def _salon_dizilimi(ogrenciler, kapasite, kenar, etiket, yasak_koltuk, rng, deneme=25, adim=6000):
    """Bir salonda öğrencileri koltuklara dizer (min-çakışma). ogrenciler: ogr_no listesi.

    yasak_koltuk: ogr_no -> bu salonda daha önce oturduğu koltuk indeksleri kümesi.
    Döner: (koltuk listesi [no|None]*kapasite, kalan_ihlal_sayisi)"""
    dolgu = list(ogrenciler) + [None] * (kapasite - len(ogrenciler))
    komsu = defaultdict(list)
    for i, j in kenar:
        komsu[i].append(j)
        komsu[j].append(i)

    def ihlal(a, i):
        s = a[i]
        if s is None:
            return 0
        c = 0
        for j in komsu[i]:
            if a[j] is not None and etiket[a[j]] == etiket[s]:
                c += 3
        if i in yasak_koltuk.get(s, ()):
            c += 1
        return c

    en_iyi, en_iyi_puan = None, None
    for _ in range(deneme):
        a = dolgu[:]
        rng.shuffle(a)
        for _ in range(adim):
            kotu = [i for i in range(kapasite) if ihlal(a, i)]
            if not kotu:
                break
            i = rng.choice(kotu)
            j = rng.randrange(kapasite)
            if i == j:
                continue
            once = ihlal(a, i) + ihlal(a, j)
            a[i], a[j] = a[j], a[i]
            if ihlal(a, i) + ihlal(a, j) > once:
                a[i], a[j] = a[j], a[i]
        puan = sum(ihlal(a, i) for i in range(kapasite))
        if en_iyi_puan is None or puan < en_iyi_puan:
            en_iyi, en_iyi_puan = a[:], puan
        if puan == 0:
            break
    return en_iyi, en_iyi_puan


def oturumu_karistir(proje, anahtar, tohum=None):
    """Bir oturumu karar ve proje.dagitimlar[anahtar] içine yazar. Uyarı listesi döndürür."""
    tohum = tohum if tohum is not None else random.randrange(1, 2**31)
    rng = random.Random(tohum)
    plan = proje.oturum_plani(anahtar)
    salonlar = plan["salonlar"]
    if not plan["ogrenciler"] or not salonlar:
        proje.dagitimlar.pop(anahtar, None)
        return ["Bu oturumda kelebek sistemine dahil öğrenci yok."]
    kap = {s: proje.kapasite(s) for s in salonlar}
    n = len(plan["ogrenciler"])
    if n > sum(kap.values()):
        raise ValueError(f"{anahtar}: {n} öğrenci var ama toplam {sum(kap.values())} sıra var.")
    etiket = proje.etiketler(anahtar, plan)
    gecmis = proje.baska_oturum_koltuklari(anahtar)

    # Komşu oturumlardaki (zamansal önceki/sonraki) salonlar: üst üste aynı salonu azalt
    sirali = sorted(set(proje.dagitimlar) | {anahtar}, key=oturum_sirasi)
    i = sirali.index(anahtar)
    komsu_oturumlar = [sirali[k] for k in (i - 1, i + 1) if 0 <= k < len(sirali) and sirali[k] != anahtar
                       and sirali[k] in proje.dagitimlar]
    yakin_salon = defaultdict(set)
    for k in komsu_oturumlar:
        for salon, koltuklar in proje.dagitimlar[k]["yerlesim"].items():
            for no in koltuklar:
                if no:
                    yakin_salon[no].add(salon)
    salon_sayac = defaultdict(Counter)
    for no, liste in gecmis.items():
        for _, salon, _ in liste:
            salon_sayac[no][salon] += 1

    # 1) Etiket başına salon payları
    sayilar = Counter(etiket[no] for no, _, _ in plan["ogrenciler"])
    bos = sum(kap.values()) - n
    if bos:
        sayilar["__bos__"] = bos
    kota = _kotalar(sayilar, kap, rng)

    # 2) Öğrencileri salonlara dağıt (yakın oturumdaki salondan kaçınarak)
    def maliyet(no, salon):
        return 10 * (salon in yakin_salon.get(no, ())) + salon_sayac[no][salon]

    kalan_kota = dict(kota)
    atama = {}
    grup = defaultdict(list)
    for no, _, _ in plan["ogrenciler"]:
        grup[etiket[no]].append(no)
    for e, uyeler in grup.items():
        rng.shuffle(uyeler)
        # önce en çok kısıtlı (yakın salonu olan) öğrenciler
        uyeler.sort(key=lambda no: -len(yakin_salon.get(no, ())))
        for no in uyeler:
            adaylar = [s for s in salonlar if kalan_kota[(e, s)] > 0]
            rng.shuffle(adaylar)
            s = min(adaylar, key=lambda s: maliyet(no, s))
            atama[no] = s
            kalan_kota[(e, s)] -= 1
        # takas ile iyileştir
        for _ in range(len(uyeler) * 8):
            a, b = rng.sample(uyeler, 2) if len(uyeler) > 1 else (uyeler[0], uyeler[0])
            sa, sb = atama[a], atama[b]
            if sa == sb:
                continue
            if maliyet(a, sb) + maliyet(b, sa) < maliyet(a, sa) + maliyet(b, sb):
                atama[a], atama[b] = sb, sa

    # 3) Her salonda koltuk dizilimi
    yerlesim, uyarilar = {}, []
    for s in salonlar:
        uyeler = [no for no, sl in atama.items() if sl == s]
        kenar = komsuluklar(kap[s], proje.siniflar[s]["salon"])
        yasak = {no: {k for _, sl, k in gecmis.get(no, []) if sl == s} for no in uyeler}
        koltuklar, puan = _salon_dizilimi(uyeler, kap[s], kenar, etiket, yasak, rng)
        yerlesim[s] = koltuklar
    proje.dagitimlar[anahtar] = {"tohum": tohum, "yerlesim": yerlesim, "salonlar": salonlar}
    sorunlar = [s["mesaj"] for s in proje.dogrula(anahtar)]
    uyarilar.extend(sorunlar[:8])
    if len(sorunlar) > 8:
        uyarilar.append(f"... ve {len(sorunlar) - 8} uyarı daha (kural bu oturumda tam sağlanamadı).")
    if plan["filtre_var"]:
        uyarilar.append("Seçmeli ders öğrenci listesi kullanıldı; yalnız gereken salonlar açıldı.")
    for sev, sinav in plan["sinavlar"].items():
        if "SEÇMELİ" in sinav["ders"].upper() and not sinav.get("ogrenci_nolari"):
            uyarilar.append(f"{seviye_adi(sev)} '{sinav['ders']}' seçmeli ders ama öğrenci listesi "
                            f"yüklenmedi; seviyenin tüm öğrencileri sınava giriyor sayıldı.")
    return uyarilar


def yer_degistir(proje, anahtar, salon1, koltuk1, salon2, koltuk2):
    """İki koltuğun içeriğini (öğrenci ya da boş) değiştirir."""
    y = proje.dagitimlar[anahtar]["yerlesim"]
    y[salon1][koltuk1], y[salon2][koltuk2] = y[salon2][koltuk2], y[salon1][koltuk1]


def dagitim_kopyasi(proje, anahtar):
    return copy.deepcopy(proje.dagitimlar[anahtar])
