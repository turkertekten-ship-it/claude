#!/usr/bin/env python3
"""KÖR SINAMA BA — kayıt ile iddianın çelişmesi.

Yönelim (kırk altıncı tur). Üç kez aynı şeyi yaptım:

  4→28. tur   `egress-kaniti.md` WebSearch için **"çalışıyor"** diyordu;
              ben "işe yaramaz" diye okudum ve üç ENGELLEYİCİ bulguyu
              çalıştığı KAYITLI olan bir kanalı denemeden açık tuttum.
  45. tur     Turu "vekil durum uç noktasını hiç sorgulamadım" diye açtım;
              kayıt onu zaten içeriyordu.
  daha önce   "hiçbiri silinmedi" sözü bir süre doğru değildi ve bunu
              yamalar/DEGISIKLIKLER.md'ye yazana kadar fark etmedim.

Yirmi yedinci turun kuralı: üç örnek bir SINIFTIR ve sınıf sağlamayla
kapanır. Ama "yazarın kaydı doğru okuyup okumadığı" sınanamaz. Sınanabilen
şey SONUCUDUR: **kayıt bir şeyin çalıştığını/doğrulandığını söylüyorken,
teslimatın onu çalışmıyor/doğrulanmamış gibi anması.** Üç olayın üçü de tam
olarak bu biçimdeydi.

Ölçüm sonucu: bugün gerçek çelişki YOK. Ama ölçüt iki kez fazla geniş çıktı
ve ikisi de bu incelemenin en sık tekrar eden tuzağıydı:

  * PENCERE ölçeği iki yanlış pozitif verdi — biri WebSearch'ün ÇALIŞTIĞINI
    söyleyen cümleydi, öteki I-04'ün doğrulandığını söylerken yanındaki
    cümleden "kapatılamaz" kelimesini kapıyordu.
  * CÜMLECİK ölçeğinde bir tane kaldı: hatayı ANLATAN cümle
    ("WebSearch satırını 'işe yaramaz' diye yanlış okumuştum").

Bir kusuru düzyazıda arayan her ölçüt, o kusuru BELGELEYEN düzyazıyı da
yakalar. Bu takım o muafiyeti açıkça tanımlar ve muafiyetin kaçış deliğine
dönüşmemesini sağlar: anlatı sayılan her cümlecik bir GEÇMİŞ-HATA işareti
taşımak zorundadır.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def oku(*p):
    y = os.path.join(_KOK_COZ, *p)
    return io.open(y, encoding="utf-8").read() if os.path.exists(y) else ""


KANIT = oku("hafiza", "egress-kaniti.md")
BULGU = oku("hafiza", "dogrulama-bulgulari.md")
TESLIMAT = oku("RAPOR.md") + "\n" + oku("KITAP-ERRATA.md")

# Kayıtların OLUMLU beyanları
CALISAN = {m.group(1).strip().strip("*") for m in
           re.finditer(r"^\|\s*([^|]+?)\s*\|[^|]*\|[^|]*çalışıyor",
                       KANIT, re.M)}
# [AE-01] Tek harfli önek varsaymak: AA/BA gibi iki harfli bulgu
# kimlikleri desene GÖRÜNMEZ olur ve BA-01 onları sessizce sınamaz.
DOGRULANAN = set(re.findall(r"^([A-Z]{1,2}-\d+)\s*\|\s*DOĞRULANDI",
                            BULGU, re.M))

OLUMSUZ = re.compile(r"kullanılamadı|denenmedi|hiç denenme|işe yaramaz|"
                     r"erişilemedi|doğrulanamadı|doğrulanmadı", re.I)

# GEÇMİŞ-HATA işaretleri: bir cümlecik bunlardan birini taşıyorsa güncel bir
# iddia değil, düzeltilmiş bir hatanın ANLATIMIDIR. Muafiyet bu işarete
# bağlıdır — "anlatı" demek yetmez, anlatı olduğunun kanıtı istenir.
ANLATI = re.compile(r"yanlış okum|yanlış okundu|düzelt|önce .{0,30}diyordu|"
                    r"sanmıştım|sanıp|hata bana ait|o güne kadar|"
                    r"\d+\. turda|turunda|yanılmış", re.I)


def cumlecikler(metin):
    # Satır kaydırması bir cümleyi ortasından böler: kaynakta "yanlış\nokum-
    # uştum" yazıyorsa ANLATI'nın "yanlış okum" kalıbı HİÇ eşleşmez ve muafiyet
    # sessizce çalışmaz. Aynı kaçış deliği otuz dokuzuncu turda AM-01'de de
    # çıkmıştı. Bu yüzden her cümlecik eşleştirmeden ÖNCE tek boşluğa
    # normalleştirilir.
    return [re.sub(r"\s+", " ", p).strip()
            for p in re.split(r"(?<=[.;:!?])\s+|\n\n|\s—\s", metin)]


# Muafiyet sessizce BÜYÜYEBİLEN bir kaçış deliğidir: bugün bir cümleyi örten
# kural, yarın gerçek bir çelişkiyi de örter ve kimse fark etmez. Bu yüzden
# muaf tutulan her hedef AYRICA burada SAYIYLA beyan edilir. Yeni bir muafiyet
# — ya da beyan edilenden fazlası — gerekçesi yazılana kadar BA-02'yi kırar.
MUAF_BEYAN = {
    "KANAL WebSearch": (1, "yirmi sekizinci turun yanlış okumasını ANLATAN "
                           "cümle; düzeltme yamalar/DEGISIKLIKLER.md'de"),
}

_celiski, _muaf = [], []
for p in cumlecikler(TESLIMAT):
    if not OLUMSUZ.search(p):
        continue
    hedefler = [("KANAL", k) for k in CALISAN if k in p]
    hedefler += [("BULGU", f) for f in DOGRULANAN
                 if re.search(r"\b%s\b" % re.escape(f), p)]
    if not hedefler:
        continue
    anahtar = "%s %s" % (hedefler[0][0], hedefler[0][1])
    if ANLATI.search(p):
        # Kesme YALNIZCA gösterim içindir. Ölçen hiçbir şey kesilmiş metni
        # okumamalı: "yanlış okum" işareti 70. karakterin ötesindeydi ve bu
        # vakayı bir tur boyunca yanlış kırmızı yaptı.
        _muaf.append((anahtar, p))
    else:
        _celiski.append("%s :: %s" % (anahtar, p[:70]))

# --- BA-01 · kayıt ile teslimat çelişmiyor --------------------------
vaka("BA-01", "kayıtta çalışan/doğrulanan hiçbir şey teslimatta olumsuzlanmıyor",
     not _celiski,
     "kayıtta çalışan kanal: %s · doğrulanan bulgu: %s · ÇELİŞKİ: %s"
     % (sorted(CALISAN), sorted(DOGRULANAN),
        "; ".join(_celiski[:3]) if _celiski else "yok"))

# --- BA-02 · ANLATI muafiyeti beyan edilmiş ve tam ------------------
# "Muaf tutulan cümlecik ANLATI işareti taşıyor mu" diye sormak TOTOLOJİDİR:
# o işareti taşıdığı için muaf tutuldu. Sınanabilir olan, muafiyetin
# BÜYÜYÜP büyümediğidir — beyandan fazla muafiyet de, hiçbir şeyi örtmeyen
# bayat bir beyan da (P takımının TESLIMATLAR sürüklenmesiyle aynı sınıf)
# vakayı kırar.
_gercek = {}
for a, _q in _muaf:
    _gercek[a] = _gercek.get(a, 0) + 1
_beyansiz = sorted("%s×%d" % (a, n) for a, n in _gercek.items()
                   if MUAF_BEYAN.get(a, (0, ""))[0] != n)
_bayat = sorted(a for a in MUAF_BEYAN if a not in _gercek)
vaka("BA-02", "her anlatı muafiyeti beyan edilmiş, her beyan bir şey örtüyor",
     not _beyansiz and not _bayat,
     "beyan %s · gerçekleşen %s · beyansız/sayı uymayan: %s · bayat beyan: %s"
     % ({a: n for a, (n, _) in MUAF_BEYAN.items()}, _gercek,
        _beyansiz or "yok", _bayat or "yok"))

# --- BA-03 · kayıtlar gerçekten OLUMLU beyan taşıyor ----------------
# Ölçüt vakum olmasın: kayıtta hiç "çalışıyor"/"DOĞRULANDI" yoksa BA-01
# hiçbir şey sınamamış olur.
vaka("BA-03", "kayıtlar sınanacak olumlu beyan taşıyor",
     bool(CALISAN) and len(DOGRULANAN) >= 3,
     "%d çalışan kanal · %d doğrulanmış bulgu"
     % (len(CALISAN), len(DOGRULANAN)))

# --- BA-04 · ölçüt cümlecik ölçeğinde ------------------------------
# Pencere ölçeği bu turda iki yanlış pozitif verdi; ölçüt cümleciğe
# indirildi. Bu vaka, ölçütün geri genişlemesini yakalar.
_kaynak = io.open(os.path.abspath(__file__), encoding="utf-8").read()
_kod = "\n".join(r for r in _kaynak.splitlines()
                 if not r.lstrip().startswith("#"))
_pencere = re.search(r"\[max\(0,|\.\{0,\d{3,}\}", _kod) is not None
vaka("BA-04", "ölçüt cümlecik ölçeğinde, karakter penceresinde değil",
     not _pencere, "pencere kullanımı: %s" % _pencere)


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 4


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BA-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
