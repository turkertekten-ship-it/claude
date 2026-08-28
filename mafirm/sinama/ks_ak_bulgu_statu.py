#!/usr/bin/env python3
"""KÖR SINAMA AK — ENGELLEYİCİ OLMAYAN bulgular da doğrulanabilir miydi.

Yirmi sekizinci tur, çalıştığı KAYITLI olan bir kanalın üç ENGELLEYİCİ bulgu
için yirmi yedi tur kullanılmadığını buldu ve AJ-02 bunu artık her koşumda
soruyor. Ama AJ-02 yalnızca ENGELLEYİCİ satırlara bakıyor.

Kayıtta dokuz bulgu daha var ve hepsi "hayır" (engelleyici değil) diye
işaretli. **Engelleyici olmamak, doğrulanmış olmak demek değildir.** Bir
raporun içinde duran her açık iddia, okuyucunun güveneceği bir iddiadır;
"engelleyici değil" yalnızca denetimi kırmızıya çevirmediğini söyler.

Bu turda dördü doğrulandı ve üçü YETKİLİ KAYNAĞINDAN okundu:
  · G-01 courtlistener AGPL — deponun kendi README'si
  · G-02 diff-match-patch 2024-08-05'te arşivlendi — depo sayfası
  · G-03 opensanctions verisi CC BY-NC 4.0 — ticari kullanım AÇIKÇA YASAK
  · I-04 m.16 alt sınırı 302.484,86 TL (2026/1 sayılı Tebliğ)

Ayrım önemli: G-01..G-03 **depo olgusudur** ve yetkili kaynağı depodur —
erişildi, okundu, kapatılabilir. I-01..I-03 **hukuk metnidir**, yetkili
kaynağı birincil mevzuattır, engellidir ve düzeltmesi §9 uyarınca insana
aittir. Bir bulguyu kapatmak, KANITIN TÜRÜNE bakmayı gerektirir.
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


BULGU = io.open(os.path.join(KOK, "hafiza/dogrulama-bulgulari.md"),
                encoding="utf-8").read()
# [AE-01] İki harfli kimlik. AE takımı bu satırı, yazıldığı TURDA
# yakaladı — sınıf taraması tam da bunun için var.
SATIR = re.findall(r"^([A-Z]{1,2}-\d+) \| ([^|]+) \|[^|]*\| (.+)$",
                   BULGU, re.M)

# --- AK-01 · her bulgu bir STATÜ taşıyor -----------------------------
GECERLI = ("ENGELLEYICI", "DOĞRULANDI", "hayır")
kotu = [k for k, st, _g in SATIR
        if not any(st.strip().startswith(g) for g in GECERLI)]
vaka("AK-01", "her bulgu tanınan bir statü taşıyor",
     bool(SATIR) and not kotu,
     "; ".join(kotu) if kotu else "%d bulgu: %s"
     % (len(SATIR), ", ".join("%s=%s" % (k, st.strip().split()[0])
                              for k, st, _g in SATIR)))

# --- AK-02 · DOĞRULANDI diyen her bulgu KAYNAK gösteriyor ------------
kaynaksiz = [k for k, st, g in SATIR
             if st.strip().startswith("DOĞRULANDI")
             and not re.search(r"Kaynak:|sayılı Tebliğ|README|depo sayfası", g)]
vaka("AK-02", "doğrulanmış her bulgu kaynağını gösteriyor",
     not kaynaksiz, "; ".join(kaynaksiz) if kaynaksiz
     else "%d doğrulanmış bulgunun hepsi kaynaklı"
          % sum(1 for _k, st, _g in SATIR if st.strip().startswith("DOĞRULANDI")))

# --- AK-03 · DEPO olgusu, deposundan doğrulanmış olmalı --------------
# Kanıtın TÜRÜ önemlidir: bir depo olgusunun yetkili kaynağı depodur;
# ikincil bir yazı değil.
depo_bulgu = [(k, g) for k, st, g in SATIR if k.startswith("G-")]
zayif = [k for k, g in depo_bulgu
         if "DOĞRULANDI" in g and "github.com" not in g]
vaka("AK-03", "depo olgusu deposundan doğrulanmış",
     not zayif, "; ".join(zayif) if zayif
     else "%d depo bulgusunun hepsi github kaynaklı" % len(depo_bulgu))

# --- AK-04 · HUKUK METNİ bulgusu ikincil kaynakla KAPATILMAMIŞ -------
# I-01..I-03 ikincil kaynakla güçlendi ama kapatılamaz; kapatılmışsa
# yöntem hatasıdır.
hukuk = [(k, st, g) for k, st, g in SATIR if k.startswith("I-0")
         and k in ("I-01", "I-02", "I-03")]
kapatilmis = [k for k, st, _g in hukuk if not st.strip().startswith("ENGELLEYICI")]
vaka("AK-04", "hukuk metni bulgusu ikincil kaynakla kapatılmamış",
     bool(hukuk) and not kapatilmis,
     ("statüsü düşürülmüş: %s" % ", ".join(kapatilmis)) if kapatilmis
     else "%d hukuk bulgusunun hepsi ENGELLEYİCİ" % len(hukuk))

# --- AK-05 · çalışan kanalla doğrulanabilir bulgu ASKIDA kalmamış ----
# Bir depo olgusu, depo erişilebilirken "hayır" diye bekletiliyorsa, bu
# yirmi sekizinci turun kusurunun tekrarıdır: kanal var, kullanılmamış.
bekleyen = [k for k, st, g in SATIR
            if k.startswith("G-") and st.strip() == "hayır"]
vaka("AK-05", "deposu erişilebilir hiçbir bulgu doğrulanmamış bekletilmiyor",
     not bekleyen,
     ("BEKLETİLEN: %s — kanal çalışıyor, bulgu doğrulanmamış" % ", ".join(bekleyen))
     if bekleyen else "bekleyen depo bulgusu yok")


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AK-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AK — engelleyici olmayan bulgular da doğrulanabilir miydi")
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
