"""PDF raporları: Liste 1 (öğrenci bazlı) ve Liste 2 (salon bazlı + seviye özeti). Modern, sade tasarım."""
import base64
import io
import os
import sys
from collections import Counter

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from .okuma import seviye_adi, seviye_sirala_anahtari, tarih_yaz

_KOK = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_YAZI_AILELERI = [
    # (normal, orta, kalın, ince)
    ("Poppins-Regular.ttf", "Poppins-Medium.ttf", "Poppins-Bold.ttf", "Poppins-Light.ttf"),
]
_YEDEK_FONTLAR = [
    (os.path.join(_KOK, "fonts", "DejaVuSans.ttf"), os.path.join(_KOK, "fonts", "DejaVuSans-Bold.ttf")),
    (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\segoeuib.ttf"),
    (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]
FONT_R, FONT_M, FONT_B, FONT_L = "KR", "KM", "KB", "KL"
_font_hazir = False

# Renkler
MUREKKEP = colors.HexColor("#111827")
SOLUK = colors.HexColor("#6b7280")
CIZGI = colors.HexColor("#e5e7eb")
VURGU = colors.HexColor("#2f6fed")
KART = colors.HexColor("#f3f6fd")
SEVIYE_RENK = {"Hazırlık": "#8b5cf6", "9": "#2f6fed", "10": "#10b981", "11": "#f59e0b", "12": "#ef4444"}


def _renk(seviye):
    return colors.HexColor(SEVIYE_RENK.get(seviye, "#64748b"))


def _font_kaydet():
    global _font_hazir
    if _font_hazir:
        return
    for dosyalar in _YAZI_AILELERI:
        yollar = [os.path.join(_KOK, "fonts", d) for d in dosyalar]
        if all(os.path.exists(y) for y in yollar):
            for ad, y in zip((FONT_R, FONT_M, FONT_B, FONT_L), yollar):
                pdfmetrics.registerFont(TTFont(ad, y))
            _font_hazir = True
            return
    for normal, kalin in _YEDEK_FONTLAR:
        if os.path.exists(normal) and os.path.exists(kalin):
            pdfmetrics.registerFont(TTFont(FONT_R, normal))
            pdfmetrics.registerFont(TTFont(FONT_B, kalin))
            pdfmetrics.registerFont(TTFont(FONT_M, normal))
            pdfmetrics.registerFont(TTFont(FONT_L, normal))
            _font_hazir = True
            return
    raise RuntimeError("Türkçe karakterli yazı tipi bulunamadı. 'fonts' klasörüne Poppins-*.ttf koyun.")


def ad_bicimle(metin):
    """'MUHAMMET EMİN' -> 'Muhammet Emin' (Türkçe büyük/küçük harf kurallarıyla)."""
    def kucuk(s):
        return s.replace("İ", "i").replace("I", "ı").lower()

    def buyuk(c):
        return {"i": "İ", "ı": "I"}.get(c, c.upper())

    sonuc = []
    for kelime in metin.split():
        k = kucuk(kelime)
        parca, yeni_kelime = [], True
        for c in k:
            parca.append(buyuk(c) if yeni_kelime else c)
            yeni_kelime = c in "-'’."
        sonuc.append("".join(parca))
    return " ".join(sonuc)


def _stil(ad, **kw):
    taban = dict(fontName=FONT_R, fontSize=9, leading=12, textColor=MUREKKEP)
    taban.update(kw)
    return ParagraphStyle(ad, **taban)


def _escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _belge(yol, baslik, proje):
    okul = (proje.okul_adi or "").strip()
    imzalar = []
    if (proje.kurum.get("mudur_yrd") or "").strip():
        imzalar.append(f"Müdür Yardımcısı: {proje.kurum['mudur_yrd'].strip()}")
    if (proje.kurum.get("mudur") or "").strip():
        imzalar.append(f"Okul Müdürü: {proje.kurum['mudur'].strip()}")

    def sayfa(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(VURGU)
        canvas.rect(0, h - 3 * mm, w, 3 * mm, stroke=0, fill=1)
        canvas.setStrokeColor(CIZGI)
        canvas.setLineWidth(0.6)
        canvas.line(16 * mm, 13 * mm, w - 16 * mm, 13 * mm)
        canvas.setFont(FONT_L, 7.5)
        canvas.setFillColor(SOLUK)
        canvas.drawString(16 * mm, 8.5 * mm, okul)
        if imzalar:
            canvas.drawCentredString(w * 0.62, 8.5 * mm, "   ·   ".join(imzalar))
        canvas.drawRightString(w - 16 * mm, 8.5 * mm, f"Sayfa {doc.page}")
        canvas.restoreState()

    belge = SimpleDocTemplate(yol, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                              topMargin=14 * mm, bottomMargin=18 * mm, title=baslik,
                              author="Kelebek")
    return belge, sayfa


GENISLIK = 178 * mm


def _kartlar(kartlar):
    """kartlar: [(etiket, değer, genişlik_mm)] -> yan yana açık renkli bilgi kutuları."""
    hucre, genislik, stil = [], [], []
    for i, (etiket, deger, w) in enumerate(kartlar):
        if i:
            hucre.append("")
            genislik.append(3 * mm)
        p = Paragraph(f'<font name="{FONT_M}" size="6.8" color="#6b7280">{_escape(etiket.upper())}</font><br/>'
                      f'<font name="{FONT_M}" size="10" color="#111827">{_escape(deger)}</font>',
                      _stil("kart", leading=14))
        hucre.append(p)
        genislik.append(w * mm)
        col = len(hucre) - 1
        stil.append(("BACKGROUND", (col, 0), (col, 0), KART))
    t = Table([hucre], colWidths=genislik)
    t.setStyle(TableStyle(stil + [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                  ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    return t


def _logo(proje, kutu=20 * mm):
    """Kurum logosunu (data URL) en-boy oranı korunarak bir Image olarak döndürür; yoksa None."""
    veri = (proje.kurum.get("logo") or "")
    if "," not in veri:
        return None
    try:
        ham = base64.b64decode(veri.split(",", 1)[1])
        gw, gh = ImageReader(io.BytesIO(ham)).getSize()
        oran = min(kutu / gw, kutu / gh)
        img = Image(io.BytesIO(ham), width=gw * oran, height=gh * oran)
        img.hAlign = "RIGHT"
        return img
    except Exception:
        return None


def _ust(proje, etiket, buyuk, kartlar):
    alt = " · ".join(x for x in ((proje.kurum.get("alt_baslik") or "").strip(),
                                 (proje.takvim_basligi or "").strip()) if x)
    sol = [Paragraph(f'<font name="{FONT_B}" size="8" color="#2f6fed">{_escape(etiket.upper())}</font>',
                     _stil("e", leading=10)),
           Spacer(1, 1.5 * mm),
           Paragraph(_escape(buyuk), _stil("b", fontName=FONT_B, fontSize=24, leading=28)),
           Paragraph(_escape((proje.okul_adi or "").strip()), _stil("o", fontName=FONT_L, fontSize=8.5,
                                                                   textColor=SOLUK, leading=11))]
    if alt:
        sol.append(Paragraph(_escape(alt), _stil("a", fontName=FONT_L, fontSize=7.5, textColor=SOLUK, leading=10)))
    logo = _logo(proje)
    if logo is not None:
        ust = Table([[sol, logo]], colWidths=[GENISLIK - 26 * mm, 26 * mm])
        ust.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        sol = [ust]
    return sol + [Spacer(1, 4.5 * mm), _kartlar(kartlar), Spacer(1, 6 * mm)]


def _tablo(basliklar, satirlar, genislikler, seviyeler, hizalar=None, vurgu_sutunlari=()):
    """Izgarasız modern tablo. Sol kenarda seviye rengi şeridi bulunur."""
    ust = [Paragraph(f'<font name="{FONT_M}" size="7" color="#6b7280">{_escape(b.upper())}</font>', _stil("th"))
           for b in basliklar]
    veri = [[""] + ust]
    for satir in satirlar:
        veri.append([""] + satir)
    t = Table(veri, colWidths=[2 * mm] + genislikler, repeatRows=1)
    stil = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.7), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.7),
            ("LEFTPADDING", (1, 0), (-1, -1), 6), ("RIGHTPADDING", (1, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 0),
            ("LINEBELOW", (0, 0), (-1, 0), 0.9, MUREKKEP),
            ("LINEBELOW", (1, 1), (-1, -1), 0.4, CIZGI),
            ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, 0), (-1, 0), 5)]
    for i, sev in enumerate(seviyeler, start=1):
        if sev:
            stil.append(("BACKGROUND", (0, i), (0, i), _renk(sev)))
            stil.append(("LINEBELOW", (0, i), (0, i), 1.2, colors.white))
    for h, (c0, c1, tur) in enumerate(hizalar or []):
        stil.append(("ALIGN", (c0 + 1, 0), (c1 + 1, -1), tur))
    t.setStyle(TableStyle(stil))
    return t


def _p(metin, **kw):
    return Paragraph(_escape(metin), _stil("h", **kw))


def _ogr_yeri(proje, anahtar):
    yer = {}
    for salon, koltuklar in proje.dagitimlar[anahtar]["yerlesim"].items():
        for i, no in enumerate(koltuklar):
            if no:
                yer[no] = (salon, i + 1)
    return yer


def liste1_pdf(proje, oturumlar, yol):
    """Öğrenci bazlı liste: her sınıf için öğrencilerin salon ve sıra numarası."""
    _font_kaydet()
    ogeler = []
    tablo = proje.ogrenci_tablosu()
    for anahtar in oturumlar:
        if anahtar not in proje.dagitimlar:
            continue
        plan = proje.oturum_plani(anahtar)
        yer = _ogr_yeri(proje, anahtar)
        siniflar = [s for s in proje.sinif_sirali() if s["anahtar"] in {tablo[no][0] for no in yer}]
        tarih, saat = anahtar.split("|")
        for s in siniflar:
            sinav = plan["sinavlar"][s["seviye"]]
            ogeler += _ust(proje, "Öğrenci sınav yerleri", proje.sinif_adi(s["anahtar"]), [
                ("Tarih", tarih_yaz(tarih), 58), ("Saat", saat, 22), ("Ders", ad_bicimle(sinav["ders"]), 68),
                ("Öğrenci", str(sum(1 for o in s["ogrenciler"] if o["no"] in yer)), 20)])
            satirlar, sevler = [], []
            for i, o in enumerate(s["ogrenciler"], 1):
                ad = ad_bicimle(f"{o['ad']} {o['soyad']}")
                if o["no"] in yer:
                    salon, koltuk = yer[o["no"]]
                    satirlar.append([_p(str(i), textColor=SOLUK), _p(o["no"], textColor=SOLUK),
                                     _p(ad, fontName=FONT_M),
                                     _p(proje.sinif_adi(salon), fontName=FONT_M),
                                     _p(str(koltuk), fontName=FONT_B, fontSize=11, textColor=VURGU, alignment=1)])
                    sevler.append(proje.siniflar[salon]["seviye"])
                else:
                    satirlar.append([_p(str(i), textColor=SOLUK), _p(o["no"], textColor=SOLUK), _p(ad),
                                     _p("Kelebek dışı", textColor=SOLUK), _p("—", textColor=SOLUK, alignment=1)])
                    sevler.append(None)
            ogeler += [_tablo(["S.No", "Okul no", "Adı soyadı", "Sınav salonu", "Sıra"], satirlar,
                              [13 * mm, 20 * mm, 70 * mm, 50 * mm, 21.5 * mm], sevler),
                       PageBreak()]
    if not ogeler:
        raise ValueError("Raporlanacak karma sonucu yok.")
    ogeler.pop()
    belge, sayfa = _belge(yol, "Öğrenci Sınav Yerleri", proje)
    belge.build(ogeler, onFirstPage=sayfa, onLaterPages=sayfa)


def _ozet(plan, say):
    """Seviye başına küçük renkli kartlar: sayı + ders adı."""
    hucre, genislik, stil = [], [], []
    seviyeler = sorted(say, key=seviye_sirala_anahtari)
    n = len(seviyeler) + 1
    w = (GENISLIK - (n - 1) * 3 * mm) / n
    for sev in seviyeler:
        rk = SEVIYE_RENK.get(sev, "#64748b")
        ders = ad_bicimle(plan["sinavlar"][sev]["ders"])
        p = [Paragraph(_escape(seviye_adi(sev)), _stil("oz_a", fontName=FONT_M, fontSize=7.5, leading=10,
                                                         textColor=colors.HexColor(rk))),
             Paragraph(str(say[sev]), _stil("oz_b", fontName=FONT_B, fontSize=18, leading=24)),
             Paragraph(_escape(ders), _stil("oz_c", fontName=FONT_L, fontSize=6.6, leading=8.5, textColor=SOLUK))]
        if hucre:
            hucre.append("")
            genislik.append(3 * mm)
        hucre.append(p)
        genislik.append(w)
        c = len(hucre) - 1
        stil += [("BACKGROUND", (c, 0), (c, 0), KART), ("LINEABOVE", (c, 0), (c, 0), 2, colors.HexColor(rk))]
    hucre += ["", [Paragraph("Toplam", _stil("oz_d", fontName=FONT_M, fontSize=7.5, leading=10, textColor=colors.white)),
                   Paragraph(str(sum(say.values())), _stil("oz_e", fontName=FONT_B, fontSize=18, leading=24,
                                                           textColor=colors.white)),
                   Paragraph("öğrenci", _stil("oz_f", fontName=FONT_L, fontSize=6.6, leading=8.5,
                                              textColor=colors.HexColor("#dbe7ff")))]]
    genislik += [3 * mm, w]
    c = len(hucre) - 1
    stil.append(("BACKGROUND", (c, 0), (c, 0), VURGU))
    t = Table([hucre], colWidths=genislik)
    t.setStyle(TableStyle(stil + [("VALIGN", (0, 0), (-1, -1), "TOP"),
                                  ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]))
    return t


def liste2_pdf(proje, oturumlar, yol):
    """Salon bazlı liste: sıra sırasıyla öğrenciler ve altında seviye özeti."""
    _font_kaydet()
    ogeler = []
    tablo = proje.ogrenci_tablosu()
    for anahtar in oturumlar:
        d = proje.dagitimlar.get(anahtar)
        if not d:
            continue
        plan = proje.oturum_plani(anahtar)
        tarih, saat = anahtar.split("|")
        for salon in plan["salonlar"]:
            koltuklar = d["yerlesim"].get(salon)
            if koltuklar is None:
                continue
            dolu = sum(1 for k in koltuklar if k)
            ogeler += _ust(proje, "Salon sınav listesi", proje.sinif_adi(salon), [
                ("Tarih", tarih_yaz(tarih), 70), ("Saat", saat, 28), ("Öğrenci", f"{dolu} / {len(koltuklar)}", 30),
                ("Salon", proje.sinif_adi(salon), 41)])
            satirlar, sevler, say = [], [], Counter()
            for i, no in enumerate(koltuklar, 1):
                if no:
                    sinif_a, o = tablo[no]
                    sev = proje.siniflar[sinif_a]["seviye"]
                    say[sev] += 1
                    satirlar.append([_p(str(i), fontName=FONT_B, textColor=VURGU, fontSize=9.5, alignment=1),
                                     _p(no, textColor=SOLUK),
                                     _p(ad_bicimle(f"{o['ad']} {o['soyad']}"), fontName=FONT_M),
                                     _p(proje.sinif_adi(sinif_a)), ""])
                    sevler.append(sev)
                else:
                    satirlar.append([_p(str(i), fontName=FONT_B, textColor=SOLUK, alignment=1), "",
                                     _p("boş sıra", fontName=FONT_L, textColor=SOLUK), "", ""])
                    sevler.append(None)
            ogeler.append(_tablo(["Sıra", "Okul no", "Adı soyadı", "Sınıfı", "İmza"], satirlar,
                                 [14 * mm, 20 * mm, 66 * mm, 32 * mm, 44 * mm], sevler))
            ogeler += [Spacer(1, 6 * mm), KeepTogether([_ozet(plan, say)]), PageBreak()]
        haric = [proje.sinif_adi(a) for a in proje.haric.get(anahtar, []) if a in proje.siniflar]
        if haric:
            ogeler += _ust(proje, "Kelebek sistemi dışındaki sınıflar", "Kendi sınıflarında", [
                ("Tarih", tarih_yaz(tarih), 70), ("Saat", saat, 28), ("Sınıflar", ", ".join(haric), 80)])
            ogeler.append(PageBreak())
    if not ogeler:
        raise ValueError("Raporlanacak karma sonucu yok.")
    ogeler.pop()
    belge, sayfa = _belge(yol, "Salon Sınav Listeleri", proje)
    belge.build(ogeler, onFirstPage=sayfa, onLaterPages=sayfa)


def dosya_adi(anahtar, ek):
    tarih, oturum = anahtar.split("|")
    saat = "".join(c for c in oturum if c.isdigit())
    return f"{tarih}_{saat}-saat_{ek}.pdf"


def raporlari_olustur(proje, oturumlar, klasor, liste1=True, liste2=True, ayri_dosyalar=True):
    """Seçilen oturumlar için PDF'leri üretir, oluşan dosya yollarını döndürür."""
    os.makedirs(klasor, exist_ok=True)
    olusan = []
    if ayri_dosyalar:
        for k in oturumlar:
            if liste1:
                y = os.path.join(klasor, dosya_adi(k, "Liste1_OgrenciYerleri"))
                liste1_pdf(proje, [k], y)
                olusan.append(y)
            if liste2:
                y = os.path.join(klasor, dosya_adi(k, "Liste2_SalonListeleri"))
                liste2_pdf(proje, [k], y)
                olusan.append(y)
    else:
        if liste1:
            y = os.path.join(klasor, "Liste1_OgrenciYerleri.pdf")
            liste1_pdf(proje, oturumlar, y)
            olusan.append(y)
        if liste2:
            y = os.path.join(klasor, "Liste2_SalonListeleri.pdf")
            liste2_pdf(proje, oturumlar, y)
            olusan.append(y)
    return olusan
