#!/usr/bin/env python3
"""KÖR SINAMA AU — epilog kontrollerinin kendi sınaması.

Yönelim (otuz dokuzuncu tur). Otuz sekizinci tur denetimin 26 kontrolüne
"her kontrolün kanıtlanmış bir mutasyonu olmalı" ölçütünü uyguladı. Aynı
ölçüt bir katman YUKARIDA hiç uygulanmamıştı: hepsi.sh'in epilogu dört
kontrol taşıyor ve hiçbiri mutasyonla sınanmamıştı.

Sebebi teknikti ve dürüstçe adlandırılmalı: bir epilog kontrolünü kırmak,
kırk üç takımın tamamını koşturmayı gerektiriyordu (~60 sn). Dört kontrol
için dört tam koşum — dört dakika. Ölçüt uygulanmadı çünkü PAHALIYDI, ve
"pahalı olduğu için ölçmedim" bu incelemenin baştan beri kabul etmediği
gerekçedir.

Çözüm kontrolü zayıflatmak değil, ONU SAF BİR FONKSİYONA ÇEVİRMEK oldu:
`sinama/epilog.py` (günlük, taban, rapor) alır, uyarı üretir. hepsi.sh hâlâ
onu tam günlüğü bilen tek yerden çağırır — katman korunur — ama artık
sentetik bir günlükle milisaniyede sınanabilir. Sınanan şey bir KOPYA
değildir: üretimde koşan kodun kendisidir (AU-06 bunu sağlar).
"""
import importlib.util
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_S = os.path.join(_KOK_COZ, "sinama")

_spec = importlib.util.spec_from_file_location(
    "epilog_au", os.path.join(_S, "epilog.py"))
epilog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(epilog)

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


# Sentetik günlük: gerçek biçimi taşır, gerçek koşum gerektirmez.
TEMIZ_GUNLUK = (
    "GEÇTİ A-01   bir vaka\n"
    "BEKLENEN A-07   eski api\n"
    "        beklenen : bildirime tabi (B)\n"
    "----------------------------------------\n"
    "12 vaka · 11 geçti · 1 beklenen · 0 SİNYAL\n"
)
TEMIZ_BEYAN = {"A-07": {"sinif": "eski-api-kaydi", "neden": "kayıt",
                        "belirti": "beklenen : bildirime tabi (B)"}}
TEMIZ_RAPOR = "**012\n"     # koşumun gerçek toplamı 12


def _uyari(gunluk=None, beyan=None, rapor=None):
    _c, n = epilog.calistir(gunluk if gunluk is not None else TEMIZ_GUNLUK,
                            beyan if beyan is not None else TEMIZ_BEYAN,
                            rapor if rapor is not None else TEMIZ_RAPOR)
    return n, "\n".join(_c)


# --- AU-00 · taban: temiz girdi SESSİZ olmalı ------------------------
# Kırmızı bir tabana karşı okunan mutasyon hiçbir şey kanıtlamaz (D'nin
# kuralı). Önce tabanın sessiz olduğu gösterilir.
_taban_n, _taban_c = _uyari()
vaka("AU-01", "temiz günlük ve güncel rapor hiçbir uyarı üretmiyor",
     _taban_n == 0, "taban uyarısı: %d · %s" % (_taban_n, _taban_c[:90]))

# --- AU-02 · beyanlı vaka koşumda YOKSA uyarır ----------------------
_n, _ = _uyari(beyan=dict(TEMIZ_BEYAN, **{"ZZ-99": {"belirti": "x"}}))
vaka("AU-02", "beyanlı olup koşumda görünmeyen vaka uyarı üretiyor",
     _n == 1, "uyarı sayısı: %d (beklenen 1)" % _n)

# --- AU-03 · belirti KAYDIĞINDA uyarır ------------------------------
_kaymis = {"A-07": dict(TEMIZ_BEYAN["A-07"],
                        belirti="tamamen alakasız kelimeler burada duruyor")}
_n, _ = _uyari(beyan=_kaymis)
vaka("AU-03", "beyan edilen belirti canlı belirtiden kayınca uyarı üretiyor",
     _n == 1, "uyarı sayısı: %d (beklenen 1)" % _n)

# --- AU-04 · belirtisiz beyan uyarır --------------------------------
_bsz = {"A-07": {"sinif": "x", "neden": "y"}}
_n, _ = _uyari(beyan=_bsz)
vaka("AU-04", "belirti kaydı olmayan beyan uyarı üretiyor",
     _n == 1, "uyarı sayısı: %d (beklenen 1)" % _n)

# --- AU-05 · raporun vaka sayısı bayatsa uyarır ---------------------
_n, _ = _uyari(rapor="**999\n")
vaka("AU-05", "raporun el yazısı vaka sayısı bayatsa uyarı üretiyor",
     _n == 1, "uyarı sayısı: %d (beklenen 1)" % _n)

# --- AU-06 · YANLIŞ POZİTİF: anlatıdaki tarihsel sayılar susmalı ----
# Bu turda düştüğüm tuzak: bash sürümünden port ederken `\*\*[0-9]{3}$`
# çapasını düşürdüm ve ölçüt raporun ANLATISINDAKİ her kalın üç haneli
# sayıyı (300, 302, 330, 690) bayat sayım sandı. Yanlış pozitif üreten bir
# kontrol, bir gün içinde kapatılır.
_anlati = ("Koşum **012 vaka taşıyor.\n"
           "Yirmi dokuzuncu turda **300 vakaydı; otuzuncu turda **302 oldu.\n"
           "AF bağımsızken 853, yönlendirme içinde **690 satır görüyordu.\n")
_n, _c = _uyari(rapor=_anlati)
vaka("AU-06", "raporun anlatısındaki tarihsel sayılar bayat sayım sayılmıyor",
     _n == 0, "uyarı: %d · %s" % (_n, _c[:120]))

# --- AU-07 · aynı kod yolu: hepsi.sh epilog.py'yi ÇAĞIRIYOR ---------
# Sınanan şey bir kopya olsaydı, bu takım hiçbir şey kanıtlamazdı.
# [yorum tuzağı · yine] İlk ölçüt "epilog.py" dizgesini METNİN HERHANGİ BİR
# YERİNDE arıyordu ve yamayı ANLATAN yorumda buluyordu: çağrı silindiği hâlde
# vaka yeşil kalıyordu. AN'de yorum, AM'de açıklama cümlesi, AE'de belge
# dizgesi, burada yine yorum. Ölçüt ÇAĞRININ KENDİSİNE bağlandı ve yorumlar
# metinden atıldı — bir şeyden söz etmek, o şeyi yapmak değildir.
_ham = io.open(os.path.join(_S, "hepsi.sh"), encoding="utf-8").read()
_hepsi = "\n".join(r for r in _ham.splitlines()
                   if not r.lstrip().startswith("#"))
_cagiriyor = re.search(r'python3\s+"\$S/epilog\.py"', _hepsi) is not None
_gomulu = "beyan = json.load" in _hepsi
vaka("AU-07", "hepsi.sh epilog kontrollerini epilog.py'den çağırıyor",
     _cagiriyor and not _gomulu,
     "çağırıyor=%s · gömülü kopya kaldı=%s" % (_cagiriyor, _gomulu))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 7


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AU-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
