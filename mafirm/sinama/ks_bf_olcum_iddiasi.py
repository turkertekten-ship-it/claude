#!/usr/bin/env python3
"""KÖR SINAMA BF — raporun ÖLÇÜM iddiaları canlı değerle uyuşuyor mu.

Yönelim (elli ikinci tur). Elli birinci tur kitabın metnini 1038 karakter
değiştirdi (yumuşak satır sonları geri geldi). Kitaptan TÜRETİLEN her sayı o
gün bozuk metin üzerinde ölçülmüştü — ama teslimatlardaki karşılıkları
kimse yeniden ölçmedi.

BB bu boşluğu kapatmıyor: BB yalnızca "N vaka" ve "N takım" sayımlarını
denetler. "N alıntı doğrulandı", "N/M birebir", "SELFTEST OK (N vaka)"
gibi ÖLÇÜM iddiaları hiçbir ölçütün kapsamında değildi ve ölçüldü:

    rapor "13 alıntı doğrulandı" diyor; AW takımı 21 alıntı doğruluyor.

Sekiz alıntı fark. Sayı, ölçtüğü şey büyürken yerinde kaldı — bu
incelemenin en sık ikinci sınıfı, bu kez ölçüm sonuçlarında.

AF-05 aynı işi iki iddia için yapıyordu (D mutasyonu, V korpusu) ama
ELLE seçilmiş iki tanesi için. Bu takım onu bir KAYDA çevirir: her ölçüm
iddiası, o değeri gerçekten üreten takımdan okunur; kayıtta olmayan bir
iddia biçimi de BF-02'yi kırar, yani kayıt sessizce eskiyemez.
"""
import io
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_S = os.path.dirname(os.path.abspath(__file__))
_KOK = os.environ.get("MAFIRM") or os.path.dirname(_S)

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def oku(*p):
    y = os.path.join(_KOK, *p)
    return io.open(y, encoding="utf-8").read() if os.path.exists(y) else ""


def _kos(*argv):
    """Ölçümü ÜRETEN takımı kendi süreci içinde koştur.

    [Onuncu turun katman kuralı] Değer yeniden HESAPLANMAZ, üreten takımdan
    OKUNUR. Yeniden hesaplayan bir gözcü, ölçtüğü takımdan sessizce ayrışır
    ve iki farklı doğru ortaya çıkar."""
    p = subprocess.run(argv, capture_output=True, text=True,
                       cwd=_KOK, env=dict(os.environ, MAFIRM=_KOK))
    return p.stdout + p.stderr


def _sayi(cikti, desen, grup=1):
    m = re.search(desen, cikti)
    return m.group(grup) if m else None


def _degisken(modul, ifade):
    """Üreten takımı kendi süreci içinde İÇE AKTAR ve DEĞERİNİ oku.

    Neden çıktıdan değil: takımlar kanıt sütununu yalnızca vaka KIRMIZIYKEN
    basıyor. Yani bir takım geçtiğinde ölçtüğü sayıyı SAKLIYOR — oysa
    denetlenmesi gereken tam olarak o sayı. Değeri modülün kendisinden
    okumak, yeniden hesaplamak değildir: üreticinin kendi sonucudur."""
    kod = ("import sys; sys.path.insert(0, %r); import %s as m; print(%s)"
           % (_S, modul, ifade))
    return _kos(sys.executable, "-c", kod).strip() or None


_kapi = _kos(sys.executable, os.path.join(_KOK, ".claude", "hooks", "kapi.py"),
             "--self-test")

# --- KAYIT: iddia biçimi -> canlı değer --------------------------------
# Her satır: (ad, teslimattaki desen, canlı değer, kaynak takım)
OLCUMLER = [
    ("AW doğrulanmış alıntı", r"(\d+) alıntı doğrulandı",
     _degisken("ks_aw_alinti", "m._ok"), "AW"),
    ("AZ birebir satır", r"(\d+)/\d+ birebir",
     _degisken("ks_az_sadik", "m._toplam - len(m._eksik) - len(m.BEYAN)"
               if False else "m._toplam - len(m.BEYAN)"), "AZ"),
    ("AZ toplam satır", r"\d+/(\d+) birebir",
     _degisken("ks_az_sadik", "m._toplam"), "AZ"),
    ("kapı öz-sınama vakası", r"SELFTEST OK \((\d+) vaka\)",
     _sayi(_kapi, r"SELFTEST OK \((\d+) vaka\)"), "kapi.py"),
]

# Geçmişi ANLATAN bir sayı, güncel bir iddia değildir: artifact otuz altıncı
# turun kusurunu anlatırken o günkü değeri ALINTILIYOR. BB'nin zaman indisi
# kuralının bu takımdaki karşılığı. [anmak ≠ iddia etmek]
ANLATI = re.compile(r"\d+\. tur|turda|turunda|önce de|demeye devam|"
                    r"diyordu|o günkü|eskiden|eklenmeden önce", re.I)

TESLIMAT = {"RAPOR": oku("RAPOR.md") + "\n" + oku("KITAP-ERRATA.md"),
            "ARTIFACT": oku("kor-sinama-raporu.html")}


def _cumlecikler(t):
    """Cümlecik ölçeği. Bütün belgeyi tek dizeye düzleştirmek, tablo
    satırlarını birbirine karıştırır ve bir satırdaki anlatı işareti
    yandaki satırı da muaf yapar — BB'de aynı tuzak çıkmıştı."""
    t = re.sub(r"<[^>]+>", " ", t)
    for p in re.split(r"(?<=[.:;!?])\s+|\n\n|\n(?=\|)|\s—\s|</?li>|</?p>", t):
        p = re.sub(r"\s+", " ", p).strip()
        if p:
            yield p


_sapan, _kapsanan = [], 0
for _ad, _desen, _canli, _kaynak in OLCUMLER:
    if _canli is None:
        _sapan.append("%s: canlı değer OKUNAMADI (%s)" % (_ad, _kaynak))
        continue
    for _bad, _metin in TESLIMAT.items():
        for _p in _cumlecikler(_metin):
            for _m in re.finditer(_desen, _p):
                if ANLATI.search(_p):
                    continue                  # geçmişi anlatan sayı
                _kapsanan += 1
                if _m.group(1) != _canli:
                    _sapan.append("%s/%s: yazılı %s, canlı %s (%s)"
                                  % (_bad, _ad, _m.group(1), _canli, _kaynak))

# --- BF-01 · her ölçüm iddiası canlı değere eşit -----------------------
vaka("BF-01", "teslimatlardaki her ölçüm iddiası canlı değere eşit",
     not _sapan, "%d iddia bulundu · sapan: %s"
     % (_kapsanan, "; ".join(sorted(set(_sapan))[:4]) if _sapan else "yok"))

# --- BF-02 · kayıt, ölçüm biçimlerini gerçekten kapsıyor ---------------
# Bir ölçüm iddiası kayıtta yoksa sessizce sürüklenir. Bu vaka, teslimatta
# geçen ama kayıtta karşılığı olmayan ölçüm KALIPLARINI yakalar.
# Kayıttaki desenleri "rakam yeri" soyutlamasına indirge ve teslimatta
# geçen ölçüm kalıplarıyla karşılaştır: kayıtta karşılığı olmayan bir kalıp
# sessizce sürüklenir.
def _iskelet(d):
    return re.sub(r"\\d\+|\(|\)", "", d)


BILINEN = {_iskelet(d) for _a, d, _c, _k in OLCUMLER}
ARANAN = [r"\d+ alıntı doğrulandı", r"\d+/\d+ birebir",
          r"SELFTEST OK \(\d+ vaka\)"]
_kayitsiz = [k for k in ARANAN
             if any(re.search(k, p) for m in TESLIMAT.values()
                    for p in _cumlecikler(m))
             and _iskelet(k) not in BILINEN]
vaka("BF-02", "teslimatta geçen her ölçüm kalıbının kayıtta karşılığı var",
     not _kayitsiz, "kayıtsız kalıp: %s" % (_kayitsiz or "yok"))

# --- BF-03 · kayıt vakum değil -----------------------------------------
_okunan = [a for a, _d, c, _k in OLCUMLER if c is not None]
vaka("BF-03", "her kayıt satırı üreten takımdan gerçek bir değer okuyor",
     len(_okunan) == len(OLCUMLER) and _kapsanan >= 4,
     "%d/%d canlı değer okundu · %d iddia eşleşti · değerler: %s"
     % (len(_okunan), len(OLCUMLER), _kapsanan,
        {a: c for a, _d, c, _k in OLCUMLER}))

# --- BF-04 · değer yeniden hesaplanmıyor, takımdan okunuyor ------------
# [Onuncu tur] Gözcü, ölçtüğü şeyi kendi hesaplarsa iki doğru oluşur ve
# hangisinin bozulduğu anlaşılmaz. Bu vaka, BF'nin kendi kaynağında
# alıntı/satır sayan bir mantık BULUNMADIĞINI güvenceye alır.
_kaynak = io.open(os.path.abspath(__file__), encoding="utf-8").read()
_kod = "\n".join(r for r in _kaynak.splitlines()
                 if not r.lstrip().startswith("#"))
# Desen KENDİ tanım satırında da geçer; onu dışlamadan ölçüt kendini
# yakalar. Bu incelemenin en sık sınıfının en saf hâli: bir kusuru arayan
# ölçüt, o kusuru TARİF EDEN satırı da bulur.
_YASAK = ("zip" "file", "do" "cx", "kitap_" "metni")
_kendi_hesabi = [t for t in _YASAK
                 if any(t in r for r in _kod.splitlines()
                        if "_YASAK" not in r)]
vaka("BF-04", "BF ölçümü yeniden hesaplamıyor, üreten takımdan okuyor",
     not _kendi_hesabi, "kendi hesabı: %s" % (_kendi_hesabi or "yok"))


BEKLENEN_VAKA = 4


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BF-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
