#!/usr/bin/env python3
"""KÖR SINAMA BG — ikinci dosya: cevabı çeviren açık soru çıktıda mı.

Yönelim (elli dördüncü tur). J takımı §19'un pilotunu uçtan uca koşuyor —
ama sistem elli üç tur boyunca TEK BİR işlem biçiminde sınandı: yabancı
alıcı, B ayağı, EVET cevabı. Kitabın yöntemi bundan fazlasını iddia ediyor:
A ayağı, teknoloji istisnası, üç değerli cevap.

İkinci bir dosya kitabın DÜZYAZISINDAN türetildi ve iki okumanın AYNI
OLGULARDA ters cevap verdiği bir bant seçildi:

    Türk alıcı  — Türkiye cirosu 2,8 milyar TL
    Türk hedef  — teknoloji teşebbüsü, Türkiye cirosu 300 milyon TL

  * Kitabın yazdığı okuma: A ayağının ikinci bacağı "en az iki tarafın AYRI
    AYRI 1 milyar TL'yi aşması"nı ister; hedef 300 milyon → A karşılanmaz.
    B ayağında diğer tarafın DÜNYA cirosu 9 milyarın altında → B karşılanmaz.
    Cevap: HAYIR.
  * I-01'in kayıtlı alternatif okuması: teknoloji indirimi (250 milyon) A
    ayağına da uygulanıyorsa hedef 300 milyon > 250 milyon → A KARŞILANIR.
    Cevap: EVET, bildirime tabi.

Yani aynı rakamlarda cevap TERSİNE DÖNÜYOR ve fark, izinsiz kapanış
demektir. Ölçüldü: sistem "HAYIR — Eşik aşılmıyor" diyor ve I-01'i HİÇ
anmıyor. Uyarı yöntem dosyasında duruyor, çıktıya ulaşmıyor.

Daha da keskini: kod, mevzuat belirsizliği uyarısını YALNIZCA EVET cevabına
ekliyor. İşletim sözleşmesinin 2. kuralı tam tersini söyler — *olumsuz bir
iddia, olumludan daha yüksek bir kanıt eşiği ister.* "Bildirime tabi değil"
cümlesi, kuralın adıyla andığı kariyer bitiren cümledir.

Bu takım cevabı DEĞİŞTİRMEZ: HAYIR'ı EVET'e çevirmek bir hukuki
nitelendirmedir ve §9 uyarınca insana aittir. Sınadığı şey, açık sorunun
çıktıda GÖRÜNÜP görünmediğidir.
"""
import io
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


# --- ikinci dosya: iki okumanın ters cevap verdiği bant ----------------
ITIRAZLI = kos("Alıcı A.Ş.,tr=2800000000,dunya=5000000000,rol=devralan",
               "Hedef Teknoloji A.Ş.,tr=300000000,dunya=300000000,"
               "rol=hedef,teknoloji=1")
# --- bant DIŞI: teknoloji değil, rakamlar eşiklerden uzak --------------
TEMIZ = kos("Alıcı Ltd.,tr=400000000,dunya=900000000,rol=devralan",
            "Hedef Ltd.,tr=50000000,dunya=50000000,rol=hedef")
# --- açıkça bildirime tabi: I-03 uyarısı korunuyor mu ------------------
EVET = kos("Alıcı GmbH,dunya=12000000000,rol=devralan",
           "Hedef A.Ş.,tr=1400000000,dunya=1400000000,rol=hedef")

def belirgin_blok(cikti):
    """"AÇIK MEVZUAT SORUSU" başlığı altındaki blok.

    [Kendi kusurum] İlk sürüm yalnızca "I-01 çıktıda geçiyor mu" diye
    sordu. Üst uyarı tamamen bastırıldığında bile kimlik, "Yetkili avukat
    görüşü" listesinde geçmeye devam ediyordu ve vaka yeşil kalıyordu —
    yani ölçüt, uyarının GÖRÜNÜRLÜĞÜNÜ değil yalnızca varlığını ölçüyordu.
    Oysa bulgunun değeri, olumsuz cevabın YANINDA durmasıdır."""
    m = re.search(r"AÇIK MEVZUAT SORUSU[^\n]*\n((?:\s+!.*\n)+)", cikti)
    return m.group(1) if m else ""


_blok = belirgin_blok(ITIRAZLI)

# --- BG-01 · açık bulgu, BELİRGİN uyarı bloğunda anılıyor --------------
vaka("BG-01", "cevabı tersine çeviren açık bulgu belirgin blokta anılıyor",
     "I-01" in _blok,
     "cevap=%s · belirgin blok %d karakter · I-01: %s"
     % (re.search(r"Bildirime tabi mi\s*:\s*(\S+)", ITIRAZLI).group(1)
        if re.search(r"Bildirime tabi mi\s*:\s*(\S+)", ITIRAZLI) else "?",
        len(_blok), "I-01" in _blok))

# --- BG-02 · uyarı, cevabın DÖNEBİLECEĞİNİ açıkça söylüyor -------------
DONER = re.compile(r"TERS DÖNER|cevap.{0,20}değiş|bildirime tabi olabilir",
                   re.I)
vaka("BG-02", "belirgin uyarı cevabın ters dönebileceğini söylüyor",
     bool(DONER.search(_blok)) and "BİLDİRİME TABİDİR" in _blok,
     "dönme ifadesi: %s · karşıt sonuç yazılı: %s"
     % (bool(DONER.search(_blok)), "BİLDİRİME TABİDİR" in _blok))

# --- BG-03 · bant DIŞINDA uyarı yok (yanlış pozitif denetimi) ----------
vaka("BG-03", "bant dışındaki olumsuz cevapta itiraz uyarısı yok",
     "I-01" not in TEMIZ, "temiz olguda I-01 anıldı mı: %s" % ("I-01" in TEMIZ))

# --- BG-04 · cevap DEĞİŞTİRİLMEMİŞ, karar insana bırakılmış ------------
# §9: hukuki nitelendirme insana aittir. Takım uyarı ister, karar istemez.
_cevap = re.search(r"Bildirime tabi mi\s*:\s*(\S+)", ITIRAZLI)
vaka("BG-04", "sistem cevabı kendiliğinden değiştirmiyor (§9)",
     bool(_cevap) and _cevap.group(1).lower().startswith("hay")
     and bool(re.search(r"insan|yetkili avukat", ITIRAZLI, re.I)),
     "cevap=%s" % (_cevap.group(1) if _cevap else "?"))

# --- BG-05 · EVET yolundaki I-03 uyarısı korunuyor ---------------------
vaka("BG-05", "bildirime tabi cevapta bekletici etki uyarısı duruyor",
     "I-03" in EVET and "KAPANIŞ YAPILMAZ" in EVET,
     "I-03: %s · kapanış uyarısı: %s"
     % ("I-03" in EVET, "KAPANIŞ YAPILMAZ" in EVET))


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BG-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
