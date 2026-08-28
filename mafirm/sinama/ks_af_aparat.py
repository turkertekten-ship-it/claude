#!/usr/bin/env python3
"""KÖR SINAMA AF — aparatın kendi hakkındaki iddiaları.

Yirmi üç tur boyunca sistemi ölçtüm. Ölçen şeyin kendisi — koşum betiği,
beyan edilmiş taban, raporun ölçüm cümleleri — büyük ölçüde ölçülmedi.

Üç iddia sınıfı var ve üçü de sessizce bozulabilir:

  1. "Her takım koşuyor."   hepsi.sh ÇAĞRILARI ELLE yazılır. Bir takım
     eklenip bağlanmazsa diskte durur, raporda anılır ve HİÇ KOŞMAZ.
  2. "Beyan edilmiş taban doğru."  beklenen.json bir vakanın GEÇMEYE
     başladığını yakalar (BEKLENMEDİK GEÇİŞ) — ama BAŞKA BİR SEBEPLE
     düşmeye başladığını yakalamaz. Yeni bir kusur, eski bir beyanın
     arkasına saklanabilir.
  3. "Kaybolan vaka yakalanır."  On üçüncü turda bir vaka iki kez sessizce
     kayboldu ve BEKLENEN_VAKA koruması eklendi — ama YALNIZCA o turdan
     sonra yazılan takımlara. Düzeltme ileriye uygulandı, geriye
     doldurulmadı.

Üçüncüsü, yirmi üçüncü turun bulgusunun aynısıdır: bir sınıfı örnek örnek
düzeltmek, sınıfı kapatmaz.
"""
import io
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(KOK, "sinama")
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def oku(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


TAKIMLAR = sorted(a for a in os.listdir(S)
                  if re.match(r"ks_[a-z]{1,2}_.*\.(py|sh)$", a))
HEPSI = oku(os.path.join(S, "hepsi.sh"))

# --- AF-01 · diskteki her takım koşum betiği tarafından ÇAĞRILIYOR ----
cagrilan = set(re.findall(r"ks_[a-z]{1,2}_[a-z_]+\.(?:py|sh)", HEPSI))
kosmayan = [t for t in TAKIMLAR if t not in cagrilan]
hayalet = [c for c in sorted(cagrilan) if c not in TAKIMLAR]
vaka("AF-01", "diskteki her takım hepsi.sh tarafından çağrılıyor",
     not kosmayan and not hayalet,
     ("ÇAĞRILMAYAN: %s" % ", ".join(kosmayan) if kosmayan else "")
     + ("  OLMAYANI ÇAĞIRAN: %s" % ", ".join(hayalet) if hayalet else "")
     or "%d takımın hepsi çağrılıyor" % len(TAKIMLAR))

# --- AF-02 · her takım KAYBOLAN VAKA korumasını taşıyor --------------
# On üçüncü turda eklendi; yalnızca sonrasında yazılanlara. 15 takım
# korumasızdı — B'de 34, A'da 24 vaka var ve birinin kaybolması görünmezdi.
# Dizge varlığı YETMEZ: beyan satırı silindiğinde `rapor()` içindeki
# KULLANIM hâlâ "BEKLENEN_VAKA" dizgesini taşır ve kontrol boşuna geçer —
# mutasyon tam olarak böyle sağ kaldı. Aranan şey MODÜL DÜZEYİNDE bir
# ATAMADIR; ayrıca takımın gerçekten koşabildiği de doğrulanır.
BEYAN_SATIRI = re.compile(r"^BEKLENEN_(?:VAKA|KURAL)\s*=\s*\d+", re.M)
korumasiz = [t for t in TAKIMLAR if t.endswith(".py")
             and not BEYAN_SATIRI.search(oku(os.path.join(S, t)))]
vaka("AF-02", "her python takımı kaybolan vaka korumasını taşıyor",
     not korumasiz,
     ("KORUMASIZ (%d): %s" % (len(korumasiz), ", ".join(korumasiz)))
     if korumasiz else
     "%d python takımının hepsi vaka sayısını beyan ediyor"
     % sum(1 for t in TAKIMLAR if t.endswith(".py")))

# --- AF-03 · beyan edilmiş her vaka koşumda BEKLENEN olarak görünüyor -
BEYAN = json.load(io.open(os.path.join(S, "beklenen.json"),
                          encoding="utf-8"))["vakalar"]
KOSUM = oku(os.path.join(S, "SONUC-sonra.txt"))
kayip = [k for k in sorted(BEYAN)
         if not re.search(r"^BEKLENEN\s+%s\b" % re.escape(k), KOSUM, re.M)]
vaka("AF-03", "beyan edilmiş her vaka koşumda BEKLENEN olarak görünüyor",
     not kayip,
     ("koşumda BEKLENEN olarak görünmeyen: %s — beyan bayat ya da vaka "
      "kayboldu" % ", ".join(kayip)) if kayip
     else "%d beyanın hepsi koşumda yerinde" % len(BEYAN))

# --- AF-04 · beyan edilen BELİRTİ hâlâ aynı mı ----------------------
# İLK SÜRÜM YANLIŞTI: beyan METNİ ile canlı ayrıntıyı kelime örtüşmesiyle
# kıyaslıyordu ve on iki beyanın onunu işaretliyordu — oysa elle kıyasladığımda
# hepsi doğruydu. Beyan bir GEREKÇEDİR (neden bırakıldı), canlı ayrıntı bir
# ÖLÇÜMDÜR (ne oldu); ikisi haklı olarak farklı kelimeler kullanır. Onda
# sekizi yanlış işaretleyen bir ölçüt, kırmızıyı görmezden gelmeyi öğretir.
#
# Doğru mekanizma: beyan anında görülen ayrıntı BELİRTİ olarak KAYDEDİLİR;
# her koşumda canlı ayrıntı o belirtiyle karşılaştırılır. Böylece "vaka hâlâ
# düşüyor" değil, "vaka HÂLÂ AYNI SEBEPLE düşüyor" ölçülür.
def _parmak(c):
    return {k[:6] for k in re.findall(r"[\wçğıöşüÇĞİÖŞÜ]{4,}", c.lower())}


kaymis, belirtisiz = [], []
for kod in sorted(BEYAN):
    belirti = BEYAN[kod].get("belirti")
    m = re.search(r"^BEKLENEN\s+%s\s+[^\n]*\n(?:\s{4,}([^\n]*)\n)?"
                  % re.escape(kod), KOSUM, re.M)
    canli = (m.group(1) or "").strip() if m else ""
    if not belirti:
        belirtisiz.append(kod)
        continue
    if not canli:
        continue
    a, b = _parmak(belirti), _parmak(canli)
    if not a:
        continue
    ortusme = len(a & b) / len(a)
    if ortusme < 0.6:
        kaymis.append("%s (%%%d örtüşme)" % (kod, ortusme * 100))
vaka("AF-04", "beyan edilen belirti hâlâ canlı belirtiyle aynı",
     not kaymis and not belirtisiz,
     ("BELİRTİ KAYMASI: %s" % ", ".join(kaymis) if kaymis else "")
     + ("  belirtisiz beyan: %s" % ", ".join(belirtisiz) if belirtisiz else "")
     or "%d beyanın belirtisi değişmemiş" % len(BEYAN))

# --- AF-05 · raporun ÖLÇÜM iddiaları canlı çıktıyla uyuşuyor ---------
RAPOR = oku(os.path.join(KOK, "RAPOR.md"))


def _kos(betik):
    y = os.path.join(S, betik)
    komut = ["bash", y] if betik.endswith(".sh") else [sys.executable, y]
    r = subprocess.run(komut, capture_output=True, text=True,
                       env=dict(os.environ, MAFIRM=KOK), timeout=600)
    return r.stdout


IDDIA = []
d_cikti = _kos("ks_d_denetim.sh")
m = re.search(r"(\d+) mutasyon · (\d+) yakalandı", d_cikti)
if m:
    IDDIA.append(("denetim mutasyonu", "%s/%s" % (m.group(2), m.group(1)),
                  "%s/%s" % (m.group(2), m.group(1)) in RAPOR))
v_cikti = _kos("ks_v_yanlis_pozitif.py")
m = re.search(r"(\d+) meşru metnin", v_cikti)
if m:
    IDDIA.append(("V meşru korpus", m.group(1),
                  "%s meşru metin" % m.group(1) in RAPOR
                  or "%s meşru" % m.group(1) in RAPOR))
yanlis = [ad for ad, deger, tamam in IDDIA if not tamam]
vaka("AF-05", "raporun ölçüm iddiaları canlı çıktıyla uyuşuyor",
     not yanlis and bool(IDDIA),
     ("uyuşmayan: %s" % ", ".join(yanlis)) if yanlis
     else "%d ölçüm iddiası canlı koşumla doğrulandı (%s)"
          % (len(IDDIA), ", ".join("%s=%s" % (a, d) for a, d, _t in IDDIA))
     if IDDIA else "ölçüm iddiası çıkarılamadı")


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AF-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AF — aparatın kendi hakkındaki iddiaları")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, _ = beklenen.durum(kod, gecti)
        print("%s %-7s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _s, _c = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _c["GEÇTİ"], _c["BEKLENEN"], _s))
    return _s


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
