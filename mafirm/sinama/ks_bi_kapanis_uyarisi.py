#!/usr/bin/env python3
"""KÖR SINAMA BI — risk uyarısı, riskin bulunduğu HER cevap yolunda mı.

Yönelim (elli altıncı tur). Üç turda aynı biçim üç kez çıktı:

  54. tur  mevzuat belirsizliği uyarısı YALNIZCA "evet" cevabına ekliyordu;
           oysa kural 2 olumsuz iddiayı daha yüksek eşiğe bağlar.
  55. tur  istisnanın itirazlı ölçütü, istisna UYGULANIRKEN hiç anılmıyordu.
  56. tur  bu tur: kapanış yasağı yalnızca "evet" cevabında yazılıyor.

Yirmi yedinci turun kuralı: üç örnek bir SINIFTIR ve sınıf duran bir
sağlamayla kapanır. Sınıfın adı: **uyarı, riskin bulunduğu her cevap yoluna
değil, tek bir yola bağlanmış.**

Dördüncü dosya bunu gösteriyor. Cevap "belirlenemiyor" olduğunda işlem
bildirime tabi OLABİLİR — yani izinsiz kapanış riski CANLIDIR. Çıktı ise
yalnızca "bilinmeyen rakamlar temin edilir" diyor. Türk işlem pratiğindeki
en sonuçlu cümle — *imza serbesttir, kapanış değildir* — tam da cevabın
belirsiz olduğu yerde eksikti.

Değişmez (invaryant) şudur ve bu takım onu kalıcı kılar:

    cevap HAYIR değilse, kapanış yasağı çıktıda olmalıdır.

HAYIR'da yasak yoktur çünkü risk yoktur; EVET ve BELİRLENEMİYOR'da vardır.
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


def cevap(c):
    m = re.search(r"Bildirime tabi mi\s*:\s*(\S+)", c)
    return m.group(1).upper() if m else "?"


KAPANIS = re.compile(r"KAPANIŞ YAPILMAZ|kapanış yapılmaz", re.I)

# --- üç cevap yolu -----------------------------------------------------
BELIRSIZ = kos("Alıcı Holding,tr=900000000,rol=devralan",
               "Hedef A.Ş.,tr=1200000000,rol=hedef")
EVET = kos("Alıcı GmbH,dunya=12000000000,rol=devralan",
           "Hedef A.Ş.,tr=1400000000,dunya=1400000000,rol=hedef")
HAYIR = kos("Alıcı Ltd.,tr=400000000,dunya=900000000,rol=devralan",
            "Hedef Ltd.,tr=50000000,dunya=50000000,rol=hedef")

YOLLAR = (("BELİRLENEMİYOR", BELIRSIZ), ("EVET", EVET), ("HAYIR", HAYIR))

# --- BI-01 · belirsiz cevapta kapanış yasağı var -----------------------
vaka("BI-01", "cevap belirlenemiyorken kapanış yasağı çıktıda",
     bool(KAPANIS.search(BELIRSIZ)),
     "cevap=%s · kapanış yasağı: %s"
     % (cevap(BELIRSIZ), bool(KAPANIS.search(BELIRSIZ))))

# --- BI-02 · belirsiz cevapta dayanağın itirazlı olduğu da yazılı ------
vaka("BI-02", "belirsiz cevapta bekletici etkinin dayanağı itirazlı diye anılıyor",
     "I-03" in BELIRSIZ, "I-03 anıldı mı: %s" % ("I-03" in BELIRSIZ))

# --- BI-03 · evet yolunda ikisi de duruyor (regresyon) -----------------
vaka("BI-03", "bildirime tabi cevapta yasak ve dayanak uyarısı duruyor",
     bool(KAPANIS.search(EVET)) and "I-03" in EVET,
     "yasak: %s · I-03: %s" % (bool(KAPANIS.search(EVET)), "I-03" in EVET))

# --- BI-04 · kesin HAYIR'da yasak YOK (yanlış pozitif denetimi) --------
# Risk yoksa uyarı da olmamalı; her yere konan bir uyarı bilgi taşımaz.
vaka("BI-04", "risk bulunmayan kesin olumsuz cevapta kapanış yasağı yok",
     not KAPANIS.search(HAYIR) and cevap(HAYIR).startswith("HAY"),
     "cevap=%s · yasak: %s" % (cevap(HAYIR), bool(KAPANIS.search(HAYIR))))

# --- BI-05 · SINIF SAĞLAMASI: değişmez bütün yollarda tutuyor ----------
# cevap HAYIR değilse kapanış yasağı olmalı. Bu, uyarının tek bir cevap
# yoluna bağlanmasını kalıcı olarak yasaklar.
_ihlal = [ad for ad, c in YOLLAR
          if not cevap(c).startswith("HAY") and not KAPANIS.search(c)]
vaka("BI-05", "değişmez: cevap HAYIR değilse kapanış yasağı çıktıda",
     not _ihlal, "%d cevap yolu sınandı · ihlal: %s"
     % (len(YOLLAR), _ihlal or "yok"))


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BI-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
