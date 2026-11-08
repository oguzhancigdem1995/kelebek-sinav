"""PDF raporları: Liste 1 (öğrenci bazlı) ve Liste 2 (salon bazlı + seviye özeti)."""
import os
from collections import Counter

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from .okuma import seviye_adi, tarih_yaz

import sys
_KOK = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_ADAYLARI = [
    (os.path.join(_KOK, "fonts", "DejaVuSans.ttf"), os.path.join(_KOK, "fonts", "DejaVuSans-Bold.ttf")),
    (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
    (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\segoeuib.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]
_font_hazir = False
FONT, FONT_B = "KelebekFont", "KelebekFont-Bold"


def _font_kaydet():
    global _font_hazir
    if _font_hazir:
        return
    for normal, kalin in _FONT_ADAYLARI:
        if os.path.exists(normal) and os.path.exists(kalin):
            pdfmetrics.registerFont(TTFont(FONT, normal))
            pdfmetrics.registerFont(TTFont(FONT_B, kalin))
            _font_hazir = True
            return
    raise RuntimeError("Türkçe karakterli yazı tipi bulunamadı. 'fonts' klasörüne "
                       "DejaVuSans.ttf ve DejaVuSans-Bold.ttf koyun.")


def _stiller():
    return {
        "okul": ParagraphStyle("okul", fontName=FONT_B, fontSize=11, alignment=1, leading=14),
        "baslik": ParagraphStyle("baslik", fontName=FONT_B, fontSize=13, alignment=1, leading=16,
                                 spaceAfter=2),
        "bilgi": ParagraphStyle("bilgi", fontName=FONT, fontSize=10, leading=13),
        "kucuk": ParagraphStyle("kucuk", fontName=FONT, fontSize=8, leading=10,
                                textColor=colors.HexColor("#444444")),
        "hucre": ParagraphStyle("hucre", fontName=FONT, fontSize=9, leading=11),
    }


def _tablo_stili(satir_sayisi, bas_renk="#d9e2f3"):
    return TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("FONTNAME", (0, 0), (-1, 0), FONT_B),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(bas_renk)),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#777777")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ])


def _ders_satiri(plan):
    parcalar = []
    for sev, sinav in plan["sinavlar"].items():
        parcalar.append(f"{seviye_adi(sev)}: {sinav['ders']}")
    return " | ".join(parcalar)


def _ust_bilgi(proje, st, baslik, oturum_anahtar, ek_satirlar):
    tarih, oturum = oturum_anahtar.split("|")
    ogeler = [Paragraph((proje.okul_adi or "").upper(), st["okul"]),
              Paragraph(baslik, st["baslik"])]
    if proje.takvim_basligi:
        ogeler.append(Paragraph(proje.takvim_basligi, ParagraphStyle(
            "tb", parent=st["kucuk"], alignment=1)))
    ogeler.append(Spacer(1, 3 * mm))
    ogeler.append(Paragraph(f"<b>Tarih:</b> {tarih_yaz(tarih)} &nbsp;&nbsp; <b>Saat:</b> {oturum}",
                            st["bilgi"]))
    for s in ek_satirlar:
        ogeler.append(Paragraph(s, st["bilgi"]))
    ogeler.append(Spacer(1, 3 * mm))
    return ogeler


def _belge(yol, baslik):
    return SimpleDocTemplate(yol, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                             topMargin=14 * mm, bottomMargin=14 * mm, title=baslik,
                             author="Kelebek Sınav Dağıtım")


def _ogr_yeri(proje, anahtar):
    """ogr_no -> (salon anahtarı, koltuk numarası 1'den)"""
    yer = {}
    for salon, koltuklar in proje.dagitimlar[anahtar]["yerlesim"].items():
        for i, no in enumerate(koltuklar):
            if no:
                yer[no] = (salon, i + 1)
    return yer


def _sayfa_no(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.drawRightString(A4[0] - 15 * mm, 8 * mm, f"Sayfa {doc.page}")
    canvas.restoreState()


def liste1_pdf(proje, oturumlar, yol):
    """Öğrenci bazlı liste: her sınıf için öğrencilerin salon ve sıra numarası."""
    _font_kaydet()
    st = _stiller()
    ogeler = []
    tablo = proje.ogrenci_tablosu()
    for anahtar in oturumlar:
        if anahtar not in proje.dagitimlar:
            continue
        plan = proje.oturum_plani(anahtar)
        yer = _ogr_yeri(proje, anahtar)
        siniflar = [s for s in proje.sinif_sirali() if s["anahtar"] in
                    {tablo[no][0] for no in yer}]
        for s in siniflar:
            sinav = plan["sinavlar"][s["seviye"]]
            ogeler += _ust_bilgi(proje, st, "ÖĞRENCİ SINAV YERLERİ", anahtar, [
                f"<b>Sınıf:</b> {proje.sinif_adi(s['anahtar'])} &nbsp;&nbsp; <b>Ders:</b> {sinav['ders']}"])
            satirlar = [["S.No", "Okul No", "Adı Soyadı", "Sınav Salonu", "Sıra No"]]
            for i, o in enumerate(s["ogrenciler"], 1):
                if o["no"] in yer:
                    salon, koltuk = yer[o["no"]]
                    satirlar.append([str(i), o["no"], f"{o['ad']} {o['soyad']}",
                                     proje.sinif_adi(salon), str(koltuk)])
                else:
                    satirlar.append([str(i), o["no"], f"{o['ad']} {o['soyad']}", "—", "—"])
            t = Table(satirlar, colWidths=[14 * mm, 22 * mm, 72 * mm, 42 * mm, 20 * mm], repeatRows=1)
            t.setStyle(_tablo_stili(len(satirlar)))
            t.setStyle(TableStyle([("ALIGN", (0, 0), (1, -1), "CENTER"), ("ALIGN", (4, 0), (4, -1), "CENTER")]))
            ogeler += [t, PageBreak()]
    if not ogeler:
        raise ValueError("Raporlanacak karma sonucu yok.")
    ogeler.pop()  # son PageBreak
    _belge(yol, "Öğrenci Sınav Yerleri").build(ogeler, onFirstPage=_sayfa_no, onLaterPages=_sayfa_no)


def liste2_pdf(proje, oturumlar, yol):
    """Salon bazlı liste: sıra sırasıyla öğrenciler ve altında seviye özeti."""
    _font_kaydet()
    st = _stiller()
    ogeler = []
    tablo = proje.ogrenci_tablosu()
    for anahtar in oturumlar:
        d = proje.dagitimlar.get(anahtar)
        if not d:
            continue
        plan = proje.oturum_plani(anahtar)
        for salon in plan["salonlar"]:
            koltuklar = d["yerlesim"].get(salon)
            if koltuklar is None:
                continue
            ogeler += _ust_bilgi(proje, st, "SALON SINAV LİSTESİ", anahtar, [
                f"<b>Sınav Salonu:</b> {proje.sinif_adi(salon)}"])
            satirlar = [["Sıra", "Okul No", "Adı Soyadı", "Sınıfı", "İmza"]]
            say = Counter()
            for i, no in enumerate(koltuklar, 1):
                if no:
                    sinif_a, o = tablo[no]
                    sev = proje.siniflar[sinif_a]["seviye"]
                    say[sev] += 1
                    satirlar.append([str(i), no, f"{o['ad']} {o['soyad']}", proje.sinif_adi(sinif_a), ""])
                else:
                    satirlar.append([str(i), "", "(boş)", "", ""])
            t = Table(satirlar, colWidths=[12 * mm, 20 * mm, 66 * mm, 36 * mm, 36 * mm], repeatRows=1)
            t.setStyle(_tablo_stili(len(satirlar)))
            t.setStyle(TableStyle([("ALIGN", (0, 0), (1, -1), "CENTER")]))
            ozet = [["Sınıf Seviyesi", "Ders", "Öğrenci Sayısı"]]
            from .okuma import seviye_sirala_anahtari
            for sev in sorted(say, key=seviye_sirala_anahtari):
                ozet.append([seviye_adi(sev), plan["sinavlar"][sev]["ders"], str(say[sev])])
            ozet.append(["TOPLAM", "", str(sum(say.values()))])
            ot = Table(ozet, colWidths=[40 * mm, 90 * mm, 40 * mm])
            ot.setStyle(_tablo_stili(len(ozet), "#e2efda"))
            ot.setStyle(TableStyle([("FONTNAME", (0, -1), (-1, -1), FONT_B),
                                    ("ALIGN", (2, 0), (2, -1), "CENTER")]))
            ogeler += [t, Spacer(1, 5 * mm),
                       KeepTogether([Paragraph("<b>Özet</b>", st["bilgi"]), Spacer(1, 1.5 * mm), ot]),
                       PageBreak()]
        haric = [proje.sinif_adi(a) for a in proje.haric.get(anahtar, []) if a in proje.siniflar]
        if haric:
            ogeler += _ust_bilgi(proje, st, "KELEBEK SİSTEMİ DIŞINDAKİ SINIFLAR", anahtar, [
                "Bu sınıflar kelebek dağıtımına dahil edilmemiş, kendi sınıflarında sınava girer:",
                ", ".join(haric)])
            ogeler.append(PageBreak())
    if not ogeler:
        raise ValueError("Raporlanacak karma sonucu yok.")
    ogeler.pop()
    _belge(yol, "Salon Sınav Listeleri").build(ogeler, onFirstPage=_sayfa_no, onLaterPages=_sayfa_no)


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
