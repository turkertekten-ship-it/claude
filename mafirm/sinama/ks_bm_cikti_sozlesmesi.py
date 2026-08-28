#!/usr/bin/env python3
"""KÖR SINAMA BM — aracın GERÇEK çıktısı kendi kapılarından geçiyor mu.

Yönelim (altmışıncı tur). J takımı §19'un kabul sınamasını koşuyor ve
"doğru cevap kapılardan geçiyor mu" diye soruyor. Ama sınadığı metin ELLE
YAZILMIŞ bir örnek cevaptı — kapıları geçsin diye benim kurduğum bir metin.
`esik.py`'nin GERÇEKTEN ürettiği çıktı hiç sınanmamıştı.

Sınanınca: aracın her cevabı, sistemin KENDİ üç kapısı tarafından
bloklanıyordu — kitabın kendi §19 pilotu dâhil.

    kanit       gerekçe eşiği adıyla anıyor ama dayanak 450 karakter ötede
    guncellik   "Eşiklerin doğrulama tarihi:" kapının tanıdığı biçim değil
    arastirma   "Kontrol edildi:" satırı hiç yok

Bu, raporun kitapta bulduğu merkezî kusurun aynısıdır: §14'ün emrettiği
biçim §12'nin kapısında bloklanıyordu. Burada aynı şey aracın kendi
çıktısında. Ve **kabul sınaması bunu göremedi, çünkü gerçek ürünü değil
onun temsilcisini sınıyordu.**

Yerine geçen bir metni sınamak, ürünü sınamak değildir.
"""
import importlib.util
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_ESIK = os.path.join(_KOK, "birimler", "rekabet", "kod", "esik.py")
_spec = importlib.util.spec_from_file_location(
    "kapi_bm", os.path.join(_KOK, ".claude", "hooks", "kapi.py"))
kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapi)

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def kos(*taraf):
    argv = [sys.executable, _ESIK]
    for t in taraf:
        argv += ["--taraf", t]
    return subprocess.run(argv, capture_output=True, text=True).stdout


def ates(cikti):
    return sorted({a for a, _ in kapi.denetle(cikti, disari=False,
                                              yol="cikti/rekabet.md")})


# Beş cevap biçimi: EVET(B), EVET(A), EVET(iki), HAYIR, BELİRLENEMİYOR.
DOSYALAR = {
    "§19 pilotu (B)": ("A GmbH,dunya=112800000000,rol=devralan",
                       "H A.Ş.,tr=1400000000,rol=hedef"),
    "itirazlı bant (HAYIR)": ("A,tr=2800000000,dunya=5000000000,rol=devralan",
                              "H,tr=300000000,dunya=300000000,"
                              "rol=hedef,teknoloji=1"),
    "yerleşiklik açık (EVET)": ("A,dunya=12000000000,rol=devralan",
                                "H,tr=400000000,dunya=900000000,"
                                "rol=hedef,teknoloji=1"),
    "belirlenemiyor": ("A,tr=900000000,rol=devralan",
                       "H,tr=1200000000,rol=hedef"),
    "her iki eşik": ("A,tr=2000000000,dunya=20000000000,rol=devralan",
                     "H,tr=1500000000,dunya=1500000000,rol=hedef"),
}
CIKTI = {ad: kos(*t) for ad, t in DOSYALAR.items()}

# --- BM-01 · her gerçek çıktı kapılardan geçiyor -----------------------
_bloklu = {ad: ates(c) for ad, c in CIKTI.items() if ates(c)}
vaka("BM-01", "aracın gerçek çıktısı her cevap biçiminde kapılardan geçiyor",
     not _bloklu, "%d çıktı sınandı · bloklanan: %s"
     % (len(CIKTI), _bloklu or "yok"))

# --- BM-02 · dayanak rakamın YANINDA ----------------------------------
# Belgenin altındaki tek bir dayanak satırı üstteki gerekçeyi aklamaz.
# [Kendi kusurum] İlk sürüm HER gerekçeden atıf istiyordu. Oysa olumsuz ve
# belirsiz cevapların gerekçesi hiçbir RAKAM anmaz ("iki ayak da
# karşılanmadı"); dayanaksız bir rakam yoktur ki dayanak istensin. Kural 1
# rakamı olan cümleye uygulanır, her cümleye değil.
_RAKAM = re.compile(r"\d{1,3}(?:\.\d{3})+\s*TL")
_atifsiz = []
for ad, c in CIKTI.items():
    bas = c.split("Kullanılan")[0]
    if _RAKAM.search(bas) and "Tebliğ" not in bas:
        _atifsiz.append(ad)
vaka("BM-02", "gerekçedeki eşik, dayanağını yanında taşıyor (kural 1)",
     not _atifsiz, "dayanağı gerekçeden uzak: %s" % (_atifsiz or "yok"))

# --- BM-03 · §14 çıktı sözleşmesi satırı var --------------------------
_kontrolsuz = [ad for ad, c in CIKTI.items()
               if not kapi.KONTROL.search(c) or "bulunamayan:" not in c]
vaka("BM-03", "her çıktı 'Kontrol edildi … bulunamayan:' satırıyla bitiyor",
     not _kontrolsuz, "eksik: %s" % (_kontrolsuz or "yok"))

# --- BM-04 · ölçüt vakum değil ----------------------------------------
# Kapılar bozuk bir çıktıda gerçekten ateşlemeli; yoksa BM-01 hiçbir şey
# sınamaz. [Elli dokuzuncu turun kuralı: tetiklenmemiş kapı sınanmamıştır.]
_bozuk = "Bildirime tabi mi : EVET\nEşik 1.000.000.000 TL aşılıyor.\n"
vaka("BM-04", "kapılar sözleşmesiz bir çıktıda gerçekten ateşliyor",
     len(ates(_bozuk)) >= 2, "sözleşmesiz çıktıda ateşleyen: %s"
     % ates(_bozuk))

# --- BM-05 · kabul sınaması artık gerçek ürünü de görüyor -------------
# [Kendi kusurumuz] J elle yazılmış bir temsilciyi sınıyordu. Bu vaka, o
# temsilcinin gerçek çıktının yerine geçmediğini kalıcı kılar.
_j = open(os.path.join(_KOK, "sinama", "ks_j_kabul.py"),
          encoding="utf-8").read()
vaka("BM-05", "gerçek çıktı, elle yazılmış örnekle aynı kapılardan geçiriliyor",
     "esik.py" in _j and len(CIKTI) >= 5,
     "J elle yazılmış örneği sınıyor; BM %d gerçek çıktıyı sınıyor"
     % len(CIKTI))


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BM-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
