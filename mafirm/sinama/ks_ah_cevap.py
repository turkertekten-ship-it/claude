#!/usr/bin/env python3
"""KÖR SINAMA AH — raporun CEVABI hâlâ raporun kendisini anlatıyor mu.

§4 "önce cevap" der ve R takımı bunu YAPI düzeyinde ölçer: ilk bölüm cevap mı,
yöntem sona mı kalmış. Ama bir cevap, doğru YERDE durup yanlış ŞEY söyleyebilir.

Bu rapor yirmi beş turda büyüdü. "Cevap" bölümü yedinci turda yazıldı ve üç
sebep sayıyordu. On üç [A] ağırlıklı bulgu var ve dördü — kural 6'nın depodan
sızması, kapının çöktüğünde AÇIK düşmesi, web yetkili ajanın sınırsızlığı,
yeniden kurulumun denetçiyi ezmesi — cevapta HİÇ GEÇMİYORDU. İlk ekranı okuyan
bir kişi, en tehlikeli şeyin ne olduğunu yanlış öğreniyordu.

Bu, §4'ün LAFZINA değil RUHUNA aykırıdır: cevap ilk sırada duruyordu ama
güncel değildi. Ve bu, raporun kendi belgelediği sınıfın son hâlidir — el
yazısı bir özet, özetlediği şeyden bağımsız yaşar.

ÖLÇÜT NEDEN BEYAN: kelime örtüşmesi burada YANLIŞ araçtır ve bunu AF-04'te
bir kez öğrendim. Cevap, bulguları PARAFRAZ eder ("öz-sınama üretim yolunu
koşturmuyor" -> "§14, §12'nin öz-sınamasını bozuyor"). Ortak kelime sayan bir
ölçüt on üçün on birini yanlış işaretliyordu. Bunun yerine her [A] bulgusu,
kendisini temsil eden cevap noktasını AÇIKÇA BEYAN eder; beyanı sürdürmek,
yeni bir ağır bulgunun cevaba girip girmediğini fark etmeye zorlar.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def oku(rel):
    p = os.path.join(KOK, rel)
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


RAPOR = oku("RAPOR.md")
ERRATA = oku("KITAP-ERRATA.md")
_m = re.search(r"## Cevap\n(.*?)\n## ", RAPOR, re.S)
CEVAP = _m.group(1) if _m else ""

# Cevabın numaralı sebepleri
SEBEPLER = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", CEVAP, re.M)

# --- AH-01 · cevap gerçekten sebep sayıyor mu -------------------------
vaka("AH-01", "cevap numaralı sebepleri taşıyor", len(SEBEPLER) >= 3,
     "%d sebep: %s" % (len(SEBEPLER),
                       "; ".join("%s) %s" % (n, t[:38]) for n, t in SEBEPLER)))

# --- AH-02 · "N cümlede sebebi" ifadesi sebep sayısıyla uyuşuyor mu ---
SAYI = {"iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6, "yedi": 7}
m = re.search(r"([A-Za-zçğıöşü]+) cümlede sebebi", CEVAP)
iddia = SAYI.get(m.group(1).lower()) if m else None
vaka("AH-02", "'N cümlede sebebi' ifadesi sayılan sebeple uyuşuyor",
     iddia is not None and iddia == len(SEBEPLER),
     "ifade '%s' (=%s), sayılan %d"
     % (m.group(1) if m else "-", iddia, len(SEBEPLER)))

# --- AH-03 · her [A] bulgusu bir cevap noktası BEYAN ediyor -----------
# Beyan biçimi: errata maddesinin sonunda  →CEVAP: <n|YOK|gerekçe>
AGIR = re.findall(r"^\*\*\[A\] ([^*]+)\*\*(.*?)(?=\n\*\*\[|\n## |\Z)",
                  ERRATA, re.M | re.S)
beyansiz = []
for baslik, govde in AGIR:
    if "→CEVAP:" not in govde:
        beyansiz.append(baslik.strip()[:60])
vaka("AH-03", "her [A] bulgusu bir cevap noktası beyan ediyor",
     not beyansiz,
     ("BEYANSIZ (%d): %s" % (len(beyansiz), "; ".join(beyansiz[:4])))
     if beyansiz else "%d [A] bulgusunun hepsi beyanlı" % len(AGIR))

# --- AH-04 · beyan edilen cevap noktası GERÇEKTEN var mı -------------
cozulmeyen = []
for baslik, govde in AGIR:
    mm = re.search(r"→CEVAP:\s*([^\n]+)", govde)
    if not mm:
        continue
    hedef = mm.group(1).strip()
    if hedef.upper().startswith("YOK"):
        continue                      # gerekçesiyle temsil edilmiyor
    no = re.match(r"(\d+)", hedef)
    if not no or no.group(1) not in {n for n, _t in SEBEPLER}:
        cozulmeyen.append("%s -> %s" % (baslik.strip()[:40], hedef[:30]))
vaka("AH-04", "beyan edilen her cevap noktası cevapta gerçekten var",
     not cozulmeyen, "; ".join(cozulmeyen) if cozulmeyen
     else "beyan edilen noktaların hepsi cevapta mevcut")

# --- AH-05 · "temsil edilmiyor" beyanı GEREKÇE taşıyor mu ------------
# Bir ağır bulguyu cevaba koymamak meşru olabilir (cevap bir özet değildir);
# ama sessizce olmamalı. YOK diyen her beyan sebebini yazar.
gerekcesiz = []
for baslik, govde in AGIR:
    mm = re.search(r"→CEVAP:\s*YOK\s*—?\s*([^\n]*)", govde)
    if mm and len(mm.group(1).strip()) < 15:
        gerekcesiz.append(baslik.strip()[:50])
vaka("AH-05", "cevaba girmeyen ağır bulgu gerekçesini yazıyor",
     not gerekcesiz, "; ".join(gerekcesiz) if gerekcesiz
     else "gerekçesiz 'YOK' beyanı yok")


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AH-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AH — raporun cevabı hâlâ raporu anlatıyor mu")
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
