#!/usr/bin/env python3
"""KÖR SINAMA BJ — iki yöntem dosyası aynı işleme farklı hukuki nitelik veriyor.

Yönelim (elli yedinci tur). Elli dördüncü–elli altıncı turlar rekabet
biriminde bir değişmez kurdu: **kayıtlı bir açık soru cevabı değiştiriyorsa,
çıktıda görünmelidir.** Aynı soru şirketler birimine hiç sorulmadı.

Sorulunca çıkan şey daha ağırdı. İki yöntem dosyası, TTK m.595/2 genel kurul
onayına **birbirini dışlayan** hukuki nitelikler veriyor:

  birimler/tr-sirketler/yontem/pay-devri.md
      "onay, devri tamamlayan KURUCU işlemdir"          → devir onayla OLUR
  birimler/sinir-otesi/yontem/mimari.md
      "Kapanış öncesi koşullar" listesinin 5. maddesi   → devirden ÖNCE gelen
                                                           bir KOŞUL

İkisi bir arada olamaz. Fark, kapanış sırasını ve nihai tarih (long-stop)
hesabını değiştirir: kurucu işlemse kapanış GÜNÜ yapılır ve devir onayla
tamamlanır; koşulsa kapanıştan ÖNCE tamamlanmış olmalıdır.

Ve hiçbiri ötekine atıf yapmıyor, hiçbiri U-02'yi anmıyor. Bir hukukçu
hangisini açarsa onun cevabını doğru sanar. Rekabet birimindeki kusurun
aynısı — açık soru, karara varılan yerde görünmüyor — ama burada iki dosya
birbirini POZİTİF OLARAK yalanlıyor.

Bu takım hangi okumanın doğru olduğunu SÖYLEMEZ: nitelendirme bir hukuki
karardır ve kural 9 uyarınca insana aittir. Sınadığı şey, çelişkinin iki
tarafta da GÖRÜNÜR olup olmadığıdır.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def oku(*p):
    y = os.path.join(_KOK, *p)
    return io.open(y, encoding="utf-8").read() if os.path.exists(y) else ""


def duz(t):
    """Markdown vurgusu ve satır kaydırması sözcükleri ayırır: kaynakta
    'tamamlayan **kurucu** işlemdir' yazıyor ve 'kurucu işlem' araması
    HİÇ eşleşmiyordu. Aynı tuzak bu incelemede defalarca çıktı."""
    return re.sub(r"\s+", " ", re.sub(r"[*`_]+", "", t))


PAY_HAM = oku("birimler", "tr-sirketler", "yontem", "pay-devri.md")
MIM_HAM = oku("birimler", "sinir-otesi", "yontem", "mimari.md")
PAY, MIM = duz(PAY_HAM), duz(MIM_HAM)


def uyarisiz(ham):
    """AÇIK SORU bloklarını çıkar.

    [Kırk birinci turun sınıfı] Bu turda eklenen uyarı bloğu, çelişkiyi
    ANLATIRKEN çelişkinin sözcüklerini de içeriyor. Onları saymak, kendi
    yamamı kitabın metni sanmaktır: çelişkinin bir ucu kaldırılsa bile
    ölçüt uyarının içindeki kopyayı bulup "çelişki duruyor" derdi."""
    return duz(re.sub(r">\s*\[AÇIK SORU.*?\]", " ", ham, flags=re.S))


PAY_SAF, MIM_SAF = uyarisiz(PAY_HAM), uyarisiz(MIM_HAM)

# --- çelişkinin iki ucu -------------------------------------------------
KURUCU = re.compile(r"kurucu\s+işlem", re.I)
KOSUL_BASLIK = re.compile(r"Kapanış öncesi koşullar(.*?)(?=## |\Z)", re.S)
# [BG-01'in dersi] "U-02 metinde geçiyor mu" diye sormak yetmez: uyarı
# başlığı tamamen silindiğinde bile kimlik kaynak atfında geçmeye devam
# ediyordu ve vaka yeşil kalıyordu. Ölçüt, BELİRGİN işareti ister.
ACIK_SORU = re.compile(r"\[AÇIK SORU[^\]]*U-02", re.S)


def kosul_maddeleri():
    m = KOSUL_BASLIK.search(MIM_SAF)
    return m.group(1) if m else ""


_kosulda_gk = bool(re.search(r"genel kurul onayı", kosul_maddeleri(), re.I))
_kurucu_gk = bool(KURUCU.search(PAY_SAF))

# --- BJ-01 · çelişki gerçekten duruyor (ölçüt vakum değil) -------------
# Çelişki ortadan kalkarsa bu vaka BEKLENMEDİK GEÇİŞ verir ve beyanın
# bayatladığını söyler — yani biri düzeltilmişse fark edilir.
vaka("BJ-01", "iki yöntem dosyası m.595/2'ye farklı nitelik veriyor (çelişki duruyor)",
     _kurucu_gk and _kosulda_gk,
     "pay-devri 'kurucu işlem': %s · mimari kapanış koşulu listesinde: %s"
     % (_kurucu_gk, _kosulda_gk))

# --- BJ-02 · pay-devri.md açık soruyu anıyor ---------------------------
vaka("BJ-02", "pay-devri.md nitelendirmenin açık olduğunu yazıyor",
     bool(ACIK_SORU.search(PAY)),
     "açık soru işareti: %s" % bool(ACIK_SORU.search(PAY)))

# --- BJ-03 · mimari.md açık soruyu anıyor ------------------------------
vaka("BJ-03", "mimari.md nitelendirmenin açık olduğunu yazıyor",
     bool(ACIK_SORU.search(MIM)),
     "açık soru işareti: %s" % bool(ACIK_SORU.search(MIM)))

# --- BJ-04 · her iki uyarı ÖTEKİ dosyaya atıf yapıyor ------------------
# Bir çelişkinin yarısını görmek, çelişkiyi görmek değildir.
_pay_atif = "mimari.md" in PAY or "sinir-otesi" in PAY
_mim_atif = "pay-devri.md" in MIM or "tr-sirketler" in MIM
vaka("BJ-04", "her iki uyarı çelişkinin öteki ucunu gösteriyor",
     _pay_atif and _mim_atif,
     "pay-devri → mimari: %s · mimari → pay-devri: %s" % (_pay_atif, _mim_atif))

# --- BJ-05 · sistem nitelendirmeyi KENDİ ÇÖZMÜYOR (§9) ----------------
# Uyarı, kararı insana bırakmalı; bir tarafı "doğru" ilan eden bir metin
# hukuki nitelendirme yapmış olur.
KARAR_VERMIS = re.compile(r"doğrusu (kurucu|koşul)|kesin olarak (kurucu|koşul)|"
                          r"bu tartışma çözülmüştür", re.I)
_karar = [ad for ad, m in (("pay-devri", PAY), ("mimari", MIM))
          if KARAR_VERMIS.search(m)]
vaka("BJ-05", "hiçbir dosya nitelendirmeyi kendi kararına bağlamıyor (§9)",
     not _karar, "karara varan dosya: %s" % (_karar or "yok"))


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BJ-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
