"""Beyan edilmiş taban — XFAIL / BEKLENMEDİK GEÇİŞ mantığı.

Neden var: her koşumda sabit sayıda kırmızı gösteren bir sınama takımı,
okuyucusuna kırmızıyı görmezden gelmeyi öğretir. Bu, kitabın D takımında
bulunan kusurunun aynadaki hâlidir — hep yeşil gösteren bir denetim de, hep
kırmızı gösteren bir takım da bilgi taşımaz.

Çözüm: bilinen ve gerekçeli her başarısızlık beklenen.json'da BEYAN EDİLİR.

  BEKLENEN     beyan edilmiş, hâlâ başarısız  -> sinyal değil
  KALDI        beyan EDİLMEMİŞ başarısızlık   -> gerçek sinyal (regresyon)
  BEKLENMEDİK  beyan edilmiş ama GEÇİYOR      -> gerçek sinyal (ya kusur
               GEÇİŞ                             düzeldi ve beyan bayat, ya da
                                                 sınama çürüdü)
"""
import json
import os

_YOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beklenen.json")

try:
    with open(_YOL, encoding="utf-8") as f:
        _B = json.load(f)
except OSError:
    _B = {"vakalar": {}, "kabuk_takimlari": {}}

VAKALAR = _B.get("vakalar", {})


def durum(kod, gecti):
    """(etiket, sinyal_mi) döner."""
    beyanli = kod in VAKALAR
    if gecti and beyanli:
        return "BEKLENMEDİK GEÇİŞ", True     # beyan bayat ya da sınama çürüdü
    if gecti:
        return "GEÇTİ", False
    if beyanli:
        return "BEKLENEN", False             # bilinen, gerekçeli
    return "KALDI", True                     # regresyon


def neden(kod):
    v = VAKALAR.get(kod)
    return v["neden"] if v else ""


def sinif(kod):
    v = VAKALAR.get(kod)
    return v["sinif"] if v else ""


def ozet(sonuclar):
    """[(kod, gecti)] -> (sinyal_sayisi, sayim sözlüğü)"""
    sayim = {"GEÇTİ": 0, "BEKLENEN": 0, "KALDI": 0, "BEKLENMEDİK GEÇİŞ": 0}
    sinyal = 0
    for kod, gecti in sonuclar:
        et, s = durum(kod, gecti)
        sayim[et] += 1
        sinyal += 1 if s else 0
    return sinyal, sayim
