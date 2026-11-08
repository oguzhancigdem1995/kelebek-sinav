"""Tkinter masaüstü arayüzü: kenar çubuğu + 5 sayfa. Mantık cekirdek/okuma/rapor modüllerindedir."""
import os
import re
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter import font as tkfont

from . import cekirdek, okuma, rapor
from .okuma import seviye_adi, tarih_yaz

KOK = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARSAYILAN_RAPOR_KLASORU = os.path.join(os.path.expanduser("~"), "Documents", "KelebekRaporlar")

# Renkler
ARKA, KENAR, KENAR_SEC = "#f4f5f7", "#1e2a3a", "#2e415a"
VURGU, VURGU_KOYU, VURGU_ACIK = "#2f6fed", "#2459c4", "#dbe7ff"
YAZI, SOLUK, CIZGI, KART = "#1f2937", "#6b7280", "#e5e7eb", "#ffffff"
HATA, UYARI = "#fde2e2", "#fff3cd"

SAYFALAR = [("siniflar", "1   Sınıflar"), ("takvim", "2   Takvim"), ("karma", "3   Karma"),
            ("yerlesim", "4   Yerleşim"), ("rapor", "5   Raporlar")]


def kisa_ad(anahtar):
    seviye, sube = anahtar.split("-", 1)
    return f"{'Haz' if seviye == 'Hazırlık' else seviye}-{sube}"


def _klasoru_ac(yol):
    try:
        if sys.platform.startswith("win"):
            os.startfile(yol)  # noqa
        elif sys.platform == "darwin":
            subprocess.Popen(["open", yol])
        else:
            subprocess.Popen(["xdg-open", yol])
    except Exception:
        pass


class Uygulama(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kelebek")
        self.geometry("1180x740")
        self.minsize(980, 620)
        self.configure(bg=ARKA)
        self.proje = cekirdek.Proje()
        self.yol = None
        self.kirli = False
        self.isaretli = None
        self.geri_al_yigini = []
        self._stil()
        self._simge()
        self._iskelet()
        self._sayfa_siniflar()
        self._sayfa_takvim()
        self._sayfa_karma()
        self._sayfa_yerlesim()
        self._sayfa_rapor()
        self.bind("<Control-s>", lambda _e: self.proje_kaydet())
        self.protocol("WM_DELETE_WINDOW", self._kapat)
        self.yenile_hepsi()
        self.git("siniflar")

    # ------------------------------------------------------------------ görünüm
    def _stil(self):
        aile = "Segoe UI" if "Segoe UI" in tkfont.families(self) else "Helvetica"
        self.aile = aile
        for ad in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
            try:
                tkfont.nametofont(ad).configure(family=aile, size=10)
            except tk.TclError:
                pass
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure(".", background=ARKA, foreground=YAZI, font=(aile, 10))
        st.configure("TFrame", background=ARKA)
        st.configure("Kart.TFrame", background=KART)
        st.configure("TLabel", background=ARKA, foreground=YAZI)
        st.configure("Soluk.TLabel", foreground=SOLUK)
        st.configure("Baslik.TLabel", font=(aile, 20, "bold"))
        st.configure("TButton", padding=(14, 7), background=KART, bordercolor=CIZGI, relief="flat",
                     borderwidth=1)
        st.map("TButton", background=[("active", "#eef1f6")])
        st.configure("Vurgu.TButton", background=VURGU, foreground="white", bordercolor=VURGU, padding=(16, 7),
                     font=(aile, 10, "bold"))
        st.map("Vurgu.TButton", background=[("active", VURGU_KOYU)])
        st.configure("Treeview", background=KART, fieldbackground=KART, rowheight=30, borderwidth=0,
                     font=(aile, 10))
        st.configure("Treeview.Heading", background="#eef1f6", foreground=SOLUK, font=(aile, 9, "bold"),
                     padding=(8, 7), relief="flat")
        st.map("Treeview", background=[("selected", VURGU_ACIK)], foreground=[("selected", YAZI)])
        st.configure("TCheckbutton", background=ARKA)
        st.configure("TRadiobutton", background=ARKA)
        st.configure("TEntry", padding=5, fieldbackground=KART)
        st.configure("TCombobox", padding=5)

    def _simge(self):
        """Pencere / görev çubuğu simgesi ve kenar çubuğu logosu."""
        self.logo = None
        try:
            png = os.path.join(KOK, "assets", "kelebek.png")
            ico = os.path.join(KOK, "assets", "kelebek.ico")
            tam = tk.PhotoImage(file=png)
            self.iconphoto(True, tam)
            self.logo = tam.subsample(10, 10)   # 512 px -> ~51 px
            if sys.platform.startswith("win") and os.path.exists(ico):
                self.iconbitmap(ico)
        except Exception:
            pass

    def _iskelet(self):
        self.kenar = tk.Frame(self, bg=KENAR, width=190)
        self.kenar.pack(side="left", fill="y")
        self.kenar.pack_propagate(False)
        baslik = tk.Frame(self.kenar, bg=KENAR)
        baslik.pack(fill="x", padx=20, pady=(24, 24))
        if self.logo is not None:
            tk.Label(baslik, image=self.logo, bg=KENAR).pack(side="left", padx=(0, 10))
        yazi = tk.Frame(baslik, bg=KENAR)
        yazi.pack(side="left")
        tk.Label(yazi, text="Kelebek", bg=KENAR, fg="white", font=(self.aile, 17, "bold"), anchor="w").pack(anchor="w")
        tk.Label(yazi, text="Sınav yerleşimi", bg=KENAR, fg="#9fb0c7", font=(self.aile, 9), anchor="w").pack(anchor="w")
        self.nav = {}
        for ad, etiket in SAYFALAR:
            b = tk.Button(self.kenar, text=etiket, anchor="w", bg=KENAR, fg="#d7e0ee", relief="flat", bd=0,
                          activebackground=KENAR_SEC, activeforeground="white", font=(self.aile, 11),
                          padx=20, pady=11, cursor="hand2", command=lambda a=ad: self.git(a))
            b.pack(fill="x")
            self.nav[ad] = b
        alt = tk.Frame(self.kenar, bg=KENAR)
        alt.pack(side="bottom", fill="x", pady=16)
        for metin, komut in (("Projeyi kaydet", self.proje_kaydet), ("Proje aç", self.proje_ac)):
            tk.Button(alt, text=metin, anchor="w", bg=KENAR, fg="#9fb0c7", relief="flat", bd=0,
                      activebackground=KENAR_SEC, activeforeground="white", font=(self.aile, 10),
                      padx=20, pady=6, cursor="hand2", command=komut).pack(fill="x")
        sag = tk.Frame(self, bg=ARKA)
        sag.pack(side="left", fill="both", expand=True)
        self.alan = tk.Frame(sag, bg=ARKA)
        self.alan.pack(fill="both", expand=True)
        self.alan.grid_rowconfigure(0, weight=1)
        self.alan.grid_columnconfigure(0, weight=1)
        self.durum = tk.StringVar(value="")
        tk.Label(sag, textvariable=self.durum, bg=ARKA, fg=SOLUK, anchor="w", font=(self.aile, 9)).pack(
            fill="x", padx=28, pady=(0, 8))
        self.sayfalar = {}

    def _sayfa(self, ad, baslik, aciklama):
        f = ttk.Frame(self.alan)
        f.grid(row=0, column=0, sticky="nsew")
        self.sayfalar[ad] = f
        ust = ttk.Frame(f)
        ust.pack(fill="x", padx=28, pady=(24, 10))
        ttk.Label(ust, text=baslik, style="Baslik.TLabel").pack(anchor="w")
        ttk.Label(ust, text=aciklama, style="Soluk.TLabel").pack(anchor="w", pady=(2, 0))
        return f

    def _arac_cubugu(self, sayfa):
        c = ttk.Frame(sayfa)
        c.pack(fill="x", padx=28, pady=(0, 12))
        return c

    def _dugme(self, ust, metin, komut, vurgu=False):
        b = ttk.Button(ust, text=metin, command=komut, style="Vurgu.TButton" if vurgu else "TButton")
        b.pack(side="left", padx=(0, 8))
        return b

    def _tablo(self, ust, kolonlar, yukseklik=None, secim="extended", **pack):
        """kolonlar: [(anahtar, başlık, genişlik, hizalama)]"""
        cerceve = ttk.Frame(ust)
        kw = {"height": yukseklik} if yukseklik else {}
        tree = ttk.Treeview(cerceve, columns=[k[0] for k in kolonlar], show="headings", selectmode=secim, **kw)
        sb = ttk.Scrollbar(cerceve, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        for k, b, w, h in kolonlar:
            tree.heading(k, text=b, anchor=h)
            tree.column(k, width=w, anchor=h)
        tree.tag_configure("hata", background=HATA)
        tree.tag_configure("isaret", background=UYARI)
        tree.tag_configure("soluk", foreground=SOLUK)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        cerceve.pack(fill="both", expand=True, padx=28, pady=(0, 12), **pack)
        return tree

    def git(self, ad):
        self.sayfalar[ad].tkraise()
        for a, b in self.nav.items():
            b.configure(bg=KENAR_SEC if a == ad else KENAR, fg="white" if a == ad else "#d7e0ee")
        if ad == "yerlesim":
            self.yenile_yerlesim_oturumlar()
        elif ad == "rapor":
            self.yenile_rapor()

    # ------------------------------------------------------------------ genel
    def _degisti(self):
        self.kirli = True

    def _kapat(self):
        if self.kirli and messagebox.askyesno("Kaydet", "Değişiklikler kaydedilsin mi?"):
            if not self.proje_kaydet():
                return
        self.destroy()

    def proje_kaydet(self, farkli=False):
        if farkli or not self.yol:
            yol = filedialog.asksaveasfilename(defaultextension=".kelebek",
                                               filetypes=[("Kelebek projesi", "*.kelebek")])
            if not yol:
                return False
            self.yol = yol
        self.proje.kaydet(self.yol)
        self.kirli = False
        self.durum.set(f"Kaydedildi: {self.yol}")
        return True

    def proje_ac(self):
        yol = filedialog.askopenfilename(filetypes=[("Kelebek projesi", "*.kelebek"), ("Tümü", "*.*")])
        if not yol:
            return
        try:
            self.proje = cekirdek.Proje.yukle(yol)
        except Exception as e:
            messagebox.showerror("Hata", f"Proje açılamadı:\n{e}")
            return
        self.yol = yol
        self.kirli = False
        self.yenile_hepsi()

    def yenile_hepsi(self):
        self.yenile_siniflar()
        self.yenile_takvim()
        self.yenile_karma()
        self.yenile_yerlesim_oturumlar()
        self.yenile_rapor()

    def _dagitimlari_temizle_sor(self, neden):
        if not self.proje.dagitimlar:
            return True
        if messagebox.askyesno("Mevcut karmalar", f"{neden}\nMevcut karma sonuçları silinsin mi?\n"
                                                  "(Silmezseniz eski yerleşimler güncel olmayabilir.)"):
            self.proje.dagitimlar = {}
            return True
        return False

    def _pencere(self, baslik):
        p = tk.Toplevel(self)
        p.title(baslik)
        p.configure(bg=ARKA)
        p.transient(self)
        return p

    # ------------------------------------------------------------------ sayfa 1: sınıflar
    def _sayfa_siniflar(self):
        f = self._sayfa("siniflar", "Sınıflar", "e-Okul sınıf listelerini yükleyin. Her sınıf bir sınav salonudur.")
        c = self._arac_cubugu(f)
        self._dugme(c, "Sınıf listesi yükle", self.sinif_yukle, True)
        self._dugme(c, "Salon düzeni", self.salon_ayarla)
        self.sinif_bilgi = tk.StringVar()
        ttk.Label(c, textvariable=self.sinif_bilgi, style="Soluk.TLabel").pack(side="right")
        self.tv_sinif = self._tablo(f, [("sinif", "Sınıf / Salon", 220, "w"), ("ogr", "Öğrenci", 90, "center"),
                                        ("duzen", "Sıra düzeni", 260, "w"), ("kap", "Sıra sayısı", 100, "center")])

    def yenile_siniflar(self):
        self.tv_sinif.delete(*self.tv_sinif.get_children())
        toplam = 0
        for s in self.proje.sinif_sirali():
            sl = s["salon"]
            toplam += len(s["ogrenciler"])
            duzen = "İkili" if sl["tur"] == "ikili" else "Tekli"
            if sl["tur"] == "ikili" and sl["komsuluk"] == "masa":
                duzen += " · yalnız masa eşi"
            if int(sl.get("sutun") or 0) > 0:
                duzen += f" · satırda {sl['sutun']} sıra (ön/arka dahil)"
            self.tv_sinif.insert("", "end", iid=s["anahtar"], values=(
                self.proje.sinif_adi(s["anahtar"]), len(s["ogrenciler"]), duzen,
                self.proje.kapasite(s["anahtar"])))
        self.sinif_bilgi.set(f"{len(self.proje.siniflar)} sınıf · {toplam} öğrenci" if self.proje.siniflar
                             else "Henüz liste yüklenmedi")

    def sinif_yukle(self):
        yollar = filedialog.askopenfilenames(title="Sınıf listeleri",
                                             filetypes=[("Excel", "*.xls *.xlsx"), ("Tümü", "*.*")])
        if not yollar:
            return
        tum, uyarilar = [], []
        for y in yollar:
            try:
                s, u = okuma.sinif_listesi_oku(y)
            except Exception as e:
                messagebox.showerror("Okunamadı", f"{os.path.basename(y)}\n{e}")
                return
            tum += s
            uyarilar += u
        if not tum:
            messagebox.showwarning("Sınıf bulunamadı", "Dosyada sınıf listesi bulunamadı.")
            return
        if not self._dagitimlari_temizle_sor("Sınıf listeleri değişiyor."):
            return
        self.proje.siniflari_ekle(tum)
        self._degisti()
        self.yenile_hepsi()
        if uyarilar:
            messagebox.showwarning("Uyarılar", "\n".join(uyarilar))
        self.durum.set(f"{len(tum)} sınıf yüklendi.")

    def salon_ayarla(self):
        secili = list(self.tv_sinif.selection())
        if not secili:
            messagebox.showinfo("Seçim yok", "Tabloda bir veya daha fazla sınıf seçin (Ctrl/Shift ile çoklu seçim).")
            return
        ilk = self.proje.siniflar[secili[0]]["salon"]
        p = self._pencere("Salon düzeni")
        tur = tk.StringVar(value=ilk["tur"])
        kural = tk.StringVar(value=ilk["komsuluk"])
        sutun = tk.IntVar(value=int(ilk.get("sutun") or 0))
        kap = tk.StringVar(value="" if len(secili) > 1 or not ilk.get("kapasite") else str(ilk["kapasite"]))
        r = ttk.Frame(p)
        r.pack(padx=24, pady=20)
        ttk.Label(r, text=f"{len(secili)} salon için düzen", font=(self.aile, 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Label(r, text="Sıra türü").grid(row=1, column=0, sticky="nw", pady=4)
        kutu = ttk.Frame(r)
        kutu.grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(kutu, text="Tekli", variable=tur, value="tekli").pack(anchor="w")
        ttk.Radiobutton(kutu, text="İkili", variable=tur, value="ikili").pack(anchor="w")
        ttk.Label(r, text="Yan yana sayılanlar").grid(row=2, column=0, sticky="nw", pady=4)
        kutu2 = ttk.Frame(r)
        kutu2.grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(kutu2, text="Art arda gelen sıra numaraları (en sıkı)", variable=kural,
                        value="ardarda").pack(anchor="w")
        ttk.Radiobutton(kutu2, text="Yalnız aynı masadakiler (ikili: 1-2, 3-4...)", variable=kural,
                        value="masa").pack(anchor="w")
        ttk.Label(r, text="Satırdaki sıra sayısı").grid(row=3, column=0, sticky="w", pady=4)
        kutu3 = ttk.Frame(r)
        kutu3.grid(row=3, column=1, sticky="w")
        ttk.Spinbox(kutu3, from_=0, to=20, textvariable=sutun, width=5).pack(side="left")
        ttk.Label(kutu3, text="  ön/arka komşuluk için, 0 = kullanma", style="Soluk.TLabel").pack(side="left")
        ttk.Label(r, text="Sıra sayısı").grid(row=4, column=0, sticky="w", pady=4)
        kutu4 = ttk.Frame(r)
        kutu4.grid(row=4, column=1, sticky="w")
        ttk.Entry(kutu4, textvariable=kap, width=6).pack(side="left")
        ttk.Label(kutu4, text="  boş = öğrenci sayısı kadar", style="Soluk.TLabel").pack(side="left")

        def tamam():
            try:
                k = int(kap.get()) if kap.get().strip() else None
                st = int(sutun.get())
            except ValueError:
                messagebox.showerror("Hata", "Sayı giriniz.")
                return
            if not self._dagitimlari_temizle_sor("Salon düzeni değişiyor."):
                return
            for a in secili:
                sl = self.proje.siniflar[a]["salon"]
                sl.update({"tur": tur.get(), "komsuluk": kural.get(), "sutun": st})
                if len(secili) == 1 or k is None:
                    sl["kapasite"] = k
            self._degisti()
            p.destroy()
            self.yenile_hepsi()

        alt = ttk.Frame(p)
        alt.pack(pady=(0, 18))
        ttk.Button(alt, text="Uygula", style="Vurgu.TButton", command=tamam).pack(side="left", padx=4)
        ttk.Button(alt, text="Vazgeç", command=p.destroy).pack(side="left", padx=4)

    # ------------------------------------------------------------------ sayfa 2: takvim
    def _sayfa_takvim(self):
        f = self._sayfa("takvim", "Sınav takvimi", "Takvim PDF veya Excel olarak yüklenir. "
                                                    "Ders adına çift tıklayarak düzeltebilirsiniz.")
        c = self._arac_cubugu(f)
        self._dugme(c, "Takvim yükle", self.takvim_yukle, True)
        self._dugme(c, "Dersi düzenle", self.ders_duzenle)
        self._dugme(c, "Sınav ekle", self.sinav_ekle)
        self._dugme(c, "Sil", self.sinav_sil)
        self._dugme(c, "Seçmeli öğrenci listesi", self.secmeli_liste)
        self.tv_takvim = self._tablo(f, [("tarih", "Tarih", 210, "w"), ("saat", "Saat", 80, "w"),
                                         ("seviye", "Seviye", 100, "w"), ("ders", "Ders", 380, "w"),
                                         ("liste", "Öğrenci listesi", 140, "w")])
        self.tv_takvim.bind("<Double-1>", lambda _e: self.ders_duzenle())
        alt = ttk.Frame(f)
        alt.pack(fill="x", padx=28, pady=(0, 6))
        self.okul_var, self.baslik_var = tk.StringVar(), tk.StringVar()
        ttk.Label(alt, text="Raporlarda görünen okul adı", style="Soluk.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(alt, text="Takvim başlığı", style="Soluk.TLabel").grid(row=0, column=1, sticky="w", padx=(12, 0))
        e1 = ttk.Entry(alt, textvariable=self.okul_var, width=48)
        e2 = ttk.Entry(alt, textvariable=self.baslik_var, width=44)
        e1.grid(row=1, column=0, sticky="w")
        e2.grid(row=1, column=1, sticky="w", padx=(12, 0))
        for e in (e1, e2):
            e.bind("<FocusOut>", lambda _e: self._baslik_kaydet())

    def _baslik_kaydet(self):
        self.proje.okul_adi = self.okul_var.get().strip()
        self.proje.takvim_basligi = self.baslik_var.get().strip()
        self._degisti()

    def yenile_takvim(self):
        self.okul_var.set(self.proje.okul_adi)
        self.baslik_var.set(self.proje.takvim_basligi)
        self.tv_takvim.delete(*self.tv_takvim.get_children())
        sirali = sorted(range(len(self.proje.sinavlar)), key=lambda i: (
            self.proje.sinavlar[i]["tarih"], int(re.search(r"\d+", self.proje.sinavlar[i]["oturum"])[0]),
            okuma.seviye_sirala_anahtari(self.proje.sinavlar[i]["seviye"])))
        for i in sirali:
            s = self.proje.sinavlar[i]
            liste = f"{len(s['ogrenci_nolari'])} öğrenci" if s.get("ogrenci_nolari") else ""
            self.tv_takvim.insert("", "end", iid=str(i), values=(
                tarih_yaz(s["tarih"]), s["oturum"], seviye_adi(s["seviye"]), s["ders"], liste))

    def _sinav_degisti(self, oturum_anahtarlari):
        """Değişen oturumların eski karması ve ders seçimleri geçersizdir."""
        for k in oturum_anahtarlari:
            self.proje.dagitimlar.pop(k, None)
            for a in [a for a in self.proje.ayni_ders if a.startswith(k + "|")]:
                del self.proje.ayni_ders[a]
        self._degisti()
        self.yenile_hepsi()

    def takvim_yukle(self):
        yol = filedialog.askopenfilename(title="Sınav takvimi",
                                         filetypes=[("Takvim", "*.pdf *.xls *.xlsx"), ("Tümü", "*.*")])
        if not yol:
            return
        try:
            baslik, sinavlar = okuma.takvim_oku(yol)
        except Exception as e:
            messagebox.showerror("Okunamadı", f"Takvim okunamadı:\n{e}")
            return
        if not sinavlar:
            messagebox.showwarning("Sınav bulunamadı", "Takvimde sınav bulunamadı. Tablo biçimi farklı olabilir; "
                                                       "sınavları 'Sınav ekle' ile elle girebilirsiniz.")
            return
        if (self.proje.dagitimlar or self.proje.haric) and not messagebox.askyesno(
                "Yeni takvim", "Yeni takvim yüklenince eski karmalar, ders seçimleri ve kelebek dışı sınıf "
                               "seçimleri silinecek. Devam edilsin mi?"):
            return
        okul = self.proje.okul_adi
        self.proje.takvimi_degistir(sinavlar, " ".join(baslik[1:]) if len(baslik) > 1 else " ".join(baslik))
        if baslik and not okul:
            self.proje.okul_adi = baslik[0]
        self._degisti()
        self.yenile_hepsi()
        self.durum.set(f"Takvim yüklendi: {len(sinavlar)} sınav, {len(self.proje.oturumlar())} oturum.")

    def _secili_sinavlar(self):
        return [int(i) for i in self.tv_takvim.selection()]

    def _oturum_of(self, s):
        return cekirdek.oturum_anahtari(s["tarih"], s["oturum"])

    def ders_duzenle(self):
        secili = self._secili_sinavlar()
        if not secili:
            messagebox.showinfo("Seçim yok", "Önce bir sınav satırı seçin.")
            return
        s = self.proje.sinavlar[secili[0]]
        yeni = simpledialog.askstring("Ders adı", f"{seviye_adi(s['seviye'])} · {tarih_yaz(s['tarih'])} "
                                                  f"{s['oturum']}\nDers adı:", initialvalue=s["ders"], parent=self)
        if yeni and yeni.strip():
            for i in secili:
                self.proje.sinavlar[i]["ders"] = yeni.strip()
            self._sinav_degisti({self._oturum_of(self.proje.sinavlar[i]) for i in secili})

    def sinav_ekle(self):
        tarih = simpledialog.askstring("Tarih", "Tarih (GG.AA.YYYY):", parent=self)
        if not tarih:
            return
        m = re.fullmatch(r"\s*(\d{1,2})[./](\d{1,2})[./](\d{4})\s*", tarih)
        if not m:
            messagebox.showerror("Hata", "Tarihi 02.11.2026 gibi yazın.")
            return
        iso = f"{int(m[3]):04d}-{int(m[2]):02d}-{int(m[1]):02d}"
        saat = simpledialog.askstring("Saat", "Ders saati (örn. 2 veya 6):", parent=self)
        sev = simpledialog.askstring("Seviye", "Seviye (Hazırlık, 9, 10, 11, 12):", parent=self)
        ders = simpledialog.askstring("Ders", "Ders adı:", parent=self)
        if not (saat and sev and ders):
            return
        sev = okuma.seviye_bul(sev + (". sınıf" if sev.strip().isdigit() else "")) or sev.strip()
        saat_no = int(re.search(r"\d+", saat)[0])
        oturum = f"{saat_no}. Saat"
        self.proje.sinavlar.append({"tarih": iso, "oturum": oturum, "seviye": sev,
                                    "ders": ders.strip(), "ogrenci_nolari": None})
        self._sinav_degisti({cekirdek.oturum_anahtari(iso, oturum)})

    def sinav_sil(self):
        secili = self._secili_sinavlar()
        if not secili or not messagebox.askyesno("Sil", f"{len(secili)} sınav silinsin mi?"):
            return
        etkilenen = {self._oturum_of(self.proje.sinavlar[i]) for i in secili}
        self.proje.sinavlar = [s for i, s in enumerate(self.proje.sinavlar) if i not in set(secili)]
        self._sinav_degisti(etkilenen)

    def secmeli_liste(self):
        """Seçili sınav için öğrenci numarası listesi ekler; liste varsa kaldırmayı önerir."""
        secili = self._secili_sinavlar()
        if len(secili) != 1:
            messagebox.showinfo("Seçim", "Tek bir sınav satırı seçin.")
            return
        s = self.proje.sinavlar[secili[0]]
        if s.get("ogrenci_nolari"):
            if messagebox.askyesno("Öğrenci listesi", f"Bu sınavda {len(s['ogrenci_nolari'])} öğrencilik liste var. "
                                                      "Kaldırılsın mı? (Seviyenin tamamı sınava girer.)"):
                s["ogrenci_nolari"] = None
                self._sinav_degisti({self._oturum_of(s)})
            return
        yol = filedialog.askopenfilename(title="Sınava girecek öğrenci numaraları",
                                         filetypes=[("Liste", "*.xls *.xlsx *.csv *.txt"), ("Tümü", "*.*")])
        if not yol:
            return
        try:
            nolar = okuma.ogrenci_no_listesi_oku(yol)
        except Exception as e:
            messagebox.showerror("Okunamadı", str(e))
            return
        bilinen = {no for no, (a, _) in self.proje.ogrenci_tablosu().items()
                   if self.proje.siniflar[a]["seviye"] == s["seviye"]}
        gecerli = [n for n in nolar if n in bilinen]
        s["ogrenci_nolari"] = gecerli
        self._sinav_degisti({self._oturum_of(s)})
        if len(nolar) - len(gecerli):
            messagebox.showwarning("Uyarı", f"{len(nolar) - len(gecerli)} numara bu seviyedeki öğrenciler arasında "
                                            f"bulunamadı ve atlandı. {len(gecerli)} öğrenci yüklendi.")

    # ------------------------------------------------------------------ sayfa 3: karma
    def _sayfa_karma(self):
        f = self._sayfa("karma", "Karma", "Oturum seçip karıştırın. Her oturumda yalnızca sınavı olan "
                                          "seviyelerin salonları kullanılır.")
        c = self._arac_cubugu(f)
        self._dugme(c, "Seçilenleri karıştır", lambda: self.karistir(False), True)
        self._dugme(c, "Tümünü karıştır", lambda: self.karistir(True))
        self._dugme(c, "Kelebek dışı sınıflar", self.haric_sec)
        self._dugme(c, "Karmayı sil", self.karma_sil)
        self.tv_karma = self._tablo(f, [("tarih", "Tarih", 190, "w"), ("saat", "Saat", 70, "w"),
                                        ("dersler", "Sınavlar", 360, "w"), ("dis", "Kelebek dışı", 110, "w"),
                                        ("salon", "Salon", 60, "center"), ("ogr", "Öğrenci", 70, "center"),
                                        ("durum", "Durum", 130, "w")], yukseklik=10)
        self.log = tk.Text(f, height=6, wrap="word", bg=KART, fg=SOLUK, relief="flat", bd=0, padx=10, pady=8,
                           font=(self.aile, 9))
        self.log.pack(fill="x", padx=28, pady=(0, 8))

    def yaz(self, metin):
        self.log.insert("end", metin + "\n")
        self.log.see("end")
        self.update_idletasks()

    @staticmethod
    def _ders_ozeti(sinavlar):
        return " · ".join(f"{'Haz' if s['seviye'] == 'Hazırlık' else s['seviye']}: {s['ders']}" for s in sinavlar)

    def yenile_karma(self):
        self.tv_karma.delete(*self.tv_karma.get_children())
        for k, sinavlar in self.proje.oturumlar().items():
            tarih, saat = k.split("|")
            plan = self.proje.oturum_plani(k)
            ozet = self._ders_ozeti(sinavlar)
            dis = ", ".join(kisa_ad(a) for a in self.proje.haric.get(k, []) if a in self.proje.siniflar)
            if k in self.proje.dagitimlar:
                sorun = len(self.proje.dogrula(k))
                durum = "✓ Karıldı" if not sorun else f"✓ Karıldı · {sorun} uyarı"
            else:
                durum = "—"
            self.tv_karma.insert("", "end", iid=k, values=(
                tarih_yaz(tarih), saat, ozet, dis or "—", len(plan["salonlar"]), len(plan["ogrenciler"]), durum))

    def haric_sec(self):
        """Seçili oturumlar için kelebek sistemine dahil edilmeyecek sınıfları seçtirir."""
        hedef = sorted(self.tv_karma.selection(), key=cekirdek.oturum_sirasi)
        if not self.proje.siniflar or not hedef:
            messagebox.showinfo("Seçim yok", "Önce tabloda bir veya daha fazla oturum seçin.")
            return
        oturumlar = self.proje.oturumlar()
        seviyeler = {s["seviye"] for k in hedef for s in oturumlar[k]}
        p = self._pencere("Kelebek dışı sınıflar")
        ttk.Label(p, text="Kelebek dışı sınıflar", font=(self.aile, 13, "bold")).pack(anchor="w", padx=24, pady=(18, 0))
        if len(hedef) == 1:
            t, s = hedef[0].split("|")
            kapsam = f"{tarih_yaz(t)} · {s}"
        else:
            kapsam = f"Seçili {len(hedef)} oturum"
        ttk.Label(p, text=f"{kapsam}\nİşaretlenen sınıflar karıştırılmaz ve salonları kullanılmaz.",
                  style="Soluk.TLabel", justify="left").pack(anchor="w", padx=24, pady=(2, 10))
        kutu = ttk.Frame(p)
        kutu.pack(padx=24)
        ilk = set(self.proje.haric.get(hedef[0], []))
        degiskenler = {}
        for c, sev in enumerate(sorted(seviyeler, key=okuma.seviye_sirala_anahtari)):
            cf = ttk.Frame(kutu)
            cf.grid(row=0, column=c, padx=14, sticky="n")
            ttk.Label(cf, text=seviye_adi(sev), font=(self.aile, 10, "bold")).pack(anchor="w", pady=(0, 4))
            for s in self.proje.sinif_sirali():
                if s["seviye"] == sev:
                    v = tk.BooleanVar(value=s["anahtar"] in ilk)
                    degiskenler[s["anahtar"]] = v
                    ttk.Checkbutton(cf, text=f"{s['sube']} şubesi", variable=v).pack(anchor="w", pady=1)
        tumu = tk.BooleanVar(value=False)
        if len(hedef) < len(oturumlar):
            ttk.Checkbutton(p, text="Bu seçimi takvimdeki tüm oturumlara uygula", variable=tumu).pack(
                anchor="w", padx=24, pady=(12, 0))

        def tamam():
            secilen = [a for a, v in degiskenler.items() if v.get()]
            hedefler = list(oturumlar) if tumu.get() else hedef
            yeni = sorted(secilen)
            etkilenen = [k for k in hedefler if k in self.proje.dagitimlar
                         and sorted(self.proje.haric.get(k, [])) != yeni]
            if etkilenen and not messagebox.askyesno(
                    "Mevcut karma", f"{len(etkilenen)} oturumun mevcut karması silinecek ve yeniden karılması "
                                    "gerekecek. Devam edilsin mi?"):
                return
            self.proje.haric_ayarla(hedefler, secilen)
            self._degisti()
            p.destroy()
            self.yenile_hepsi()

        alt = ttk.Frame(p)
        alt.pack(pady=18)
        ttk.Button(alt, text="Uygula", style="Vurgu.TButton", command=tamam).pack(side="left", padx=4)
        ttk.Button(alt, text="Vazgeç", command=p.destroy).pack(side="left", padx=4)

    def ayni_ders_sor(self, oturumlar):
        """Aynı dersin birden fazla seviyede yapıldığı uygun oturumlar için kullanıcıya sorar."""
        sorular = self.proje.ayni_ders_sorulari(oturumlar)
        for q in [q for q in sorular if not q["uygulanabilir"]]:
            t, s = q["oturum"].split("|")
            self.yaz(f"Bilgi: {tarih_yaz(t)} {s} · {q['ders']} öğrencilerin %{q['oran']*100:.0f}'ini kapsıyor; "
                     f"derse göre ayırmak mümkün değil, yalnız aynı seviye ayrılacak.")
        uygun = [q for q in sorular if q["uygulanabilir"]]
        if not uygun:
            return True
        p = self._pencere("Aynı ders, farklı seviyeler")
        p.grab_set()
        ttk.Label(p, text="Aynı ders birden fazla seviyede yapılıyor", font=(self.aile, 13, "bold")).pack(
            anchor="w", padx=24, pady=(18, 0))
        ttk.Label(p, text="Bu seviyelerin öğrencileri yan yana oturabilsin mi?", style="Soluk.TLabel").pack(
            anchor="w", padx=24, pady=(2, 10))
        secenekler = ["Yan yana oturabilir", "Oturmasın (derse göre ayır)"]
        kutu = ttk.Frame(p)
        kutu.pack(padx=24)
        degiskenler = []
        for r, q in enumerate(uygun):
            t, s = q["oturum"].split("|")
            ttk.Label(kutu, text=f"{tarih_yaz(t)} · {s}\n{q['ders']} ({', '.join(seviye_adi(x) for x in q['seviyeler'])})",
                      justify="left").grid(row=r, column=0, sticky="w", pady=6)
            v = tk.StringVar(value=secenekler[1 if self.proje.ayni_ders.get(f"{q['oturum']}|{q['ders']}") == "ayri" else 0])
            ttk.Combobox(kutu, textvariable=v, values=secenekler, state="readonly", width=26).grid(row=r, column=1, padx=14)
            degiskenler.append(v)
        sonuc = {"tamam": False}

        def hepsi(i):
            for v in degiskenler:
                v.set(secenekler[i])

        def tamam():
            for q, v in zip(uygun, degiskenler):
                self.proje.ayni_ders[f"{q['oturum']}|{q['ders']}"] = "ayri" if v.get() == secenekler[1] else "serbest"
            sonuc["tamam"] = True
            p.destroy()

        alt = ttk.Frame(p)
        alt.pack(pady=18)
        ttk.Button(alt, text="Hepsi yan yana", command=lambda: hepsi(0)).pack(side="left", padx=4)
        ttk.Button(alt, text="Hepsi ayrı", command=lambda: hepsi(1)).pack(side="left", padx=4)
        ttk.Button(alt, text="Tamam", style="Vurgu.TButton", command=tamam).pack(side="left", padx=(16, 4))
        ttk.Button(alt, text="Vazgeç", command=p.destroy).pack(side="left", padx=4)
        self.wait_window(p)
        return sonuc["tamam"]

    def karistir(self, hepsi):
        oturumlar = list(self.proje.oturumlar()) if hepsi else sorted(self.tv_karma.selection(),
                                                                       key=cekirdek.oturum_sirasi)
        if not self.proje.siniflar or not self.proje.sinavlar:
            messagebox.showinfo("Eksik veri", "Önce sınıf listelerini ve sınav takvimini yükleyin.")
            return
        if not oturumlar:
            messagebox.showinfo("Seçim yok", "Tabloda karıştırılacak oturumları seçin ya da 'Tümünü karıştır'ı kullanın.")
            return
        self.log.delete("1.0", "end")
        if not self.ayni_ders_sor(oturumlar):
            return
        for k in oturumlar:
            try:
                uyarilar = cekirdek.oturumu_karistir(self.proje, k)
            except ValueError as e:
                self.yaz(f"HATA {k}: {e}")
                continue
            tarih, saat = k.split("|")
            d = self.proje.dagitimlar.get(k)
            n = sum(1 for ks in d["yerlesim"].values() for x in ks if x) if d else 0
            self.yaz(f"✓ {tarih_yaz(tarih)} {saat}: {n} öğrenci, {len(d['yerlesim']) if d else 0} salon")
            for u in uyarilar:
                self.yaz(f"    ! {u}")
        self._degisti()
        self.yenile_karma()
        self.yenile_yerlesim_oturumlar()
        self.yenile_rapor()
        self.durum.set("Karma tamamlandı.")

    def karma_sil(self):
        secili = list(self.tv_karma.selection())
        for k in secili:
            self.proje.dagitimlar.pop(k, None)
        if secili:
            self._degisti()
            self.yenile_hepsi()

    # ------------------------------------------------------------------ sayfa 4: yerleşim
    def _sayfa_yerlesim(self):
        f = self._sayfa("yerlesim", "Yerleşim", "Karma sonucunu inceleyin; gerekirse iki öğrencinin yerini değiştirin.")
        c = self._arac_cubugu(f)
        self.elle_oturum, self.elle_salon, self.ara_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.cb_oturum = ttk.Combobox(c, textvariable=self.elle_oturum, state="readonly", width=30)
        self.cb_oturum.pack(side="left", padx=(0, 8))
        self.cb_oturum.bind("<<ComboboxSelected>>", lambda _e: self.yerlesim_oturum_degisti())
        self.cb_salon = ttk.Combobox(c, textvariable=self.elle_salon, state="readonly", width=16)
        self.cb_salon.pack(side="left", padx=(0, 8))
        self.cb_salon.bind("<<ComboboxSelected>>", lambda _e: self.yenile_yerlesim_tablo())
        ttk.Entry(c, textvariable=self.ara_var, width=18).pack(side="right")
        ttk.Button(c, text="Öğrenci bul", command=self.elle_bul).pack(side="right", padx=8)
        c2 = self._arac_cubugu(f)
        self._dugme(c2, "1 · Sırayı işaretle", self.elle_isaretle)
        self._dugme(c2, "2 · İşaretliyle yer değiştir", self.elle_degistir, True)
        self._dugme(c2, "Geri al", self.elle_geri_al)
        self.isaret_var = tk.StringVar()
        ttk.Label(c2, textvariable=self.isaret_var, style="Soluk.TLabel").pack(side="left", padx=8)
        self.tv_elle = self._tablo(f, [("sira", "Sıra", 60, "center"), ("no", "Okul no", 90, "center"),
                                       ("ad", "Adı soyadı", 280, "w"), ("sinif", "Sınıfı", 140, "w"),
                                       ("uyari", "Uyarı", 380, "w")], secim="browse")
        ttk.Label(f, style="Soluk.TLabel", text="Kırmızı satırlar kuralı bozan yerlerdir. Kural bozan değişiklik "
                                               "yapmadan önce uyarılırsınız.").pack(anchor="w", padx=28, pady=(0, 6))

    def yenile_yerlesim_oturumlar(self):
        anahtarlar = [k for k in self.proje.oturumlar() if k in self.proje.dagitimlar]
        self._elle_etiket = {f"{tarih_yaz(k.split('|')[0])} · {k.split('|')[1]}": k for k in anahtarlar}
        self.cb_oturum["values"] = list(self._elle_etiket)
        if self.elle_oturum.get() not in self._elle_etiket:
            self.elle_oturum.set(next(iter(self._elle_etiket), ""))
        self.yerlesim_oturum_degisti()

    def _elle_anahtar(self):
        return getattr(self, "_elle_etiket", {}).get(self.elle_oturum.get())

    def yerlesim_oturum_degisti(self):
        k = self._elle_anahtar()
        salonlar = list(self.proje.dagitimlar[k]["yerlesim"]) if k else []
        self._elle_salon_etiket = {self.proje.sinif_adi(s): s for s in salonlar}
        self.cb_salon["values"] = list(self._elle_salon_etiket)
        if self.elle_salon.get() not in self._elle_salon_etiket:
            self.elle_salon.set(next(iter(self._elle_salon_etiket), ""))
        self.isaretli = None
        self.isaret_var.set("" if k else "Henüz karılmış oturum yok.")
        self.yenile_yerlesim_tablo()

    # eski ad: testler ve olası dış çağrılar için
    yenile_elle_oturumlar = yenile_yerlesim_oturumlar
    elle_oturum_degisti = yerlesim_oturum_degisti

    def _elle_salon(self):
        return getattr(self, "_elle_salon_etiket", {}).get(self.elle_salon.get())

    def yenile_yerlesim_tablo(self):
        self.tv_elle.delete(*self.tv_elle.get_children())
        k, salon = self._elle_anahtar(), self._elle_salon()
        if not k or not salon:
            return
        tablo = self.proje.ogrenci_tablosu()
        sorunlar = {}
        for s in self.proje.dogrula(k):
            if s["salon"] == salon:
                sorunlar.setdefault(s["koltuk"], []).append(s["mesaj"])
                if s.get("koltuk2") is not None:
                    sorunlar.setdefault(s["koltuk2"], []).append(s["mesaj"])
        for i, no in enumerate(self.proje.dagitimlar[k]["yerlesim"][salon]):
            if no:
                sinif_a, o = tablo[no]
                ad, sinif = f"{o['ad']} {o['soyad']}", self.proje.sinif_adi(sinif_a)
            else:
                ad, sinif = "(boş sıra)", ""
            etiketler = []
            if i in sorunlar:
                etiketler.append("hata")
            if self.isaretli == (salon, i):
                etiketler.append("isaret")
            if not no:
                etiketler.append("soluk")
            self.tv_elle.insert("", "end", iid=str(i), tags=tuple(etiketler), values=(
                i + 1, no or "", ad, sinif, " | ".join(sorunlar.get(i, []))))

    yenile_elle_tablo = yenile_yerlesim_tablo

    def _secili_koltuk(self):
        s = self.tv_elle.selection()
        return int(s[0]) if s else None

    def elle_isaretle(self):
        i = self._secili_koltuk()
        if i is None:
            messagebox.showinfo("Seçim yok", "Tabloda bir sıra seçin.")
            return
        self.isaretli = (self._elle_salon(), i)
        self.isaret_var.set(f"İşaretli: {self.elle_salon.get()} · {i+1}. sıra. Şimdi değiştireceğiniz sırayı "
                            "seçin (başka salona da geçebilirsiniz).")
        self.yenile_yerlesim_tablo()

    def elle_degistir(self):
        k = self._elle_anahtar()
        i = self._secili_koltuk()
        if not k or not self.isaretli or i is None:
            messagebox.showinfo("Eksik seçim", "Önce bir sırayı işaretleyin, sonra ikinci sırayı seçin.")
            return
        s1, k1 = self.isaretli
        s2, k2 = self._elle_salon(), i
        if (s1, k1) == (s2, k2):
            return
        onceki = cekirdek.dagitim_kopyasi(self.proje, k)
        once_sayi = len(self.proje.dogrula(k))
        cekirdek.yer_degistir(self.proje, k, s1, k1, s2, k2)
        yeni = self.proje.dogrula(k)
        if len(yeni) > once_sayi:
            ek = [s["mesaj"] for s in yeni][:6]
            if not messagebox.askyesno("Kural ihlali", "Bu değişiklik kuralları bozuyor:\n\n" + "\n".join(ek)
                                       + "\n\nYine de uygulansın mı?"):
                self.proje.dagitimlar[k] = onceki
                return
        self.geri_al_yigini.append((k, onceki))
        self.isaretli = None
        self.isaret_var.set("Yer değiştirildi.")
        self._degisti()
        self.yenile_yerlesim_tablo()
        self.yenile_karma()

    def elle_geri_al(self):
        if not self.geri_al_yigini:
            return
        k, onceki = self.geri_al_yigini.pop()
        self.proje.dagitimlar[k] = onceki
        self._degisti()
        self.yenile_yerlesim_tablo()
        self.yenile_karma()

    def elle_bul(self):
        k = self._elle_anahtar()
        aranan = okuma.tr_kucuk(self.ara_var.get().strip())
        if not k or not aranan:
            return
        tablo = self.proje.ogrenci_tablosu()
        for salon, koltuklar in self.proje.dagitimlar[k]["yerlesim"].items():
            for i, no in enumerate(koltuklar):
                if no:
                    o = tablo[no][1]
                    if aranan == no or aranan in okuma.tr_kucuk(f"{o['ad']} {o['soyad']}"):
                        self.elle_salon.set(self.proje.sinif_adi(salon))
                        self.yenile_yerlesim_tablo()
                        self.tv_elle.selection_set(str(i))
                        self.tv_elle.see(str(i))
                        return
        messagebox.showinfo("Bulunamadı", "Öğrenci bu oturumda bulunamadı.")

    # ------------------------------------------------------------------ sayfa 5: rapor
    def _sayfa_rapor(self):
        f = self._sayfa("rapor", "Raporlar", "Seçtiğiniz oturumlar için PDF listeleri oluşturun.")
        govde = ttk.Frame(f)
        govde.pack(fill="both", expand=True, padx=28)
        sol = ttk.Frame(govde)
        sol.pack(side="left", fill="both", expand=True)
        ttk.Label(sol, text="Oturumlar (Ctrl/Shift ile çoklu seçim)", style="Soluk.TLabel").pack(anchor="w", pady=(0, 4))
        cerceve = ttk.Frame(sol)
        cerceve.pack(fill="both", expand=True)
        self.lb_rapor = tk.Listbox(cerceve, selectmode="extended", bg=KART, relief="flat", bd=0,
                                   highlightthickness=0, activestyle="none", selectbackground=VURGU_ACIK,
                                   selectforeground=YAZI, font=(self.aile, 10))
        sb = ttk.Scrollbar(cerceve, orient="vertical", command=self.lb_rapor.yview)
        self.lb_rapor.configure(yscrollcommand=sb.set)
        self.lb_rapor.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        sag = ttk.Frame(govde)
        sag.pack(side="left", fill="y", padx=(24, 0))
        self.r_liste1, self.r_liste2, self.r_ayri = tk.BooleanVar(value=True), tk.BooleanVar(value=True), tk.BooleanVar(value=True)
        ttk.Label(sag, text="Listeler", style="Soluk.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Checkbutton(sag, text="Liste 1 · Öğrenci bazlı\n(hangi salonda, kaçıncı sırada)", variable=self.r_liste1).pack(anchor="w", pady=3)
        ttk.Checkbutton(sag, text="Liste 2 · Salon bazlı\n(öğrenciler + seviye özeti)", variable=self.r_liste2).pack(anchor="w", pady=3)
        ttk.Checkbutton(sag, text="Her oturum ayrı PDF olsun", variable=self.r_ayri).pack(anchor="w", pady=(10, 3))
        ttk.Label(sag, text="Kayıt klasörü", style="Soluk.TLabel").pack(anchor="w", pady=(16, 4))
        self.r_klasor = tk.StringVar(value=VARSAYILAN_RAPOR_KLASORU)
        ttk.Entry(sag, textvariable=self.r_klasor, width=34).pack(anchor="w")
        ttk.Button(sag, text="Klasör seç", command=self.rapor_klasor_sec).pack(anchor="w", pady=6)
        ttk.Button(sag, text="PDF oluştur", style="Vurgu.TButton", command=self.rapor_olustur).pack(anchor="w", pady=(16, 0))
        self.r_sonuc = tk.StringVar()
        ttk.Label(f, textvariable=self.r_sonuc, style="Soluk.TLabel").pack(anchor="w", padx=28, pady=8)

    def yenile_rapor(self):
        self.lb_rapor.delete(0, "end")
        self._rapor_anahtarlari = []
        for k, sinavlar in self.proje.oturumlar().items():
            if k in self.proje.dagitimlar:
                self._rapor_anahtarlari.append(k)
                self.lb_rapor.insert("end", f"  {tarih_yaz(k.split('|')[0])} · {k.split('|')[1]}   —   "
                                            f"{self._ders_ozeti(sinavlar)}")

    def rapor_klasor_sec(self):
        y = filedialog.askdirectory()
        if y:
            self.r_klasor.set(y)

    def rapor_olustur(self):
        secili = [self._rapor_anahtarlari[i] for i in self.lb_rapor.curselection()]
        if not secili:
            messagebox.showinfo("Seçim yok", "Listeden en az bir oturum seçin.")
            return
        if not (self.r_liste1.get() or self.r_liste2.get()):
            messagebox.showinfo("Seçim yok", "En az bir liste türü seçin.")
            return
        kirli = [k for k in secili if any(s["tur"] in ("eksik", "cift") for s in self.proje.dogrula(k))]
        if kirli and not messagebox.askyesno(
                "Eksik yerleşim", "Bazı oturumlarda yerleştirilmemiş ya da çift yerleştirilmiş öğrenci var. "
                                  "Yine de rapor üretilsin mi?"):
            return
        try:
            dosyalar = rapor.raporlari_olustur(self.proje, secili, self.r_klasor.get(), self.r_liste1.get(),
                                               self.r_liste2.get(), self.r_ayri.get())
        except Exception as e:
            messagebox.showerror("Hata", f"PDF oluşturulamadı:\n{e}")
            return
        self.r_sonuc.set(f"{len(dosyalar)} PDF oluşturuldu: {self.r_klasor.get()}")
        self.durum.set("PDF raporları hazır.")
        if messagebox.askyesno("Tamam", f"{len(dosyalar)} PDF oluşturuldu. Klasör açılsın mı?"):
            _klasoru_ac(self.r_klasor.get())


def calistir():
    Uygulama().mainloop()
