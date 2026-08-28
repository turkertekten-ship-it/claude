#!/usr/bin/env python3
"""KÖR SINAMA BB — sayıların zaman indisi.

Yönelim (kırk yedinci tur). Kırk altı tur DEPOYU sınadı. Okuyucunun açtığı
şey ise ARTIFACT'tir ve o, ölçülen sonuçların ELLE bakımı yapılan bir
sunumudur. Bu incelemenin en sık ikinci sınıfı tam olarak budur: **elle
yazılan sayı, ölçtüğü şeyden sürüklenir.**

Gözlem üç şey buldu:

  1. RAPOR.md'de "Dokuz takım, 96 vaka:" başlığı, altında 53 satırlık bir
     tablo taşıyor. Başlık birinci turda yazıldı; tablo kırk altı turda
     büyüdü. Başlık büyümedi.
  2. 96 sayısı tarihsel olarak da yanlış yerde: yamalar/DEGISIKLIKLER.md
     96'yı YAMALI koşuma, 85'i KİTABA SADIK koşuma yazıyor.
  3. Artifact'in girişi 96'yı "kelimesi kelimesine kuruldu" diye
     nitelenen — yani SADIK — koşuma bağlıyor. Sadık koşum 85'ti.

Üçüncüsü kırk altı tur boyunca neden hayatta kaldı: sayı rakamla değil,
**"doksan altı"** diye YAZIYLA yazılmış. `\\d+ vaka` arayan hiçbir ölçüt onu
göremez. Bu takım Türkçe sayı sözcüklerini de okur.

Kural: bir sayı ya ŞU ANDA ölçülebilen değere eşittir, ya da hangi koşuma
ait olduğunu SÖYLER. İndissiz bir tarihsel sayı, güncel bir iddiadan
ayırt edilemez.
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


def tr_kucult(s):
    """Türkçe-güvenli küçültme. Çıplak .lower() 'İ' harfini i+U+0307 yapar
    ve 'İki' sözlükte bulunamaz — bu takım ilk koşusunda tam olarak buna
    çarptı. AE-03'ün yasakladığı şey, onu yazan takımı da vurdu."""
    return s.replace("I", "ı").replace("İ", "i").lower()


# --- Türkçe sayı sözcükleri --------------------------------------------
BIRLER = {"bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6,
          "yedi": 7, "sekiz": 8, "dokuz": 9}
ONLAR = {"on": 10, "yirmi": 20, "otuz": 30, "kırk": 40, "elli": 50,
         "altmış": 60, "yetmiş": 70, "seksen": 80, "doksan": 90}
# Ek: Türkçe sayı sözcükleri EK ALIR ("on beşi", "doksan altısı"), ONLAR'sız
# tek başına gelir ("dokuz takım") ve YÜZLÜ olur ("üç yüz yetmiş yedi").
# İlk yazımda üçü de atlanmıştı. Yüzlüler mutasyonla yakalandı: "iki yüz
# vakayla sınandı" kaçtı — ve toplamlar tam olarak yüzlü sayılardır, yani
# delik ölçütün en çok gerektiği yerdeydi.
_EK = r"(?:[ıiuü]?[nmsz]?[ıiuü]?n?[ae]?|[ıiuü]?)"
KELIME = dict(BIRLER, **ONLAR)
KELIME["yüz"] = 100
KELIME["bin"] = 1000
_TOK = "|".join(sorted(KELIME, key=len, reverse=True))
DIZI = re.compile(r"\b(?:(?:%s)%s)(?:\s+(?:(?:%s)%s))*\b(?!\s*\.)"
                  % (_TOK, _EK, _TOK, _EK), re.I)
_BIR = re.compile(r"(%s)%s" % (_TOK, _EK), re.I)


def _degerle(kelimeler):
    toplam = kismi = 0
    for k in kelimeler:
        v = KELIME[k]
        if v == 100:
            kismi = (kismi or 1) * 100
        elif v == 1000:
            toplam += (kismi or 1) * 1000
            kismi = 0
        else:
            kismi += v
    return toplam + kismi


def rakamlastir(metin):
    """'üç yüz yetmiş yedi vaka' -> '377 vaka'. Yazıyla yazılmış sayı,
    rakamla yazılmıştan daha az iddia değildir; ölçüt ikisini de görmeli."""
    def _c(m):
        k = [tr_kucult(x.group(1)) for x in _BIR.finditer(m.group(0))]
        k = [x for x in k if x in KELIME]
        # Türkçede "bir" hem SAYIDIR hem BELİRSİZ ARTİKELDİR. Tek başına
        # geldiğinde neredeyse her zaman artikeldir: "bir alt takımın vaka
        # sayısı" bir toplam iddiası değildir, ama çevrilirse öyle görünür.
        # Dizinin parçasıyken ("yirmi bir", "yüz bir") sayıdır ve çevrilir.
        if k == ["bir"]:
            return m.group(0)
        return str(_degerle(k)) if k else m.group(0)
    return DIZI.sub(_c, metin)


def duz(metin):
    metin = re.sub(r"<!--.*?-->", " ", metin, flags=re.S)
    metin = re.sub(r"<[^>]+>", " ", metin)
    return re.sub(r"[ \t]+", " ", metin)


# --- ölçülen gerçek ----------------------------------------------------
_hepsi = oku("sinama", "hepsi.sh")
OLCULEN_TAKIM = len(re.findall(r'topla "', _hepsi))
# G/H/I çalıştırılabilir değil, işaretçi olarak basılır ama tabloda
# BELGELENİR. İki sayı da gerçektir; ikisi de elle değil, hepsi.sh'ten
# ölçülür. Elle yazılmış üçüncü bir sayı kabul edilmez.
OLCULEN_ISARETCI = len(re.findall(r'echo "  [A-Z] · .*-> sinama/ks_', _hepsi))
OLCULEN_BELGELI = OLCULEN_TAKIM + OLCULEN_ISARETCI
# [AL-06] İlk yazımda vaka sayısı SAYIM.txt'ten okunuyordu — yani BB, İÇİNDE
# BULUNDUĞU koşumun kaydını okuyordu. Koşum sırasında dosya henüz ÖNCEKİ
# koşumun sayısını taşır: BB koşum içinde kırmızı, koşumdan sonra yeşil
# görünüyordu. Onuncu ve on altıncı turların katman kuralı ("denetim, kendini
# denetleyen takımı denetleyemez") üçüncü kez, bu kez VERİ yoluyla ihlal
# edilmişti ve AL-06 yakaladı.
#
# Sayı artık DURAĞAN ölçülür: hepsi.sh'e bağlı her takımın kendi beyan ettiği
# BEKLENEN_VAKA toplanır. Her takımın XX-00 vakası o beyanın gerçek vaka
# sayısına eşit olduğunu ayrıca güvenceye alır; zincir kapalıdır ve hiçbir
# koşum kaydına dokunmaz.
_bagli = re.findall(r'python3 "\$S/(ks_\w+\.py)"', _hepsi)
_top, _beyansiz = 0, []
for _f in _bagli:
    _t = oku("sinama", _f)
    _b = re.search(r"^BEKLENEN_VAKA = (\d+)", _t, re.M)
    if _b:
        _top += int(_b.group(1))
    else:
        _beyansiz.append(_f)
OLCULEN_VAKA = _top if _bagli and not _beyansiz else -1

# --- beyan edilmiş tarihsel koşumlar -----------------------------------
# Kaynak: yamalar/DEGISIKLIKLER.md — raporun kendi kaydı.
_deg = oku("yamalar", "DEGISIKLIKLER.md")
_sadik = re.search(r"Kitaba sadık kurulum:\s*(\d+) vaka,\s*\*\*(\d+)", _deg)
SADIK_VAKA = int(_sadik.group(1)) if _sadik else -1
SADIK_KALDI = int(_sadik.group(2)) if _sadik else -1

# Bir cümleciği SADIK koşuma bağlayan nitelemeler
SADIK_NITEL = re.compile(
    r"kitaba sadık|eksiksiz kurulum|kelimesi kelimesine|yamasız|sadık kurulum",
    re.I)
# Bir sayıyı geçmişe bağlayan indisler
INDIS = re.compile(r"\d+\. tur|turda|turunda|başlangıçta|ilk koşu|o gün|"
                   r"birinci tur|kurulum anında|\d{4}-\d{2}-\d{2}|"
                   r"yamalı kurulum|yamalı hâlde", re.I)

# Türkçe eklemeli yazar: "96 vakayla sınandı" içinde \b hiç eşleşmez
# ve iddia GÖRÜNMEZ olur. AO-02'de aynı tuzak vardı ("ara" / "aranır").
# Sayı ile birim arasına SIFAT girer: "50 çalıştırılabilir takım". Bitişiklik
# arayan ilk yazım bunu göremedi — ve bu, artifact'in ÜST BİLGİSİNDEKİ
# iddianın ta kendisiydi. Yani ölçüt, en çok ölçmesi gereken cümleyi
# atlıyordu; mutasyon M6 olmasa görünmezdi.
# "XX-00 vakası" bir KİMLİKTİR, bir sayım değil: tireden sonraki rakam
# iddia taşımaz. Sol sınır olmadan ölçüt kendi vaka kimliklerini sayı sandı.
SAYIM_IDDIA = re.compile(
    r"(?<![\w-])(\d{1,4})\s+(?:[^\W\d_]+\s+){0,2}(vaka|takım)(?:\w*)")

# "B (34 vaka), A (24)" bir B iddiasıdır, TAKIMIN TAMAMI hakkında değil.
# İlk yazımda ölçüt her sayımı bir TOPLAM sandı ve dört yanlış pozitif
# verdi. Yirmi dokuzuncu turun kuralının ikinci ekseni: yalnızca iddiayı
# taşıyan en küçük birim değil, iddianın NEYE dair olduğu da ölçülmeli.
# Bu yüzden yalnızca TOPLAM çerçevesindeki sayımlar denetlenir.
TOPLAMLAYICI = re.compile(
    r"toplam|çalıştırılabilir takım|vakayla sınan|vaka koşul|"
    r"\d+ takım · \d+ vaka|\d+ vaka \+ \d+ mutasyon|\d+ takım, \d+ vaka|"
    r"takımın tamamı|hepsi\.sh", re.I)
# Bir sayımı ALT KÜMEYE bağlayan çerçeveler: toplam iddiası değildir.
ALT_KUME = re.compile(r"korunuyordu|korunmuyordu|dâhil|takımı \d+ vaka|"
                      r"\([^)]*\d+ vaka|aynı yardımcıyı", re.I)


def iddialar(metin, yalnizca_toplam=True):
    """(sayi, birim, cumlecik) — cümlecik ölçeğinde, pencere değil."""
    cikti = []
    # Markdown vurgusu noktaya YAPIŞIR ("...kaldı.** Yamalı hâlde...") ve
    # bölücü ateşlemez; iki ayrı koşumun cümlesi tek cümlecik olur, sadık
    # tabana yamalı sayı yazılmış gibi görünür. Vurgu önce soyulur.
    metin = re.sub(r"[*_`]+", "", metin)
    # Markdown tablo SATIRLARI ayrı iddialardır: yalnızca \n\n ile bölmek
    # bütün tabloyu tek cümlecik yapar ve bir satırın zaman indisi yandaki
    # satırı da örter. "\n(?=|)" satırları ayırır, sarılmış düzyazıyı bölmez.
    for p in re.split(r"(?<=[.:;!?])\s+|\n\n|\n(?=\|)|\s—\s", metin):
        p = re.sub(r"\s+", " ", p).strip()
        if not p:
            continue
        r = rakamlastir(p)
        if yalnizca_toplam and (not TOPLAMLAYICI.search(r)
                                or ALT_KUME.search(r)):
            continue
        for m in SAYIM_IDDIA.finditer(r):
            cikti.append((int(m.group(1)), m.group(2).lower(), r))
    return cikti


def denetle(metin, ad):
    kotu = []
    for sayi, birim, p in iddialar(metin):
        if SADIK_NITEL.search(p):
            dogru = SADIK_VAKA if birim == "vaka" else None
            if dogru is not None and sayi != dogru:
                kotu.append("%s: SADIK koşuma %d %s yazılmış, kayıt %d — %s"
                            % (ad, sayi, birim, dogru, p[:60]))
            continue
        if INDIS.search(p):
            continue                      # tarihsel ve indisli: serbest
        if birim == "vaka":
            if sayi != OLCULEN_VAKA:
                kotu.append("%s: indissiz %d vaka, ölçülen %d — %s"
                            % (ad, sayi, OLCULEN_VAKA, p[:60]))
        elif sayi not in (OLCULEN_TAKIM, OLCULEN_BELGELI):
            kotu.append("%s: indissiz %d takım, ölçülen %d/%d — %s"
                        % (ad, sayi, OLCULEN_TAKIM, OLCULEN_BELGELI, p[:60]))
    return kotu


RAPOR = duz(oku("RAPOR.md"))
HTML = duz(oku("kor-sinama-raporu.html"))

_r = denetle(RAPOR, "RAPOR")
_h = denetle(HTML, "ARTIFACT")

# --- BB-01 · raporun indissiz sayıları güncel --------------------------
vaka("BB-01", "RAPOR'daki indissiz her sayım ölçülen değere eşit",
     not _r, "ölçülen %d takım / %d vaka · sapma: %s"
     % (OLCULEN_TAKIM, OLCULEN_VAKA, "; ".join(_r[:3]) if _r else "yok"))

# --- BB-02 · artifact'in sayıları da ------------------------------------
vaka("BB-02", "ARTIFACT'taki indissiz her sayım ölçülen değere eşit",
     not _h, "sapma: %s" % ("; ".join(_h[:3]) if _h else "yok"))

# --- BB-03 · "Dokuz takım" başlığı tablosuyla uyuşuyor ------------------
_i = RAPOR.find("takım, ")
# Başlık, SATIR BAŞINDA duran gerçek başlıktır. İlk metinsel eşleşmeyi almak,
# bu turun DÜZELTME TABLOSUNDAKİ alıntıyı ("9 takım, 96 vaka") başlık sanıyordu:
# bir kusuru arayan ölçüt, o kusuru BELGELEYEN düzyazıyı da yakalar — bu takım
# o sınıfın beşinci örneği.
_bas = re.search(r"^(\d+) takım, (\d+) vaka:$", rakamlastir(RAPOR), re.M)
if _bas:
    _blok = RAPOR[RAPOR.find(_bas.group(0)) + len(_bas.group(0)):]
    _blok = _blok[:_blok.find("\n\n**Sonuç")] if "\n\n**Sonuç" in _blok else _blok
    _satir = len([r for r in _blok.splitlines()
                  if re.match(r"^\|\s*[A-Z]{1,2}\s*\|", r)])
else:
    _satir = -1
vaka("BB-03", "takım tablosunun başlığı tablodaki satır sayısını söylüyor",
     bool(_bas) and int(_bas.group(1)) == _satir,
     "başlık %s · tablo %d satır"
     % (_bas.group(1) if _bas else "yok", _satir))

# --- BB-04 · sadık taban her yerde aynı ---------------------------------
_taban = set()
for ad, metin in (("RAPOR", RAPOR), ("ARTIFACT", HTML),
                  ("DEGISIKLIKLER", duz(_deg))):
    for sayi, birim, p in iddialar(metin):
        if birim == "vaka" and SADIK_NITEL.search(p):
            _taban.add((ad, sayi))
_sapan = sorted(a for a, n in _taban if n != SADIK_VAKA)
vaka("BB-04", "kitaba sadık tabanın vaka sayısı üç belgede de aynı",
     SADIK_VAKA > 0 and not _sapan,
     "kayıt %d vaka / %d kaldı · sapan belge: %s"
     % (SADIK_VAKA, SADIK_KALDI, _sapan or "yok"))

# --- BB-05 · ölçüt vakum değil ------------------------------------------
# Sayı sözcüklerini okumayan bir ölçüt "doksan altı"yı göremez; BB-02 bu
# yüzden kırk altı tur boyunca sessiz kalırdı.
_yazi = (rakamlastir("doksan altı vaka") == "96 vaka"
         and rakamlastir("iki yüz vaka") == "200 vaka"
         and rakamlastir("üç yüz yetmiş yedi vaka") == "377 vaka")
vaka("BB-05", "ölçüt yazıyla yazılmış sayıları okuyor ve tabanı durağan sayıyor",
     _yazi and not _beyansiz and OLCULEN_VAKA > 0
     and len(iddialar(RAPOR)) >= 5 and len(iddialar(HTML)) >= 3,
     "yazı→rakam %s · %d takım beyanından %d vaka · beyansız: %s · "
     "RAPOR %d iddia · ARTIFACT %d iddia"
     % (_yazi, len(_bagli), OLCULEN_VAKA, _beyansiz or "yok",
        len(iddialar(RAPOR)), len(iddialar(HTML))))


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BB-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
