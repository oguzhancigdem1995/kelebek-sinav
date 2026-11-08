"use strict";
/* Kelebek – web arayüzü. Python tarafı window.pywebview.api üzerinden çağrılır. */
const S = { d: null, sayfa: "karma", hafta: 0, secili: null, sonuc: {}, yer: { oturum: null, salon: null, sec: null, bulunan: null, veri: null }, rapor: new Set(), sinifSec: new Set(), takvimSec: new Set() };
const HATALAR = [];
window.addEventListener("error", e => HATALAR.push(String(e.message)));
window.addEventListener("unhandledrejection", e => HATALAR.push(String(e.reason)));

const $ = (s, k = document) => k.querySelector(s);
const $$ = (s, k = document) => [...k.querySelectorAll(s)];
const h = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const vk = sev => sev === "Hazırlık" ? "0" : String(sev);
const nokta = sev => `<i class="dot v${vk(sev)}" title="${h(sev === "Hazırlık" ? "Hazırlık" : sev + ". Sınıf")}"></i>`;
const sevAd = sev => sev === "Hazırlık" ? "Hazırlık" : sev + ". Sınıf";

function toast(m, tur) {
  const t = document.createElement("div");
  t.className = "toast" + (tur === "hata" ? " hata" : "");
  t.textContent = m;
  $("#toast-kap").appendChild(t);
  setTimeout(() => t.remove(), tur === "hata" ? 7000 : 3500);
}

async function api(ad, ...a) {
  if (!window.pywebview || !window.pywebview.api) throw new Error("Uygulama motoru hazır değil.");
  const r = await window.pywebview.api[ad](...a);
  if (!r || !r.ok) { toast((r && r.hata) || "Beklenmeyen hata", "hata"); throw new Error((r && r.hata) || "hata"); }
  if (r.durum) S.d = r.durum;
  return r;
}
async function dene(f) { try { return await f(); } catch (e) { return null; } }

function modal(html, dugmeler) {
  return new Promise(coz => {
    const kap = $("#modal-kap");
    kap.innerHTML = `<div class="modal">${html}<div class="alt"></div></div>`;
    const alt = $(".alt", kap);
    dugmeler.forEach(d => {
      const b = document.createElement("button");
      b.className = "btn " + (d.sinif === undefined ? "g" : d.sinif);
      b.textContent = d.ad;
      b.onclick = () => { const v = d.deger === undefined ? d.ad : d.deger; const sonuc = d.al ? d.al(kap) : v; kap.hidden = true; kap.innerHTML = ""; coz(sonuc); };
      alt.appendChild(b);
    });
    kap.hidden = false;
  });
}
const onayla = (baslik, metin, evet = "Evet") => modal(`<h3>${h(baslik)}</h3><p class="s">${metin}</p>`, [{ ad: "Vazgeç", deger: false }, { ad: evet, sinif: "", deger: true }]);

/* ------------------------------------------------------------------ gezinme */
function git(sayfa) {
  S.sayfa = sayfa;
  $$("#menu button").forEach(b => b.classList.toggle("on", b.dataset.sayfa === sayfa));
  ciz();
}
function ciz() {
  const f = { kurum: cizKurum, siniflar: cizSiniflar, takvim: cizTakvim, karma: cizKarma, yerlesim: cizYerlesim, raporlar: cizRaporlar }[S.sayfa];
  const kap = $("#icerik");
  const kay = kap.scrollTop;
  f(kap);
  kap.scrollTop = kay;
}

/* ------------------------------------------------------------------ kurum */
function cizKurum(k) {
  const q = S.d.kurum;
  k.innerHTML = `
  <div class="baslik-satir"><div><div class="t">Kurum bilgileri</div><div class="s">Raporların üst ve alt bilgisinde kullanılır. Farklı bir okulda kullanmak için burayı değiştirmeniz yeterli.</div></div>
    <div class="btnler"><button class="btn g" id="k-yeni">Yeni proje</button><button class="btn g" id="k-yedek">Yedek al</button><button class="btn g" id="k-ac">Yedekten aç</button></div></div>
  <div class="kurum-duzen">
    <div class="kart">
      <label class="alan"><span>Okul / kurum adı</span><input type="text" id="k-okul" value="${h(q.okul_adi)}"></label>
      <label class="alan"><span>Alt başlık (ör. şehir, ilçe, eğitim-öğretim yılı)</span><input type="text" id="k-alt" value="${h(q.alt_baslik)}"></label>
      <label class="alan"><span>Sınav başlığı</span><input type="text" id="k-baslik" value="${h(q.sinav_basligi)}"></label>
      <div class="iki">
        <label class="alan"><span>Müdür yardımcısı</span><input type="text" id="k-yrd" value="${h(q.mudur_yrd)}"></label>
        <label class="alan"><span>Okul müdürü</span><input type="text" id="k-mudur" value="${h(q.mudur)}"></label>
      </div>
      <label class="alan"><span>Raporların kaydedileceği klasör</span>
        <div class="btnler"><input type="text" id="k-klasor" value="${h(q.rapor_klasoru)}" style="flex:1"><button class="btn g" id="k-klasor-sec">Seç…</button></div></label>
      <button class="btn" id="k-kaydet">Kaydet</button>
    </div>
    <div class="kart">
      <div class="bolum" style="margin-top:0">Logo</div>
      <div class="logo-kutu">${q.logo ? `<img src="${q.logo}" alt="logo">` : "Logo eklenmedi"}</div>
      <div class="btnler"><button class="btn g" id="k-logo">Logo seç…</button>${q.logo ? `<button class="btn k" id="k-logo-sil">Kaldır</button>` : ""}</div>
      <p class="s" style="margin-top:12px">Logo raporların sağ üst köşesinde görünür. PNG veya JPG kullanabilirsiniz.</p>
    </div>
  </div>`;
  const form = () => ({ okul_adi: $("#k-okul").value, alt_baslik: $("#k-alt").value, sinav_basligi: $("#k-baslik").value, mudur_yrd: $("#k-yrd").value, mudur: $("#k-mudur").value, rapor_klasoru: $("#k-klasor").value });
  $("#k-kaydet").onclick = async () => { await dene(() => api("kurum_kaydet", form())); toast("Kurum bilgileri kaydedildi."); ciz(); };
  $("#k-klasor-sec").onclick = async () => { await dene(() => api("kurum_kaydet", form())); await dene(() => api("klasor_sec")); ciz(); };
  $("#k-logo").onclick = async () => { await dene(() => api("kurum_kaydet", form())); await dene(() => api("kurum_logo_sec")); ciz(); };
  const sil = $("#k-logo-sil"); if (sil) sil.onclick = async () => { await dene(() => api("kurum_logo_kaldir")); ciz(); };
  $("#k-yedek").onclick = async () => { const r = await dene(() => api("yedek_al")); if (r && r.yol) toast("Yedek kaydedildi."); };
  $("#k-ac").onclick = async () => { if (await onayla("Yedekten aç", "Şu anki çalışmanın yerini yedekteki proje alacak. Devam edilsin mi?")) { await dene(() => api("yedek_ac")); ciz(); } };
  $("#k-yeni").onclick = async () => {
    if (await onayla("Yeni proje", "Sınıflar, takvim ve karmalar silinir. Kurum bilgileri korunur. Devam edilsin mi?", "Yeni proje")) { await dene(() => api("yeni_proje")); S.secili = null; S.hafta = 0; ciz(); }
  };
}

/* ------------------------------------------------------------------ sınıflar */
function cizSiniflar(k) {
  const L = S.d.siniflar, toplam = L.reduce((a, s) => a + s.ogrenci, 0);
  k.innerHTML = `
  <div class="baslik-satir"><div><div class="t">Sınıflar</div><div class="s">Her sınıf bir sınav salonudur; sıra sayısı öğrenci sayısına eşittir.</div></div>
    <div class="btnler"><button class="btn g" id="s-duzen" ${S.sinifSec.size ? "" : "disabled"}>Salon düzeni (${S.sinifSec.size})</button><button class="btn" id="s-yukle">Sınıf listesi yükle</button></div></div>
  <div class="istat"><div class="kart"><b>${L.length}</b><span>Sınıf / salon</span></div><div class="kart"><b>${toplam}</b><span>Öğrenci</span></div><div class="kart"><b>${new Set(L.map(s => s.seviye)).size}</b><span>Seviye</span></div></div>
  ${L.length ? `<div class="kart"><table><thead><tr><th><input type="checkbox" id="s-hepsi"></th><th>Sınıf</th><th>Öğrenci</th><th>Sıra</th><th>Sıra türü</th><th>Yan yana kuralı</th></tr></thead><tbody>
    ${L.map(s => `<tr class="tikla ${S.sinifSec.has(s.anahtar) ? "sec" : ""}" data-a="${h(s.anahtar)}"><td><input type="checkbox" ${S.sinifSec.has(s.anahtar) ? "checked" : ""}></td><td>${nokta(s.seviye)} <b>${h(s.ad)}</b></td><td>${s.ogrenci}</td><td>${s.kapasite}${s.kapasite_ozel ? " (özel)" : ""}</td><td>${s.tur === "ikili" ? "İkili" : "Tekli"}</td><td>${s.tur === "ikili" && s.komsuluk === "masa" ? "Aynı masadakiler" : "Ardışık sıralar"}${s.sutun ? ` · ${s.sutun} sütun` : ""}</td></tr>`).join("")}
  </tbody></table></div>` : `<div class="kart bos"><b>Henüz sınıf eklenmedi</b>e-Okul'dan aldığınız sınıf listesi Excel dosyalarını yükleyin.</div>`}`;
  $("#s-yukle").onclick = async () => {
    const r = await dene(() => api("sinif_yukle"));
    if (r && r.eklenen) { toast(`${r.eklenen} sınıf yüklendi.`); if (r.uyarilar && r.uyarilar.length) await modal(`<h3>Dikkat</h3><div class="s">${r.uyarilar.map(h).join("<br>")}</div>`, [{ ad: "Tamam", sinif: "" }]); }
    ciz();
  };
  const hepsi = $("#s-hepsi"); if (hepsi) hepsi.onchange = () => { S.sinifSec = hepsi.checked ? new Set(L.map(s => s.anahtar)) : new Set(); ciz(); };
  $$("tbody tr", k).forEach(tr => tr.onclick = () => { const a = tr.dataset.a; S.sinifSec.has(a) ? S.sinifSec.delete(a) : S.sinifSec.add(a); ciz(); });
  $("#s-duzen").onclick = salonDuzeni;
}
async function salonDuzeni() {
  const sec = S.d.siniflar.filter(s => S.sinifSec.has(s.anahtar)), ilk = sec[0], tek = sec.length === 1;
  const p = modal(`<h3>Salon düzeni</h3><div class="s">${sec.length} sınıf seçili${tek ? " · " + h(ilk.ad) : ""}</div><br>
    <label class="alan"><span>Sıra türü</span><select id="m-tur"><option value="tekli">Tekli sıra</option><option value="ikili">İkili sıra</option></select></label>
    <label class="alan"><span>Yan yana kuralı</span><select id="m-kom"><option value="ardarda">Ardışık sıralar yan yana sayılır</option><option value="masa">Yalnız aynı masada oturanlar</option></select></label>
    <div class="iki"><label class="alan"><span>Sütun sayısı (ön-arka komşuluk için, 0 = yok)</span><input type="number" id="m-sutun" min="0" value="${ilk.sutun}"></label>
    ${tek ? `<label class="alan"><span>Sıra sayısı (boş = öğrenci sayısı)</span><input type="number" id="m-kap" min="0" value="${ilk.kapasite_ozel ? ilk.kapasite : ""}"></label>` : "<div></div>"}</div>
    <div class="s">Değişince bu salonların mevcut karmaları silinir.</div>`,
    [{ ad: "Vazgeç", deger: null }, { ad: "Uygula", sinif: "", al: kap => ({ tur: $("#m-tur", kap).value, kom: $("#m-kom", kap).value, sutun: $("#m-sutun", kap).value, kap: tek ? $("#m-kap", kap).value : "" }) }]);
  $("#m-tur").value = ilk.tur; $("#m-kom").value = ilk.komsuluk;
  const r = await p;
  if (!r) return;
  await dene(() => api("salon_ayarla", [...S.sinifSec], r.tur, r.kom, r.sutun, r.kap));
  ciz();
}
/* ------------------------------------------------------------------ takvim */
function cizTakvim(k) {
  const L = S.d.sinavlar;
  k.innerHTML = `
  <div class="baslik-satir"><div><div class="t">Takvim</div><div class="s">${h(S.d.kurum.sinav_basligi || "Sınav takvimini PDF ya da Excel olarak yükleyin")} · ders adına tıklayıp düzeltebilirsiniz.</div></div>
    <div class="btnler"><button class="btn g k" id="t-sil" ${S.takvimSec.size ? "" : "disabled"}>Seçilenleri sil</button><button class="btn g" id="t-ekle">Sınav ekle</button><button class="btn" id="t-yukle">Takvim yükle</button></div></div>
  ${L.length ? `<div class="kart"><table><thead><tr><th></th><th>Tarih</th><th>Saat</th><th>Seviye</th><th>Ders</th><th>Öğrenci listesi</th></tr></thead><tbody>
  ${L.map(s => `<tr data-id="${s.id}"><td><input type="checkbox" class="t-c" ${S.takvimSec.has(s.id) ? "checked" : ""}></td><td>${h(s.tarih_yazi)}</td><td>${h(s.oturum)}</td><td>${nokta(s.seviye)} ${h(s.seviye_adi)}</td><td><a href="#" class="t-ders" style="color:inherit;text-decoration:none;border-bottom:1px dashed #b6bdcc">${h(s.ders)}</a></td>
  <td>${s.liste ? `<span class="pill ok">${s.liste} öğrenci</span> <button class="btn g kucuk t-lk">Kaldır</button>` : `<button class="btn g kucuk t-ls">Liste ekle</button>`}</td></tr>`).join("")}</tbody></table></div>`
    : `<div class="kart bos"><b>Takvim yüklenmedi</b>Okulunuzun sınav takvimi PDF'ini ya da Excel dosyasını yükleyin; program tabloyu kendisi okur.</div>`}`;
  $("#t-yukle").onclick = async () => {
    if (S.d.oturumlar.some(o => o.karildi) && !(await onayla("Yeni takvim", "Yeni takvim yüklenince eski karmalar, ders seçimleri ve kelebek dışı sınıf seçimleri silinecek. Devam edilsin mi?"))) return;
    const r = await dene(() => api("takvim_yukle")); if (r && r.eklenen) { toast(`${r.eklenen} sınav yüklendi.`); S.hafta = 0; S.secili = null; S.takvimSec.clear(); } ciz();
  };
  $("#t-ekle").onclick = sinavEkle;
  $$(".t-c", k).forEach(c => c.onchange = () => { const id = +c.closest("tr").dataset.id; c.checked ? S.takvimSec.add(id) : S.takvimSec.delete(id); ciz(); });
  $("#t-sil").onclick = async () => { if (await onayla("Sınav sil", `${S.takvimSec.size} sınav silinecek.`, "Sil")) { await dene(() => api("sinav_sil", [...S.takvimSec])); S.takvimSec.clear(); ciz(); } };
  $$(".t-ders", k).forEach(a => a.onclick = async e => {
    e.preventDefault(); const id = +a.closest("tr").dataset.id, s = S.d.sinavlar.find(x => x.id === id);
    const v = await modal(`<h3>Ders adı</h3><div class="s">${h(s.tarih_yazi)} · ${h(s.oturum)} · ${h(s.seviye_adi)}</div><br><input type="text" id="m-ders" value="${h(s.ders)}">`,
      [{ ad: "Vazgeç", deger: null }, { ad: "Kaydet", sinif: "", al: kap => $("#m-ders", kap).value }]);
    if (v) { await dene(() => api("sinav_ders_degistir", id, v)); ciz(); }
  });
  $$(".t-ls", k).forEach(b => b.onclick = async () => { const id = +b.closest("tr").dataset.id; const r = await dene(() => api("secmeli_liste_sec", id)); if (r && r.yuklenen !== undefined) toast(`${r.yuklenen} öğrenci eklendi` + (r.atlanan ? `, ${r.atlanan} numara bu seviyede bulunamadı.` : ".")); ciz(); });
  $$(".t-lk", k).forEach(b => b.onclick = async () => { await dene(() => api("secmeli_liste_kaldir", +b.closest("tr").dataset.id)); ciz(); });
}
async function sinavEkle() {
  const tarihler = [...new Set(S.d.sinavlar.map(s => s.tarih))], bugun = tarihler[0] || new Date().toISOString().slice(0, 10);
  const sevler = S.d.seviyeler.length ? S.d.seviyeler : ["Hazırlık", "9", "10", "11", "12"];
  const v = await modal(`<h3>Sınav ekle</h3><br><div class="iki"><label class="alan"><span>Tarih</span><input type="date" id="e-t" value="${bugun}"></label><label class="alan"><span>Ders saati</span><input type="number" id="e-s" min="1" max="12" value="2"></label></div>
    <label class="alan"><span>Seviye</span><select id="e-v">${sevler.map(x => `<option value="${h(x)}">${h(sevAd(x))}</option>`).join("")}</select></label>
    <label class="alan"><span>Ders adı</span><input type="text" id="e-d"></label>`,
    [{ ad: "Vazgeç", deger: null }, { ad: "Ekle", sinif: "", al: kap => [$("#e-t", kap).value, $("#e-s", kap).value, $("#e-v", kap).value, $("#e-d", kap).value] }]);
  if (v) { await dene(() => api("sinav_ekle", ...v)); ciz(); }
}

/* ------------------------------------------------------------------ karma (takvim panosu) */
function haftalar() {
  const g = {};
  S.d.oturumlar.forEach(o => {
    const [y, a, d] = o.tarih.split("-").map(Number), t = new Date(Date.UTC(y, a - 1, d));
    t.setUTCDate(t.getUTCDate() - o.gun_no);
    const k = t.toISOString().slice(0, 10);
    (g[k] = g[k] || []).push(o);
  });
  return Object.keys(g).sort().map(k => ({ baslangic: k, oturumlar: g[k] }));
}
const AY = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
function haftaYazi(w) {
  const t = w.oturumlar.map(o => o.tarih).sort(), [y1, a1, d1] = t[0].split("-").map(Number), [y2, a2, d2] = t[t.length - 1].split("-").map(Number);
  return a1 === a2 ? `${d1}–${d2} ${AY[a1]}` : `${d1} ${AY[a1]} – ${d2} ${AY[a2]}`;
}
function cizKarma(k) {
  const O = S.d.oturumlar;
  if (!O.length) { k.innerHTML = `<div class="baslik-satir"><div><div class="t">Karma</div><div class="s">Önce sınıf listelerini ve takvimi yükleyin.</div></div></div><div class="kart bos"><b>Takvim yok</b>Sınıflar ve Takvim sayfalarından dosyalarınızı yükleyin.</div>`; return; }
  const H = haftalar(); S.hafta = Math.max(0, Math.min(S.hafta, H.length - 1));
  const w = H[S.hafta], gunler = [...new Set(w.oturumlar.map(o => o.gun_no))].sort(), saatler = [...new Set(w.oturumlar.map(o => o.saat_no))].sort((a, b) => a - b);
  const karildi = O.filter(o => o.karildi).length, uyari = O.reduce((a, o) => a + o.uyari, 0);
  const secOt = O.find(o => o.anahtar === S.secili);
  const hucre = (g, s) => {
    const o = w.oturumlar.find(x => x.gun_no === g && x.saat_no === s);
    if (!o) return `<div class="hucre bos"></div>`;
    const durum = !o.karildi ? `<span class="pill bekle">Bekliyor</span>` : o.uyari ? `<span class="pill uyari">${o.uyari} uyarı</span>` : `<span class="pill ok">Karıldı</span>`;
    return `<button class="hucre ${o.anahtar === S.secili ? "sec" : ""}" data-k="${h(o.anahtar)}"><b>${o.ogrenci} öğrenci</b><small>${o.salon} salon</small><span>${o.sinavlar.map(x => nokta(x.seviye)).join("")}</span>${durum}</button>`;
  };
  const gunBas = g => { const o = w.oturumlar.find(x => x.gun_no === g); return `<div class="h"><b>${h(o.gun)}</b>${h(o.tarih_yazi.split(" ").slice(0, 2).join(" "))}</div>`; };
  k.innerHTML = `
  <div class="baslik-satir"><div><div class="t">Karma</div><div class="s">Bir oturuma tıklayın; ayarlayın ve karıştırın.</div></div>
    <div class="btnler hafta-bas"><button class="ok-btn" id="h-geri" ${S.hafta === 0 ? "disabled" : ""}>‹</button><span class="hafta-ad">${h(haftaYazi(w))}</span><button class="ok-btn" id="h-ileri" ${S.hafta >= H.length - 1 ? "disabled" : ""}>›</button>
    <button class="btn" id="h-karistir">Haftayı karıştır</button></div></div>
  <div class="istat"><div class="kart"><b>${S.d.siniflar.length}</b><span>Sınıf / salon</span></div><div class="kart"><b>${O.length}</b><span>Oturum</span></div><div class="kart"><b style="color:var(--ok)">${karildi} / ${O.length}</b><span>Karıldı</span></div><div class="kart"><b style="color:${uyari ? "var(--uy)" : "inherit"}">${uyari}</b><span>Uyarı</span></div></div>
  <div class="pano"><div class="pano-sol"><div class="cal" style="grid-template-columns:62px repeat(${gunler.length},minmax(0,1fr))"><div></div>${gunler.map(gunBas).join("")}
    ${saatler.map(s => `<div class="r">${s}. Saat</div>${gunler.map(g => hucre(g, s)).join("")}`).join("")}</div></div>
    <div class="drawer" id="drawer">${secOt ? drawer(secOt) : `<div class="bos" style="padding:30px 0"><b>Oturum seçin</b>Ayrıntılar burada görünür.</div>`}</div></div>`;
  $("#h-geri").onclick = () => { S.hafta--; S.secili = null; ciz(); };
  $("#h-ileri").onclick = () => { S.hafta++; S.secili = null; ciz(); };
  $$(".hucre[data-k]", k).forEach(b => b.onclick = () => { S.secili = b.dataset.k; ciz(); });
  $("#h-karistir").onclick = () => karistir(w.oturumlar.map(o => o.anahtar));
  if (secOt) drawerBagla(secOt);
}
function drawer(o) {
  const sorular = o.sorular.map((q, i) => `<div style="margin-top:10px"><b>${h(q.ders)}</b><div class="s">${q.seviyeler.map(sevAd).join(" + ")} aynı dersi alıyor. Farklı seviyeler yan yana otursun mu?</div>
    ${q.uygulanabilir ? `<div class="seg" data-ders="${h(q.ders)}"><button data-v="serbest" class="${q.secim !== "ayri" ? "on" : ""}">Olabilir</button><button data-v="ayri" class="${q.secim === "ayri" ? "on" : ""}">Oturmasın</button></div>`
      : `<div class="not">Bu ders öğrencilerin %${Math.round(q.oran * 100)}'ini kapsıyor; derse göre ayırmak mümkün değil. Yalnız aynı seviye yan yana oturmaz.</div>`}</div>`).join("");
  const sonuc = (S.sonuc[o.anahtar] || []).filter(Boolean);
  return `<h3>${h(o.tarih_yazi)}</h3><div class="s">${h(o.oturum)}</div>
  <div style="margin:12px 0">${!o.karildi ? `<span class="pill bekle">Bekliyor</span>` : o.uyari ? `<span class="pill uyari">${o.uyari} uyarı</span>` : `<span class="pill ok">Karıldı</span>`}</div>
  <div class="satir"><span>Salon</span><b>${o.salon}</b></div><div class="satir"><span>Öğrenci</span><b>${o.ogrenci}</b></div>
  <div class="bolum">Sınavlar</div>${o.sinavlar.map(x => `<div class="satir"><span>${nokta(x.seviye)} ${h(x.seviye_adi)}</span><b>${h(x.ders)}</b></div>`).join("")}
  ${o.sorular.length ? `<div class="bolum">Aynı ders</div>${sorular}` : ""}
  <div class="bolum">Kelebek dışı sınıflar</div><div class="s" style="margin-bottom:6px">Tıklanan sınıf bu oturumda karıştırılmaz.</div>
  <div id="d-haric">${o.siniflar.map(s => `<span class="chip ${o.haric.includes(s.anahtar) ? "x" : ""}" data-a="${h(s.anahtar)}">${h(s.ad)}</span>`).join("")}</div>
  ${sonuc.length ? `<div class="uyarilar">${sonuc.map(m => `<div>${h(m)}</div>`).join("")}</div>` : ""}
  <div class="btnler" style="margin-top:18px"><button class="btn" id="d-karistir">${o.karildi ? "Yeniden karıştır" : "Bu oturumu karıştır"}</button>
  ${o.karildi ? `<button class="btn g" id="d-gor">Yerleşimi gör</button><button class="btn g k" id="d-sil">Karmayı sil</button>` : ""}</div>`;
}
function drawerBagla(o) {
  $$(".seg button", $("#drawer")).forEach(b => b.onclick = async () => { await dene(() => api("ayni_ders_ayarla", o.anahtar, b.parentElement.dataset.ders, b.dataset.v)); ciz(); });
  $$("#d-haric .chip").forEach(c => c.onclick = async () => { await dene(() => api("haric_degistir", o.anahtar, c.dataset.a)); delete S.sonuc[o.anahtar]; ciz(); });
  $("#d-karistir").onclick = () => karistir([o.anahtar]);
  const g = $("#d-gor"); if (g) g.onclick = () => { S.yer.oturum = o.anahtar; S.yer.salon = null; S.yer.sec = null; git("yerlesim"); };
  const s = $("#d-sil"); if (s) s.onclick = async () => { await dene(() => api("karma_sil", [o.anahtar])); delete S.sonuc[o.anahtar]; ciz(); };
}
async function karistir(liste) {
  let r = await dene(() => api("karistir", liste, false));
  if (r && r.sorular_gerekli) {
    const qs = r.sorular_gerekli;
    const v = await modal(`<h3>Aynı dersi alan seviyeler</h3><div class="s">Bu derslerde farklı seviyeler yan yana otursun mu?</div>
      ${qs.map((q, i) => `<div style="margin-top:14px"><b>${h(q.tarih_yazi)} · ${h(q.saat)}</b><div class="s">${h(q.ders)} · ${q.seviyeler.map(h).join(" + ")}</div><div class="seg" data-i="${i}"><button class="on" data-v="serbest">Olabilir</button><button data-v="ayri">Oturmasın</button></div></div>`).join("")}`,
      [{ ad: "Vazgeç", deger: null }, { ad: "Karıştır", sinif: "", al: kap => $$(".seg", kap).map(sg => $(".on", sg).dataset.v) }]);
    if (!v) return;
    for (let i = 0; i < qs.length; i++) await dene(() => api("ayni_ders_ayarla", qs[i].oturum, qs[i].ders, v[i]));
    r = await dene(() => api("karistir", liste, true));
  }
  if (!r) return;
  (r.sonuclar || []).forEach(s => S.sonuc[s.anahtar] = s.hata ? [s.hata] : s.uyarilar);
  const nu = (r.sonuclar || []).filter(s => s.hata || (s.uyarilar || []).length).length;
  toast(nu ? `${liste.length} oturum karıldı; ${nu} oturumda uyarı var.` : `${liste.length} oturum karıldı.`);
  if (r.notlar && r.notlar.length) await modal(`<h3>Bilgi</h3><div class="s">${r.notlar.map(h).join("<br>")}</div>`, [{ ad: "Tamam", sinif: "" }]);
  ciz();
}
document.addEventListener("click", e => {
  const seg = e.target.closest(".modal .seg button");
  if (seg) { $$("button", seg.parentElement).forEach(b => b.classList.toggle("on", b === seg)); }
});

/* ------------------------------------------------------------------ yerleşim */
async function cizYerlesim(k) {
  const kar = S.d.oturumlar.filter(o => o.karildi);
  if (!kar.length) { k.innerHTML = `<div class="baslik-satir"><div><div class="t">Yerleşim</div><div class="s">Önce Karma sayfasından bir oturumu karıştırın.</div></div></div><div class="kart bos"><b>Karılmış oturum yok</b></div>`; return; }
  if (!kar.some(o => o.anahtar === S.yer.oturum)) S.yer.oturum = kar[0].anahtar;
  const r = await dene(() => api("yerlesim", S.yer.oturum, S.yer.salon));
  if (!r) return;
  S.yer.salon = r.salon; S.yer.veri = r;
  const sinif = S.d.siniflar.find(s => s.anahtar === r.salon) || { tur: "tekli", sutun: 0 };
  const kolon = sinif.sutun || 6, cift = sinif.tur === "ikili" && !sinif.sutun;
  const ks = r.koltuklar.map(q => {
    const sec = S.yer.sec && S.yer.sec.salon === r.salon && S.yer.sec.i === q.i;
    const bul = S.yer.bulunan && S.yer.bulunan.salon === r.salon && S.yer.bulunan.koltuk === q.i;
    return `<button class="koltuk ${q.seviye ? "k" + vk(q.seviye) : "bos-k"} ${sec ? "sec" : ""} ${q.uyari.length ? "sorun" : ""} ${bul ? "bulundu" : ""}" data-i="${q.i}" title="${h(q.uyari.join("\n"))}"><i>${q.i + 1}. sıra</i>${q.no ? `<b>${h(q.ad)}</b><small>${h(q.sinif)} · ${h(q.no)}</small>` : `<small>Boş</small>`}</button>`;
  });
  let izgara;
  if (cift) { const ciftler = []; for (let i = 0; i < ks.length; i += 2) ciftler.push(`<div class="cift">${ks.slice(i, i + 2).join("")}</div>`); izgara = `<div class="koltuklar" style="grid-template-columns:repeat(3,minmax(0,1fr))">${ciftler.join("")}</div>`; }
  else izgara = `<div class="koltuklar" style="grid-template-columns:repeat(${kolon},minmax(0,1fr))">${ks.join("")}</div>`;
  k.innerHTML = `
  <div class="baslik-satir"><div><div class="t">Yerleşim</div><div class="s">İki sıraya sırayla tıklayarak öğrencileri yer değiştirin. Kural bozulursa sorulur.</div></div>
    <div class="btnler"><select id="y-ot" style="width:auto">${kar.map(o => `<option value="${h(o.anahtar)}" ${o.anahtar === S.yer.oturum ? "selected" : ""}>${h(o.tarih_yazi)} · ${h(o.oturum)}</option>`).join("")}</select>
    <input type="text" id="y-ara" placeholder="Öğrenci ara…" style="width:170px"><button class="btn g" id="y-geri" ${r.geri_var ? "" : "disabled"}>Geri al</button></div></div>
  <div class="yer-duzen"><div class="salon-liste">${r.salonlar.map(s => `<button class="salon-oge ${s.anahtar === r.salon ? "on" : ""}" data-a="${h(s.anahtar)}">${nokta(s.seviye)} <b>${h(s.ad)}</b>${s.uyari ? `<span class="pill uyari">${s.uyari}</span>` : ""}<small>${s.dolu}/${s.kapasite}</small></button>`).join("")}</div>
  <div style="flex:1;min-width:0"><div class="kart">${izgara}</div></div></div>`;
  $("#y-ot").onchange = e => { S.yer.oturum = e.target.value; S.yer.salon = null; S.yer.sec = null; S.yer.bulunan = null; ciz(); };
  $$(".salon-oge", k).forEach(b => b.onclick = () => { S.yer.salon = b.dataset.a; ciz(); });
  $("#y-geri").onclick = async () => { const x = await dene(() => api("geri_al")); if (x) { S.yer.sec = null; ciz(); } };
  $("#y-ara").onkeydown = async e => { if (e.key !== "Enter") return; const x = await dene(() => api("ogrenci_bul", S.yer.oturum, e.target.value)); if (x && x.bulunan) { S.yer.bulunan = x.bulunan; S.yer.salon = x.bulunan.salon; ciz(); } else toast("Öğrenci bulunamadı."); };
  $$(".koltuk", k).forEach(b => b.onclick = async () => {
    const i = +b.dataset.i, onceki = S.yer.sec; S.yer.bulunan = null;
    if (!onceki) { S.yer.sec = { salon: r.salon, i }; return ciz(); }
    if (onceki.salon === r.salon && onceki.i === i) { S.yer.sec = null; return ciz(); }
    let x = await dene(() => api("yer_degistir", S.yer.oturum, onceki.salon, onceki.i, r.salon, i, false));
    if (x && x.onay_gerekli) {
      if (await onayla("Kural bozuluyor", `Bu değişiklik uyarı sayısını artırıyor:<br><br>${x.mesajlar.map(h).join("<br>")}<br><br>Yine de yapılsın mı?`, "Yine de yap"))
        x = await dene(() => api("yer_degistir", S.yer.oturum, onceki.salon, onceki.i, r.salon, i, true));
    }
    S.yer.sec = null; ciz();
  });
}

/* ------------------------------------------------------------------ raporlar */
function cizRaporlar(k) {
  const O = S.d.oturumlar, kar = O.filter(o => o.karildi);
  if (!kar.length) { k.innerHTML = `<div class="baslik-satir"><div><div class="t">Raporlar</div><div class="s">Önce en az bir oturumu karıştırın.</div></div></div><div class="kart bos"><b>Karılmış oturum yok</b></div>`; return; }
  const gecerli = new Set(kar.map(o => o.anahtar)); S.rapor = new Set([...S.rapor].filter(a => gecerli.has(a)));
  k.innerHTML = `
  <div class="baslik-satir"><div><div class="t">Raporlar</div><div class="s">Liste 1: öğrenci bazlı (salon ve sıra) · Liste 2: salon bazlı (sıra sırasıyla öğrenciler + seviye özeti)</div></div>
    <div class="btnler"><button class="btn g" id="r-hepsi">Tümünü seç</button><button class="btn" id="r-olustur" ${S.rapor.size ? "" : "disabled"}>PDF oluştur (${S.rapor.size})</button></div></div>
  <div class="kurum-duzen"><div class="kart liste-kutu">${kar.map(o => `<label class="onay-satir"><input type="checkbox" data-k="${h(o.anahtar)}" ${S.rapor.has(o.anahtar) ? "checked" : ""}><b style="min-width:150px">${h(o.tarih_yazi)}</b><span style="min-width:60px">${h(o.oturum)}</span><span style="flex:1;color:var(--gri);font-size:12px">${o.sinavlar.map(x => nokta(x.seviye) + h(x.ders)).join(" · ")}</span>${o.uyari ? `<span class="pill uyari">${o.uyari} uyarı</span>` : ""}</label>`).join("")}</div>
  <div class="kart"><div class="bolum" style="margin-top:0">Seçenekler</div>
    <label class="onay-satir"><input type="checkbox" id="r-l1" checked> Liste 1 – öğrenci yerleri</label>
    <label class="onay-satir"><input type="checkbox" id="r-l2" checked> Liste 2 – salon listeleri</label>
    <label class="onay-satir"><input type="checkbox" id="r-ayri" checked> Her oturum için ayrı dosya</label>
    <div class="bolum">Klasör</div><div class="s" style="word-break:break-all">${h(S.d.kurum.rapor_klasoru)}</div>
    <div class="btnler" style="margin-top:8px"><button class="btn g kucuk" id="r-klasor">Değiştir…</button><button class="btn g kucuk" id="r-ac">Klasörü aç</button></div>
    <div id="r-sonuc"></div></div></div>`;
  $$("input[data-k]", k).forEach(c => c.onchange = () => { c.checked ? S.rapor.add(c.dataset.k) : S.rapor.delete(c.dataset.k); ciz(); });
  $("#r-hepsi").onclick = () => { S.rapor = S.rapor.size === kar.length ? new Set() : new Set(kar.map(o => o.anahtar)); ciz(); };
  $("#r-klasor").onclick = async () => { await dene(() => api("klasor_sec")); ciz(); };
  $("#r-ac").onclick = () => dene(() => api("klasor_ac", S.d.kurum.rapor_klasoru));
  $("#r-olustur").onclick = async () => {
    const b = $("#r-olustur"); b.disabled = true; b.textContent = "Hazırlanıyor…";
    const r = await dene(() => api("rapor_olustur", [...S.rapor], $("#r-l1").checked, $("#r-l2").checked, $("#r-ayri").checked));
    if (!r) { ciz(); return; }
    ciz();
    $("#r-sonuc").innerHTML = `<div class="bolum">Oluşturuldu</div><div class="s">${r.dosyalar.length} dosya klasöre kaydedildi.</div>` + (r.eksik.length ? `<div class="not">${r.eksik.length} oturumda yerleştirilmemiş öğrenci var; Karma sayfasından kontrol edin.</div>` : "");
    toast(`${r.dosyalar.length} PDF oluşturuldu.`);
  };
}

/* ------------------------------------------------------------------ başlangıç */
async function basla() {
  $$("#menu button").forEach(b => b.onclick = () => git(b.dataset.sayfa));
  const r = await api("durum");
  S.d = r.durum;
  git(S.d.siniflar.length && S.d.sinavlar.length ? "karma" : (S.d.siniflar.length ? "takvim" : "kurum"));
  if (window.pywebview.api.selftest_modu) {
    const m = await window.pywebview.api.selftest_modu();
    if (m) selftest();
  }
}
async function selftest() {
  let ok = true, mesaj = "";
  try {
    for (const s of ["kurum", "siniflar", "takvim", "karma", "yerlesim", "raporlar"]) { git(s); await new Promise(r => setTimeout(r, 60)); if (!$("#icerik").innerHTML.length) throw new Error("boş sayfa: " + s); }
    const q = Object.assign({}, S.d.kurum, { okul_adi: "Deneme Lisesi" });
    await api("kurum_kaydet", { okul_adi: q.okul_adi, sinav_basligi: "", alt_baslik: "", mudur: "", mudur_yrd: "", rapor_klasoru: "" });
    if (S.d.kurum.okul_adi !== "Deneme Lisesi") throw new Error("kurum kaydı okunamadı");
    if (HATALAR.length) throw new Error("JS hatası: " + HATALAR.join(" | "));
  } catch (e) { ok = false; mesaj = String(e && e.message || e); }
  await window.pywebview.api.selftest_bitir(ok, mesaj);
}
if (window.pywebview && window.pywebview.api) basla(); else window.addEventListener("pywebviewready", basla);
window.kelebekDurum = () => ({ S, HATALAR });
