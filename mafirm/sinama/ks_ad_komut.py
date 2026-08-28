#!/usr/bin/env python3
"""KÖR SINAMA AD — komutların BAŞKA bileşenler hakkındaki iddiaları.

§15 dokuz komut kurar ve her biri başka bileşenlere ATIFTA BULUNUR:
"`spa-inceleme` becerisindeki SEKİZ ADIMLI sırayı uygula", "`kurul-notu`
becerisindeki BEŞ BÖLÜMLÜ sırayı uygula", "tarih ALTI AYDAN eskiyse bayat".

Bu cümleler bugün doğrudur. Hiçbiri kontrol edilmiyor.

Bu, kitapta ve bu raporda defalarca bulduğum sınıfın ta kendisidir: §9'un
"10 beceri" beklentisi §14 onbirinciyi ekleyince bayatladı; bu raporun "on üç
beyan" satırı gerçek on birken yazılıydı; F matrisi üç kuralda "mekanizma yok"
diyordu ve üçünün de mekanizması vardı. EL YAZISI BİR SAYI, ÖLÇTÜĞÜ ŞEYDEN
BAĞIMSIZ YAŞAR.

Bu takım komut içeriğinde CANLI bir kusur bulmadı — bulduğu şey, hiçbir
şeyin bu iddiaları koruMADIĞIdır. Sağlam olanı ölçmek de bir sonuçtur;
ölçülmeyen sağlamlık, yarın sessizce bozulur.
"""
import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
KOMUT = os.path.join(KOK, ".claude/commands")
BECERI = os.path.join(KOK, ".claude/skills")
sonuclar = []

SAYI = {"bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6,
        "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10, "on bir": 11,
        "on iki": 12, "on beş": 15}


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def oku(p):
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


KOMUTLAR = {os.path.basename(f)[:-3]: oku(os.path.join(KOMUT, f))
            for f in sorted(os.listdir(KOMUT))} if os.path.isdir(KOMUT) else {}

# --- AD-01 · komutun bir beceri hakkındaki SAYISAL iddiası doğru mu ---
# "`<beceri>` becerisindeki <SAYI> <birim>li sırayı uygula"
# Türkçe ünlü uyumu: adımLI, bölümLÜ, alanLI. İlk sürüm yalnızca `l[ıi]`
# arıyordu ve "beş bölümlü" iddiasını SESSİZCE atlıyordu — yani iki iddiadan
# birini doğrulayıp "doğrulandı" diyordu. Kapsadığını sanan bir dedektör,
# kapsamadığını söylemez; bu, iki harfli takım adı kusurunun Türkçe hâli.
IDDIA = re.compile(
    r"`([a-z-]+)`\s+becerisindeki\s+([a-zçğıöşü ]+?)\s+"
    r"(adım|bölüm|alan|madde|başlık)l[ıiuü]",
    re.I)
yanlis, dogrulanan = [], []
for ad, metin in KOMUTLAR.items():
    for beceri, sayi_sozu, birim in IDDIA.findall(metin):
        n = SAYI.get(sayi_sozu.strip().lower())
        yol = os.path.join(BECERI, beceri, "SKILL.md")
        if n is None or not os.path.exists(yol):
            yanlis.append("%s: '%s' çözülemedi (%s)" % (ad, sayi_sozu, beceri))
            continue
        gercek = len(re.findall(r"^\d+\.", oku(yol), re.M))
        if gercek != n:
            yanlis.append("%s: %s becerisi için '%s %s' diyor, gerçek %d"
                          % (ad, beceri, sayi_sozu, birim, gercek))
        else:
            dogrulanan.append("%s→%s=%d" % (ad, beceri, n))
vaka("AD-01", "komutların becerilere dair sayısal iddiaları doğru",
     not yanlis, "; ".join(yanlis) if yanlis
     else "%d sayısal iddia doğrulandı: %s"
          % (len(dogrulanan), ", ".join(dogrulanan)))

# --- AD-02 · komutun andığı her beceri/ajan gerçekten var -------------
mevcut_beceri = set(os.listdir(BECERI)) if os.path.isdir(BECERI) else set()
ajan_dizin = os.path.join(KOK, ".claude/agents")
mevcut_ajan = {a[:-3] for a in os.listdir(ajan_dizin)} \
    if os.path.isdir(ajan_dizin) else set()
kayip = []
for ad, metin in KOMUTLAR.items():
    for b in re.findall(r"`([a-z-]+)`\s+becerisi", metin):
        if b not in mevcut_beceri:
            kayip.append("%s -> beceri %s" % (ad, b))
    for a in re.findall(r"`([a-z-]+)`\s+alt\s+ajan", metin):
        if a not in mevcut_ajan:
            kayip.append("%s -> ajan %s" % (ad, a))
vaka("AD-02", "komutların andığı her beceri ve ajan var",
     not kayip, "; ".join(kayip) if kayip
     else "%d komut tarandı, kayıp atıf yok" % len(KOMUTLAR))

# --- AD-03 · bayatlık eşiği komut düzyazısı ile kapı sabiti aynı mı ---
_sp = importlib.util.spec_from_file_location(
    "kapi_ad", os.path.join(KOK, ".claude/hooks/kapi.py"))
_k = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(_k)
ay_iddia = []
for ad, metin in KOMUTLAR.items():
    for sayi_sozu in re.findall(r"([a-zçğıöşü]+)\s+aydan\s+eski", metin, re.I):
        n = SAYI.get(sayi_sozu.lower())
        if n is None:
            continue
        gun = n * 30.44
        ay_iddia.append((ad, n, gun))
sapan_ay = [("%s: '%d ay' (~%d gün) ama BAYAT_GUN=%d"
             % (a, n, g, _k.BAYAT_GUN))
            for a, n, g in ay_iddia if abs(g - _k.BAYAT_GUN) > 20]
vaka("AD-03", "komutun bayatlık tanımı kapının sabitiyle uyuşuyor",
     not sapan_ay, "; ".join(sapan_ay) if sapan_ay
     else "%d ay iddiası, BAYAT_GUN=%d ile uyumlu"
          % (len(ay_iddia), _k.BAYAT_GUN))

# --- AD-04 · müvekkile giden komutlar §0 sözleşmesini emrediyor -------
# Muafiyet BEYAN edilir ve AD-05'te kapıyla sınanır (U-10/U-11 deseni).
SON = ("Şimdi ne yapılmalı", "Yetkili avukat görüşü gereken konular")
MUAF = {"denetim": "mühendislik çıktısı: denetim satırlarını raporlar",
        "esik-denetle": "bakım çıktısı: eşik tablosu üretir, müvekkile gitmez"}
eksik = []
for ad, metin in sorted(KOMUTLAR.items()):
    if ad in MUAF:
        continue
    duz = re.sub(r"\s+", " ", metin)
    yok = [b for b in SON if b not in duz]
    if yok:
        eksik.append("%s (%s)" % (ad, " + ".join(yok)))
vaka("AD-04", "müvekkile giden her komut §0 çıktı sözleşmesini emrediyor",
     not eksik, "; ".join(eksik) if eksik
     else "%d komut (%d muaf: %s)"
          % (len(KOMUTLAR) - len(MUAF), len(MUAF),
             ", ".join("%s — %s" % kv for kv in sorted(MUAF.items()))))

# --- AD-05 · muafiyet iddiası KAPIYLA sınanıyor ----------------------
# Muaf bir komutun belgelediği çıktı biçimi kapsam kapısını ateşlememeli.
ORNEK = {"denetim": "12 kontrol çalıştı, 11 geçti. Güvenilmeyen dosya: yok.\n",
         "esik-denetle": "3 eşik kontrol edildi, 1 bayat. Bayat dosya: "
                         "birimler/rekabet/yontem/tr-esikler.md\n"}
ates = []
for ad, ornek in sorted(ORNEK.items()):
    b = _k.kapi_kapsam(ornek)
    if b:
        ates.append("%s -> %s" % (ad, b[0]))
vaka("AD-05", "muaf komutların belgelenen çıktısı kapsam kapısını ateşlemiyor",
     not ates, "; ".join(ates) if ates
     else "%d muaf komutun örnek çıktısı da kapıdan geçiyor" % len(ORNEK))

# --- AD-06 · dışarı yetkili ajan dağıtan komut sır sınırını yazıyor ---
RISKLI_AJAN = set()
for a in sorted(mevcut_ajan):
    m = oku(os.path.join(ajan_dizin, a + ".md"))
    t = re.search(r"^tools:\s*(.+)$", m, re.M)
    if t and ({"Bash", "WebSearch", "WebFetch"} & {x.strip() for x in
                                                   t.group(1).split(",")}):
        RISKLI_AJAN.add(a)
sinirsiz = []
for ad, metin in sorted(KOMUTLAR.items()):
    dagitilan = {a for a in re.findall(r"`([a-z-]+)`\s+alt\s+ajan", metin)}
    if dagitilan & RISKLI_AJAN and not re.search(
            r"§6|kural 6|sır|soyutla|müvekkil ad", metin, re.I):
        sinirsiz.append("%s (%s)" % (ad, ", ".join(sorted(dagitilan & RISKLI_AJAN))))
vaka("AD-06", "riskli ajan dağıtan her komut sır sınırını yazıyor",
     not sinirsiz, "; ".join(sinirsiz) if sinirsiz
     else "riskli ajan (%s) dağıtan komutların hepsi sınırı yazıyor"
          % ", ".join(sorted(RISKLI_AJAN)))


BEKLENEN_VAKA = 6


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AD-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AD — komutların başka bileşenlere dair iddiaları")
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
