#!/usr/bin/env python3
"""KÖR SINAMA BH — üçüncü dosya: model, itiraz edilen ölçütü söyleyebiliyor mu.

Yönelim (elli beşinci tur). Elli dördüncü tur I-01'in bandını buldu: kitap
"HAYIR" derken kayıtlı alternatif okuma "bildirime tabi" diyordu. I-02 bunun
AYNASIDIR ve daha derin bir soru sorar — teknoloji istisnasına kimin HAK
KAZANDIĞI.

  * Kitabın yazdığı ölçüt: hedef, Türkiye'de "faaliyet gösteren ya da Ar-Ge
    yürüten" bir teknoloji teşebbüsüyse 250 milyon TL uygulanır.
  * I-02'nin kayıtlı alternatifi: güncel ölçüt "Türkiye'de YERLEŞİK" olabilir
    (2022/2'nin kalkmış ölçütü ile karıştırılmış olabilir). Doğruysa,
    Türkiye'de yerleşik OLMAYAN bir teknoloji hedefi istisnanın tamamen
    dışındadır ve 250 milyon değil 1 milyar TL uygulanır.

Üçüncü dosya bu ayrımın cevabı çevirdiği bandı seçer: Türkiye'de faaliyet
gösteren ama yerleşik OLMAYAN bir teknoloji hedefi, Türkiye cirosu 400
milyon TL, alıcının dünya cirosu 12 milyar TL.

  kitabın okuması : 400 > 250 -> B karşılanır -> EVET, bildirime tabi
  I-02'nin okuması: istisna uygulanmaz, 400 < 1.000 -> HAYIR

Ölçüldü ve İKİ kusur çıktı:

  1. Çıktı "teknoloji teşebbüsü istisnası uygulandı" diyor ve I-02'yi HİÇ
     anmıyor. Elli dördüncü turun kusuru, bu kez OLUMLU cevap yolunda.
  2. Daha ağırı: MODEL bu ayrımı SÖYLEYEMİYOR. `teknoloji` tek bir doğru/
     yanlış alanıdır; "Türkiye'de faaliyet gösteriyor ama yerleşik değil"
     hâli girilemez. Yani kullanıcı, itiraz edilen ölçütün karşılandığını
     istemeden BEYAN etmiş olur. Bir modelin söyleyemediği ayrım, o modeli
     kullanan hukukçunun göremediği ayrımdır.

Bu takım cevabı DEĞİŞTİRMEZ; ölçütün itirazlı olduğunu görünür kılar (§9).
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_ESIK = os.path.join(_KOK, "birimler", "rekabet", "kod", "esik.py")

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def kos(*taraf):
    argv = [sys.executable, _ESIK]
    for t in taraf:
        argv += ["--taraf", t]
    p = subprocess.run(argv, capture_output=True, text=True)
    return p.stdout + p.stderr


def belirgin_blok(cikti):
    m = re.search(r"AÇIK MEVZUAT SORUSU[^\n]*\n((?:\s+!.*\n)+)", cikti)
    return m.group(1) if m else ""


# --- üçüncü dosya: yerleşiklik bilinmiyor ------------------------------
BILINMEYEN = kos("Alıcı Inc.,dunya=12000000000,rol=devralan",
                 "Hedef Tech GmbH,tr=400000000,dunya=900000000,"
                 "rol=hedef,teknoloji=1")
# --- yerleşiklik AÇIKÇA beyan edilmiş ----------------------------------
YERLESIK = kos("Alıcı Inc.,dunya=12000000000,rol=devralan",
               "Hedef Tek A.Ş.,tr=400000000,dunya=900000000,"
               "rol=hedef,teknoloji=1,yerlesik=1")
# --- teknoloji hiç yok: istisna uygulanmıyor ---------------------------
TEKNOLOJISIZ = kos("Alıcı Inc.,dunya=12000000000,rol=devralan",
                   "Hedef A.Ş.,tr=1400000000,dunya=1400000000,rol=hedef")

_blok = belirgin_blok(BILINMEYEN)

# --- BH-01 · istisna uygulandığında itirazlı ölçüt anılıyor ------------
vaka("BH-01", "teknoloji istisnası uygulanırken I-02 belirgin blokta anılıyor",
     "I-02" in _blok,
     "cevap=%s · belirgin blok %d karakter · I-02: %s"
     % (re.search(r"Bildirime tabi mi\s*:\s*(\S+)", BILINMEYEN).group(1)
        if re.search(r"Bildirime tabi mi\s*:\s*(\S+)", BILINMEYEN) else "?",
        len(_blok), "I-02" in _blok))

# --- BH-02 · uyarı ters yönü söylüyor ---------------------------------
# I-01'de cevap HAYIR'dan EVET'e dönüyordu; burada EVET'ten HAYIR'a.
# [Mutasyon bulgusu] İlk alternasyon "uygulanmaz" sözcüğünü de kabul
# ediyordu — ama o sözcük İSTİSNANIN düşmesini anlatır, CEVABIN dönmesini
# değil, ve zaten metinde başka bir sebeple duruyor. Ters dönme ifadesi
# tamamen silindiğinde vaka yeşil kalıyordu. Ölçüt, cevabın döndüğünü
# SÖYLEYEN ifadeyi istemeli; yakınındaki bir sözcüğü değil.
_TERS = re.compile(r"TERS DÖNER|bildirime tabi olmayabilir", re.I)
vaka("BH-02", "uyarı, istisna düşerse cevabın olumsuza döneceğini söylüyor",
     bool(_TERS.search(_blok)) and "1.000.000.000" in _blok,
     "ters yön ifadesi: %s · karşıt eşik yazılı: %s"
     % (bool(_TERS.search(_blok)), "1.000.000.000" in _blok))

# --- BH-03 · yerleşiklik beyan edilince uyarı düşüyor -----------------
vaka("BH-03", "yerleşiklik açıkça beyan edilince I-02 uyarısı düşüyor",
     "I-02" not in belirgin_blok(YERLESIK),
     "beyanlı olguda I-02: %s" % ("I-02" in belirgin_blok(YERLESIK)))

# --- BH-04 · model ayrımı SÖYLEYEBİLİYOR ------------------------------
# Bir modelin söyleyemediği ayrım, hukukçunun göremediği ayrımdır.
vaka("BH-04", "girdi modeli yerleşiklik ayrımını ifade edebiliyor",
     "yerlesik" in open(_ESIK, encoding="utf-8").read()
     and "hata" not in YERLESIK.lower() and "Traceback" not in YERLESIK,
     "alan tanımlı ve kabul ediliyor: %s"
     % ("Traceback" not in YERLESIK))

# --- BH-05 · istisna yokken uyarı da yok (yanlış pozitif denetimi) ----
vaka("BH-05", "teknoloji istisnası uygulanmayan olguda I-02 uyarısı yok",
     "I-02" not in TEKNOLOJISIZ,
     "teknolojisiz olguda I-02: %s" % ("I-02" in TEKNOLOJISIZ))


# --- BH-06 · cevap DEĞİŞTİRİLMEMİŞ, karar insana bırakılmış -----------
# [Mutasyon bulgusu] İlk sürümde bu güvence yalnızca BG'deydi; kod I-02
# uyarısı varken cevabı kendiliğinden HAYIR'a çevirdiğinde BH hiçbir şey
# söylemiyordu. Bir sınırı bir takımda koyup ötekinde koymamak, sınırı
# yarım koymaktır: §9 her iki yolda da geçerlidir.
_c = re.search(r"Bildirime tabi mi\s*:\s*(\S+)", BILINMEYEN)
vaka("BH-06", "sistem cevabı kendiliğinden değiştirmiyor (§9)",
     bool(_c) and _c.group(1).upper().startswith("EVET"),
     "cevap=%s (kitabın okumasına göre EVET olmalı)"
     % (_c.group(1) if _c else "?"))


BEKLENEN_VAKA = 6


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BH-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    genislik = max(len(b) for _, b, _, _ in sonuclar) + 2
    for kod, baslik, gecti, kanit in sonuclar:
        etiket, _ = beklenen.durum(kod, gecti)
        print("%-14s %-6s %-*s %s"
              % (etiket, kod, genislik, baslik, kanit if not gecti else ""))
    sinyal, sayim = beklenen.ozet([(k, g) for k, _, g, _ in sonuclar])
    print("-" * 100)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), sayim["GEÇTİ"], sayim["BEKLENEN"], sinyal))
    return sinyal


if __name__ == "__main__":
    sys.exit(rapor())
