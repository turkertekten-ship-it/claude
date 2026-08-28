#!/usr/bin/env python3
"""KÖR SINAMA O — sır kapısının KAÇIRMA yüzeyi.

B takımındaki her vaka bir hukukçunun gerçekten YAZACAĞI cümleydi. Ama sır
kapısı (işletim sözleşmesi §6) bir güvenlik denetimidir ve güvenlik denetimi
yalnızca iyi niyetli girdiyle sınanmaz.

Ve bu, kuramsal bir tehdit modeli değil: aşağıdaki üç yüzeyin üçü de KAZA
olarak oluşur. PDF ya da Word'den kopyala yapıştır rutin olarak yumuşak tire,
sıfır genişlikli karakter ve ayrışmış aksan üretir. Bir müvekkil kod adı
veri odası belgesinden kopyalanıp bir web aramasına yapıştırıldığında,
kapının onu görmesi gerekir.

Zaten §12'de aynı SINIFTAN bir kusur vardı ve raporun ikinci turunda
bulunmuştu: Python'un 'İ'.lower() ayrışması. Bu takım o sınıfın tamamını
tarar.
"""
import importlib.util
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

_yol = os.path.join(_KOK_COZ, ".claude/hooks/kapi.py")
_spec = importlib.util.spec_from_file_location("kapi_o", _yol)
kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapi)

sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def ateslendi(metin, kapi_adi="sir"):
    return kapi_adi in {a for a, _ in kapi.denetle(metin, disari=True)}


KOD_ADI = "Proje Şahin işlemin kod adıdır."
UNVAN = "Hedef Acme Gıda A.Ş. şirketidir."

# --- Taban: düz biçim yakalanmalı ---------------------------------------
vaka("O-01", "düz kod adı yakalanıyor", ateslendi(KOD_ADI))
vaka("O-02", "düz şirket unvanı yakalanıyor", ateslendi(UNVAN))

# --- Unicode ayrışması (NFD) — kopyala yapıştırın olağan ürünü ----------
vaka("O-03", "NFD ayrışmış kod adı yakalanıyor",
     ateslendi(unicodedata.normalize("NFD", KOD_ADI)),
     "Ş -> S + U+0327 birleşen çengel")
vaka("O-04", "NFD ayrışmış şirket unvanı yakalanıyor",
     ateslendi(unicodedata.normalize("NFD", UNVAN)),
     "A.Ş. -> A.S + U+0327")

# --- Görünmez karakterler ----------------------------------------------
vaka("O-05", "sıfır genişlikli boşluk (U+200B) atlatamıyor",
     ateslendi("Proje​ Şahin işlemin kod adıdır."))
vaka("O-06", "sıfır genişlikli birleştirici (U+200D) atlatamıyor",
     ateslendi("Proje Şa‍hin işlemin kod adıdır."))
vaka("O-07", "yumuşak tire (U+00AD) atlatamıyor",
     ateslendi("Proje Şa­hin işlemin kod adıdır."))
vaka("O-08", "sağdan sola işaretleyici (U+200F) atlatamıyor",
     ateslendi("Proje‏ Şahin işlemin kod adıdır."))

# --- Homoglifler --------------------------------------------------------
vaka("O-09", "Kiril 'о' ile yazılmış kod adı yakalanıyor",
     ateslendi("Prоje Şahin işlemin kod adıdır."))
vaka("O-10", "Kiril 'а' ile yazılmış unvan yakalanıyor",
     ateslendi("Hedef Аcme Gıda A.Ş. şirketidir."))
vaka("O-11", "Yunan 'ο' ile yazılmış kod adı yakalanıyor",
     ateslendi("Prοje Şahin işlemin kod adıdır."))

# --- Birleşik saldırı ---------------------------------------------------
vaka("O-12", "ayrışma + görünmez + homoglif birlikte",
     ateslendi(unicodedata.normalize(
         "NFD", "Prоje​ Şa­hin işlemin kod adıdır.")))

# --- NEGATİF KONTROLLER: aşırı normalleştirme yanlış pozitif üretmemeli --
vaka("O-13", "masum işlem metni SUSUYOR",
     not ateslendi("Kapanış öncesi koşullar sıralanır ve sahiplendirilir."))
vaka("O-14", "mevzuat metni SUSUYOR",
     not ateslendi("TTK madde 490 uyarınca nama yazılı paylar devredilebilir."))
vaka("O-15", "Türkçe aksanlı olağan cümle SUSUYOR",
     not ateslendi("Şirketin özkaynak yapısı ve kıdem yükü incelenmiştir."))
vaka("O-16", "yerel yazmada hiçbir şey ateşlemiyor (disari=False)",
     "sir" not in {a for a, _ in kapi.denetle(KOD_ADI, disari=False)},
     "sır kapısı yalnızca dışarı giden çağrıda ateşler — §12'nin kendi kuralı")

# --- Kapının kendi öz-sınaması hâlâ geçiyor mu -------------------------
vaka("O-17", "normalleştirme kapının öz-sınamasını bozmadı",
     kapi._selftest() == 0)


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
# Bu koruma on üçüncü turda eklendi ama YALNIZCA sonrasında yazılan
# takımlara; on beş takım korumasız kaldı. Geriye doldurma.
BEKLENEN_VAKA = 17


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("O-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))

    print("=" * 96)
    print("KÖR SINAMA O — sır kapısının kaçırma yüzeyi (Unicode)")
    print("=" * 96)
    kaldi = 0
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, sinyal = beklenen.durum(kod, gecti)
        if sinyal:
            kaldi += 1
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
