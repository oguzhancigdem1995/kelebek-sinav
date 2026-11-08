"""Gerçek ekran olmadan arayüz mantığını dener: sahte tkinter ile tüm düğme işlevlerini çağırır."""
import sys, types, glob, os, tempfile

class Sahte:
    def __init__(self, *a, **k): self._cocuklar = []; self._secim = ()
    def __getattr__(self, ad):
        if ad.startswith('_'): raise AttributeError(ad)
        return lambda *a, **k: Sahte()
    def get_children(self, *a): return list(getattr(self, '_ogeler', {}).keys())
    def insert(self, parent, idx, iid=None, **k):
        if not hasattr(self, '_ogeler'): self._ogeler = {}
        self._ogeler[iid or str(len(self._ogeler))] = k.get('values')
    def delete(self, *a):
        if hasattr(self, '_ogeler'): self._ogeler = {}
    def selection(self): return self._secim
    def curselection(self): return self._secim
    def __setitem__(self, k, v): pass
    def __getitem__(self, k): return ()
    def pack(self, *a, **k): return None
    def grid(self, *a, **k): return None
class Degisken:
    def __init__(self, master=None, value=None): self.v = value
    def get(self): return self.v
    def set(self, v): self.v = v
tk = types.ModuleType('tkinter'); ttk = types.ModuleType('tkinter.ttk')
tk.TclError = type('TclError',(Exception,),{})
for ad in ['Tk','Toplevel','Menu','Text','Listbox','Frame','Label','Button','Canvas']: setattr(tk, ad, type(ad, (Sahte,), {}))
for ad in ['StringVar','IntVar','BooleanVar']: setattr(tk, ad, type(ad, (Degisken,), {}))
for ad in ['Frame','Label','Button','Entry','Checkbutton','Radiobutton','Combobox','Spinbox','Notebook','Treeview','Scrollbar','LabelFrame','Style']:
    setattr(ttk, ad, type(ad, (Sahte,), {}))
cagrilar = []
mb = types.ModuleType('tkinter.messagebox')
for ad, d in [('showinfo',None),('showwarning',None),('showerror',None),('askyesno',True)]:
    setattr(mb, ad, (lambda ad,d: lambda *a, **k: (cagrilar.append((ad, a)), d)[1])(ad,d))
fo = types.ModuleType('tkinter.font'); fo.families = lambda *a, **k: []; fo.nametofont = lambda *a, **k: Sahte()
fd = types.ModuleType('tkinter.filedialog'); sd = types.ModuleType('tkinter.simpledialog')
tk.font = fo; tk.ttk, tk.messagebox, tk.filedialog, tk.simpledialog = ttk, mb, fd, sd
for ad, m in [('tkinter',tk),('tkinter.ttk',ttk),('tkinter.messagebox',mb),('tkinter.font',fo),('tkinter.filedialog',fd),('tkinter.simpledialog',sd)]:
    sys.modules[ad] = m
tk.filedialog = fd; tk.simpledialog = sd

xls, pdf, cikti = sys.argv[1], sys.argv[2], sys.argv[3]
from kelebek import arayuz
fd.askopenfilenames = lambda **k: [xls]
fd.askopenfilename = lambda **k: pdf
fd.asksaveasfilename = lambda **k: os.path.join(cikti, 'test.kelebek')
fd.askdirectory = lambda **k: cikti
a = arayuz.Uygulama()
a.sinif_yukle(); assert len(a.proje.siniflar) == 15
a.takvim_yukle(); assert len(a.proje.oturumlar()) == 16
a.tv_sinif._secim = ('9-A', '9-B'); a.salon_ayarla()
k0 = list(a.proje.oturumlar())[0]
a.tv_karma._secim = (k0,); a.haric_sec()  # pencere kurulumu hatasız çalışmalı
a.proje.haric_ayarla([k0], ['12-C'])
a.tv_karma._secim = ()
a.ayni_ders_sor(list(a.proje.oturumlar()))  # pencere kurulumu hatasız çalışmalı
a.ayni_ders_sor = lambda o: True
a.karistir(True)
assert len(a.proje.dagitimlar) == 16, len(a.proje.dagitimlar)
k = list(a.proje.dagitimlar)[0]
a.cb_oturum.set = lambda v: None
a.elle_oturum.set(next(iter(a._elle_etiket))); a.elle_oturum_degisti()
a.tv_elle._secim = ('0',); a.elle_isaretle(); a.tv_elle._secim = ('5',); a.elle_degistir(); a.elle_geri_al()
a.ara_var.set('AHMET'); a.elle_bul()
a.proje_kaydet(); a.proje_ac()
a.lb_rapor._secim = (0, 1); a.r_klasor.set(os.path.join(cikti, 'pdf')); a.rapor_olustur()
print('PDF sayısı:', len(glob.glob(os.path.join(cikti, 'pdf', '*.pdf'))))
print('hata/uyarı mesajları:', [c for c in cagrilar if c[0] in ('showerror',)])
print('DUMAN TESTİ BAŞARILI')
