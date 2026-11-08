"""Sınıf listesi (e-Okul .xls/.xlsx) ve sınav takvimi (PDF/Excel) okuyucuları."""
import re
from datetime import date

SEVIYE_SIRASI = ["Hazırlık", "9", "10", "11", "12"]
AYLAR = {"ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "haziran": 6,
         "temmuz": 7, "ağustos": 8, "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12}
AY_ADLARI = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
             "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUN_ADLARI = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def tr_kucuk(s):
    """Türkçe'ye duyarlı küçük harfe çevirme (I->ı, İ->i)."""
    return str(s).replace("İ", "i").replace("I", "ı").lower()


def seviye_bul(metin):
    """'9. SINIF', '10. Sınıf', 'HAZIRLIK SINIFI' gibi metinden seviyeyi bulur."""
    t = tr_kucuk(metin)
    if "hazırlık" in t or "hazirlik" in t:
        return "Hazırlık"
    m = re.search(r"(\d{1,2})\s*\.?\s*s[ıi]n[ıi]f", t)
    return m.group(1) if m else None


def seviye_sirala_anahtari(s):
    if s in SEVIYE_SIRASI:
        return (SEVIYE_SIRASI.index(s), s)
    return (len(SEVIYE_SIRASI), s)


def seviye_adi(s):
    return "Hazırlık" if s == "Hazırlık" else f"{s}. Sınıf"


def tarih_yaz(iso):
    """'2026-11-02' -> '2 Kasım 2026 Pazartesi'"""
    y, a, g = (int(x) for x in iso.split("-"))
    d = date(y, a, g)
    return f"{g} {AY_ADLARI[a]} {y} {GUN_ADLARI[d.weekday()]}"


def _hucre(c):
    return "" if c is None else str(c).strip()


# ---------------------------------------------------------------- sınıf listeleri
def sinif_listesi_oku(yol):
    """e-Okul sınıf listesi dosyasını okur. (siniflar, uyarilar) döndürür.

    Her sınıf: {seviye, sube, ogrenciler:[{no, ad, soyad, cinsiyet}], okul}
    """
    from python_calamine import CalamineWorkbook
    wb = CalamineWorkbook.from_path(str(yol))
    siniflar, uyarilar = [], []
    for sayfa in wb.sheet_names:
        satirlar = wb.get_sheet_by_name(sayfa).to_python()
        cur = None
        for r in satirlar:
            hucreler = [c for c in r if _hucre(c) != ""]
            if not hucreler:
                continue
            ilk = _hucre(hucreler[0])
            if "Şubesi" in ilk and "Liste" in ilk:
                baslik = ilk.split("\n")[-1].strip()
                satir_okul = [p.strip() for p in ilk.split("\n") if p.strip()]
                seviye = seviye_bul(baslik)
                m = re.search(r"/\s*([^\s/]+)\s*Şubesi", baslik)
                sube = m.group(1).upper() if m else None
                if seviye is None or sube is None:
                    uyarilar.append(f"Başlık çözülemedi: {baslik!r}")
                    cur = None
                    continue
                okul = satir_okul[-2] if len(satir_okul) >= 2 else ""
                okul = re.sub(r"^.*?/\s*", "", okul) if "/" in okul else okul
                cur = {"seviye": seviye, "sube": sube, "ogrenciler": [], "okul": okul,
                       "bildirilen": None}
                siniflar.append(cur)
                continue
            if cur is None:
                continue
            if ilk.startswith("Kız Öğrenci"):
                sayilar = [c for c in hucreler if isinstance(c, (int, float))]
                if sayilar:
                    cur["bildirilen"] = int(sayilar[-1])
                continue
            if isinstance(hucreler[0], (int, float)) and len(hucreler) >= 4:
                try:
                    no = str(int(hucreler[1])) if isinstance(hucreler[1], (int, float)) else _hucre(hucreler[1])
                except (ValueError, TypeError):
                    continue
                cur["ogrenciler"].append({
                    "no": no, "ad": _hucre(hucreler[2]), "soyad": _hucre(hucreler[3]),
                    "cinsiyet": _hucre(hucreler[4]) if len(hucreler) > 4 else ""})
    for s in siniflar:
        b = s.pop("bildirilen")
        if b is not None and b != len(s["ogrenciler"]):
            uyarilar.append(f"{seviye_adi(s['seviye'])} {s['sube']}: listede {b} öğrenci yazıyor, "
                            f"{len(s['ogrenciler'])} öğrenci okundu.")
        if not s["ogrenciler"]:
            uyarilar.append(f"{seviye_adi(s['seviye'])} {s['sube']}: öğrenci bulunamadı.")
    return siniflar, uyarilar


def ogrenci_no_listesi_oku(yol):
    """Seçmeli ders için: ilk sütunda (veya 'Öğrenci No' sütununda) okul numaraları olan dosya."""
    yol = str(yol)
    if yol.lower().endswith((".txt", ".csv")):
        with open(yol, encoding="utf-8-sig") as f:
            ham = [re.split(r"[;,\t]", s.strip()) for s in f if s.strip()]
        satirlar = ham
    else:
        from python_calamine import CalamineWorkbook
        wb = CalamineWorkbook.from_path(yol)
        satirlar = wb.get_sheet_by_name(wb.sheet_names[0]).to_python()
    no_sutunu = 0
    for r in satirlar[:10]:
        for i, c in enumerate(r):
            if "öğrenci no" in tr_kucuk(_hucre(c)) or tr_kucuk(_hucre(c)) in ("okul no", "no"):
                no_sutunu = i
    sonuc = []
    for r in satirlar:
        if len(r) <= no_sutunu:
            continue
        c = r[no_sutunu]
        if isinstance(c, float) and c == int(c):
            sonuc.append(str(int(c)))
        elif isinstance(c, int):
            sonuc.append(str(c))
        elif re.fullmatch(r"\d+", _hucre(c)):
            sonuc.append(_hucre(c))
    return sonuc


# ---------------------------------------------------------------- sınav takvimi
_TARIH_RE = re.compile(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})")
_SAAT_RE = re.compile(r"(\d+)\s*\.?\s*saat", re.I)


def _tarih_coz(metin):
    m = _TARIH_RE.search(metin or "")
    if not m:
        return None
    ay = AYLAR.get(tr_kucuk(m.group(2)))
    if not ay:
        return None
    return f"{int(m.group(3)):04d}-{ay:02d}-{int(m.group(1)):02d}"


def _tablolari_coz(tablolar):
    """Satır/sütun tablolarından sınav listesi çıkarır."""
    sinavlar = []
    for t in tablolar:
        t = [[_hucre(c) for c in satir] for satir in t]
        baslik_i = None
        for i, r in enumerate(t):
            if sum(1 for c in r if _tarih_coz(c)) >= 2:
                baslik_i = i
                break
        if baslik_i is None:
            continue
        tarihler = {j: _tarih_coz(c) for j, c in enumerate(t[baslik_i]) if _tarih_coz(c)}
        govde = [r for r in t[baslik_i + 1:] if any(r)]
        saat_sutunu = 1
        for r in govde:
            for j, c in enumerate(r[:3]):
                if _SAAT_RE.search(c):
                    saat_sutunu = j
                    break
            break
        # Seviye etiketi çiftin ilk veya ikinci satırında olabilir: ilk satıra bakarak kipi bul.
        etiket_ilk = bool(govde) and seviye_bul(govde[0][0]) is not None
        seviyeler = [None] * len(govde)
        if etiket_ilk:
            cur = None
            for i, r in enumerate(govde):
                if seviye_bul(r[0]):
                    cur = seviye_bul(r[0])
                seviyeler[i] = cur
        else:
            bekleyen, cur = [], None
            for i, r in enumerate(govde):
                bekleyen.append(i)
                if seviye_bul(r[0]):
                    for k in bekleyen:
                        seviyeler[k] = seviye_bul(r[0])
                    bekleyen = []
        for r, sev in zip(govde, seviyeler):
            m = _SAAT_RE.search(r[saat_sutunu] if saat_sutunu < len(r) else "")
            if not m or sev is None:
                continue
            oturum = f"{int(m.group(1))}. Saat"
            for j, tarih in tarihler.items():
                if j < len(r) and r[j].strip():
                    sinavlar.append({"tarih": tarih, "oturum": oturum, "seviye": sev,
                                     "ders": " ".join(r[j].split()), "ogrenci_nolari": None})
    return sinavlar


def takvim_oku(yol):
    """PDF veya Excel sınav takvimini okur. (baslik_satirlari, sinavlar) döndürür."""
    yol = str(yol)
    if yol.lower().endswith(".pdf"):
        import pdfplumber
        tablolar, baslik = [], []
        with pdfplumber.open(yol) as pdf:
            for sayfa in pdf.pages:
                tablolar += sayfa.extract_tables()
                metin = (sayfa.extract_text() or "").splitlines()
                if not baslik:
                    baslik = [s.strip() for s in metin[:2]]
        sinavlar = _tablolari_coz(tablolar)
    else:
        from python_calamine import CalamineWorkbook
        wb = CalamineWorkbook.from_path(yol)
        tablolar, baslik = [], []
        for ad in wb.sheet_names:
            satirlar = wb.get_sheet_by_name(ad).to_python()
            tablolar.append(satirlar)
            if not baslik:
                baslik = [_hucre(c) for r in satirlar[:2] for c in r if _hucre(c)][:2]
        sinavlar = _tablolari_coz(tablolar)
    sinavlar.sort(key=lambda s: (s["tarih"], int(re.search(r"\d+", s["oturum"])[0]),
                                 seviye_sirala_anahtari(s["seviye"])))
    return baslik, sinavlar
