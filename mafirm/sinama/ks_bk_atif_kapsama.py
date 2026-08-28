#!/usr/bin/env python3
"""KÖR SINAMA BK — hüküm atıflarının kapsaması, beyanla değil KEŞİFLE.

Yönelim (elli sekizinci tur). BJ bir çelişkiyi buldu — ama ELLE seçilmiş
bir çelişkiyi. Aynı sorunun başka hükümlerde de olup olmadığını hiçbir şey
sormuyordu. Bu, bu incelemenin üçüncü sınıfıdır: elle yazılmış liste,
ölçtüğü şeyden sürüklenir.

Keşif yapıldı: yöntem dosyalarında BİRDEN FAZLA dosyada nitelendirilen üç
hüküm atfı var.

    TTK m.595/2   pay-devri.md · mimari.md      -> BJ'nin bulduğu çelişki
    TTK m.499     pay-devri.md · kapsam.md      -> iki dosya UYUŞUYOR
    II-26.1       pay-alim-teklifi.md · INDEX   -> ikincisi yalnızca işaretçi

Çelişki yalnızca birindeydi. Ama ikinci bir kusur çıktı: **I-05**, TTK
m.499 kaydının ve m.595/1 noter onayının nitelendirilmesini yetkili avukat
görüşü gerektiren konular arasında sayıyor — ve bu, o nitelendirmeyi YAPAN
yöntem dosyasında hiç anılmıyordu. Elli dört–elli yedinci turların sınıfı,
beşinci kez: açık soru, kararın verildiği yerde görünmüyor.

Bu takım kapsamayı kalıcı kılar: birden fazla dosyada nitelendirilen her
hüküm beyan edilmiş olmalı, ve nitelendirmesi açık soru olarak kaydedilmiş
her hüküm, o nitelendirmeyi yapan dosyada işaretli olmalıdır.
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


def duz(t):
    return re.sub(r"\s+", " ", re.sub(r"[*`_]+", "", t))


def belgeler():
    d = {}
    for kok, _, fs in os.walk(os.path.join(_KOK, "birimler")):
        for f in fs:
            if f.endswith(".md"):
                y = os.path.join(kok, f)
                d[os.path.relpath(y, _KOK)] = duz(
                    io.open(y, encoding="utf-8").read())
    return d


BELGE = belgeler()
ATIF = re.compile(r"(TTK m\.\s*\d+(?:/\d+)?|II-26\.1|4054[^,.;]{0,20}m\.\s*\d+)",
                  re.I)

_yer = {}
for _y, _t in BELGE.items():
    for _m in ATIF.finditer(_t):
        _yer.setdefault(re.sub(r"\s+", " ", _m.group(1)).lower(), set()).add(_y)

COKLU = {k: v for k, v in _yer.items() if len(v) > 1}

# --- BEYAN: birden fazla dosyada geçen her hüküm ve durumu -------------
# Her satır: hüküm -> (durum, gerekçe). Yeni bir çoklu atıf, buraya
# girmeden BK-01'i kırar.
BEYAN = {
    "ttk m.595/2": ("ÇELİŞKİ · BJ ile sınanıyor",
                    "pay-devri kurucu işlem der, mimari kapanış koşulu sayar; "
                    "iki uçta da AÇIK SORU işareti var, karar insana bırakıldı"),
    "ttk m.499": ("UYUŞUYOR",
                  "pay-devri ve kapsam, kaydın şirkete karşı hüküm ifade "
                  "ettiğini aynı biçimde yazıyor; nitelendirme sorusu I-05 "
                  "olarak pay-devri.md'de işaretli"),
    "ii-26.1": ("İŞARETÇİ",
                "ikinci dosya bir INDEX girdisidir, nitelendirme yapmaz"),
}

_beyansiz = sorted(set(COKLU) - set(BEYAN))
_bayat = sorted(set(BEYAN) - set(COKLU))

# --- BK-01 · her çoklu atıf beyan edilmiş ------------------------------
vaka("BK-01", "birden fazla dosyada geçen her hüküm atfı beyanlı",
     not _beyansiz and not _bayat,
     "%d çoklu atıf · beyansız: %s · bayat beyan: %s"
     % (len(COKLU), _beyansiz or "yok", _bayat or "yok"))

# --- BK-02 · nitelendirmesi açık soru olan hüküm, dosyasında işaretli --
# I-05 ve U-02: kayıtta nitelendirme sorusu olarak duruyorlar.
ACIK = {
    "I-05": ("birimler/tr-sirketler/yontem/pay-devri.md", "499"),
    "U-02": ("birimler/tr-sirketler/yontem/pay-devri.md", "595/2"),
}
_isaretsiz = []
for _kod, (_dosya, _hukum) in ACIK.items():
    _t = BELGE.get(_dosya, "")
    if not re.search(r"\[AÇIK SORU[^\]]*%s" % re.escape(_kod), _t):
        _isaretsiz.append("%s (%s)" % (_kod, _dosya))
vaka("BK-02", "nitelendirmesi açık soru olan her hüküm dosyasında işaretli",
     not _isaretsiz, "işaretsiz: %s" % (_isaretsiz or "yok"))

# --- BK-03 · keşif vakum değil ----------------------------------------
vaka("BK-03", "keşif yöntem dosyalarını ve atıfları gerçekten buluyor",
     len(BELGE) >= 20 and len(_yer) >= 6 and len(COKLU) >= 3,
     "%d belge · %d ayrı hüküm atfı · %d çoklu"
     % (len(BELGE), len(_yer), len(COKLU)))

# --- BK-04 · hiçbir dosya açık nitelendirmeyi kendi çözmüyor (§9) -----
KARAR = re.compile(r"bu tartışma çözülmüştür|kesin olarak (kurucu|açıklayıcı)|"
                   r"doğrusu (kurucu|açıklayıcı|koşul)", re.I)
_karar = sorted(y for y, t in BELGE.items() if KARAR.search(t))
vaka("BK-04", "hiçbir yöntem dosyası açık nitelendirmeye kendi karar vermiyor",
     not _karar, "karara varan: %s" % (_karar or "yok"))

# --- BK-05 · her AÇIK SORU işareti kaynağını gösteriyor ---------------
# Kaynaksız bir uyarı, okuyucunun doğrulayamayacağı bir uyarıdır (kural 1).
_kaynaksiz = []
for _y, _t in BELGE.items():
    # [AV-02] Pencere yerine YAPISAL eşleşme: blok zaten "]" ile biter,
    # sayısal bir sınır koymak gereksiz bir pencere yaratır ve pencereler
    # bu incelemede defalarca komşuyu kanıt saydı.
    for _m in re.finditer(r"\[AÇIK SORU([^\]]*)\]", _t):
        if "dogrulama-bulgulari.md" not in _m.group(1):
            _kaynaksiz.append(_y)
vaka("BK-05", "her açık soru işareti kayıt dosyasına atıf yapıyor",
     not _kaynaksiz, "kaynaksız uyarı taşıyan dosya: %s"
     % (sorted(set(_kaynaksiz)) or "yok"))


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BK-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
