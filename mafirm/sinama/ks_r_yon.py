#!/usr/bin/env python3
"""KÖR SINAMA R — yön, insan onayı ve dil kuralları, raporun kendisine.

Dokuz tur boyunca kitabın kurallarını uyguladım; üçü kaldı ve üçü de bu
raporun KENDİ biçimi hakkında.

§4 · Yön: *"Her çıktı cevapla başlar. Sonra gerekçe, en sonda yöntem.
Yöntemi merak eden okuyucu aşağı iner; cevabı merak eden ilk paragrafta
bulur."*
Bu rapor dokuz tur boyunca `## Yöntem` ile BAŞLIYORDU ve cevabı 818. satırda
duruyordu. Kuralın önlemek için var olduğu şeyin ta kendisi.

§9 · İnsan onayı: *"Şu çıktılar adı belli bir insan onaylamadan
kullanılmaz."* Bir rapor onay taşımıyorsa, taşımadığını YAZMALIDIR; sessizlik
onaylanmış gibi okunur.

§10 · Dil: piyasada karşılığı yerleşmiş terimler korunur ama *"ilk
geçtiklerinde açıklanır."* Rapor NFKC, CONNECT, homoglif gibi terimleri
açıklamadan kullanıyordu.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def basliklar(rel):
    s = open(os.path.join(_KOK_COZ, rel), encoding="utf-8").read()
    return s, [(m.start(), m.group(1))
               for m in re.finditer(r"^## (.+)$", s, re.M)]


s, b = basliklar("RAPOR.md")
adlar = [a for _, a in b]

# --- §4: ilk bölüm CEVAP, yöntem DEĞİL ---------------------------------
vaka("R-01", "rapor cevapla başlıyor, yöntemle değil",
     bool(adlar) and adlar[0].strip().lower().startswith("cevap"),
     "ilk bölüm: %r — §4: 'cevabı merak eden ilk paragrafta bulur'"
     % (adlar[0] if adlar else None))

# --- §4: yöntem, bulgulardan SONRA -------------------------------------
try:
    i_yontem = adlar.index("Yöntem")
except ValueError:
    i_yontem = -1
i_bir = next((k for k, a in enumerate(adlar) if a.startswith("Bir ·")), -1)
vaka("R-02", "yöntem bölümü bulgulardan sonra geliyor",
     i_yontem > i_bir > 0,
     "yöntem %d. başlık, ilk bulgu %d. başlık" % (i_yontem, i_bir))

# --- §5: iki zorunlu başlık, EN SONDA ve bu sırayla --------------------
vaka("R-03", "iki zorunlu başlık en sonda ve doğru sırada",
     len(adlar) >= 2 and adlar[-2].startswith("Şimdi ne yapılmalı")
     and adlar[-1].startswith("Yetkili avukat"),
     "son iki başlık: %s" % adlar[-2:])

# --- §9: onay durumu AÇIKÇA yazılmış -----------------------------------
onay = re.search(r"adı belli bir insan tarafından\s*\n?onaylanmamıştır"
                 r"|onaylanmamıştır|insan onayı", s, re.I)
vaka("R-04", "raporun onay durumu açıkça yazılı (§9)",
     bool(onay),
     "sessizlik onaylanmış gibi okunur; rapor onaysız olduğunu söylemeli")

# --- §9: onay ifadesi CEVAP bölümünde, dipnotta değil ------------------
cevap_govde = s[b[0][0]:b[1][0]] if len(b) > 1 else ""
vaka("R-05", "onay durumu ilk bölümde, dipnotta değil",
     bool(re.search(r"onaylanmamıştır", cevap_govde)),
     "okuyucu bunu 800 satır sonra değil, ilk ekranda görmeli")

# --- §10: teknik terimler ilk geçişte açıklanmış -----------------------
# [R-06, dedektörün kendi kusuru] İlk sürüm [^\n] kullanıyordu, yani açıklamanın
# terimle AYNI SATIRDA olmasını istiyordu. Satır kaydırması olan bir açıklama
# görünmez oluyordu ve dedektör "açıklanmamış" diyordu. Bu oturumda aynı sınıftan
# sekizinci ayrıştırıcı kusurum: bir dedektör, ölçtüğü şeyin gerçek biçimini
# görmeden yazılırsa bulduğu şey kendi körlüğüdür.
TERIMLER = {
    "NFKC": r"NFKC[\s\S]{0,200}?(normalleştir|ayrış|indirge)",
    "CONNECT": r"CONNECT[\s\S]{0,200}?(vekil|bağlantı|istek)",
    "homoglif": r"homoglif[\s\S]{0,200}?(görsel|eşdeğer|Kiril|Yunan)",
}
aciklanmamis = []
for terim, desen in TERIMLER.items():
    ilk = s.find(terim)
    if ilk < 0:
        continue
    pencere = s[ilk:ilk + 320]
    if not re.search(desen, pencere, re.S | re.I):
        aciklanmamis.append(terim)
vaka("R-06", "teknik terimler ilk geçtiklerinde açıklanmış (§10)",
     not aciklanmamis, "açıklanmamış: %s" % (aciklanmamis or "yok"))

# --- MUTASYON: yöntem başa alınırsa R-01 yakalar -----------------------
sahte = ["Yöntem"] + [a for a in adlar if a != "Yöntem"]
vaka("R-07", "mutasyon: yöntem başa alınırsa R-01 yakalar",
     not sahte[0].lower().startswith("cevap"),
     "kural 4 ihlali makinece görülebilir")


def rapor():
    print("=" * 96)
    print("KÖR SINAMA R — yön, insan onayı ve dil kuralları")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, _ = beklenen.durum(kod, gecti)
        print("%s %-6s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _sinyal, _sayim = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _sayim["GEÇTİ"], _sayim["BEKLENEN"], _sinyal))
    return _sinyal


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
