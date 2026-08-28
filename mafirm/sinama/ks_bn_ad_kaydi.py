#!/usr/bin/env python3
"""KÖR SINAMA BN — sır kapısının AD KAYDI ayağı, dolu bir kayıtla.

Yönelim (altmış üçüncü tur). Kural 6 sistemin en yüksek bedelli kuralıdır:
müvekkili tanıtan hiçbir bilgi makineden çıkmaz. Kapının iki ayağı var —
DESEN ayağı (kod adı, A.Ş., dosya yolu) ve AD KAYDI ayağı
(`hafiza/muvekkil-adlari.txt`).

B takımı desen ayağını sınıyor. Ad kaydı ayağı **hiç sınanmamıştı**, çünkü
kayıt dosyası kurulumda BOŞ geliyor — ve boş bir kayıtla o ayağın kodu hiç
çalışmaz. Yani sistemin en ağır kuralının yarısı, ölçülmemiş duruyordu.

Dolu bir kayıtla ölçüldü ve bir kaçak bulundu:

    kayıtta "Işık Holding" · dışarı giden metinde "Isik Holding" → GEÇİYOR

`ş→s` bir büyük/küçük varyantı değildir; `re.I` onu yakalayamaz ve homoglif
tablosu yalnızca Kiril/Yunan harflerini katlıyordu. Oysa bir Türk müvekkil
adını **aksansız** yazmak Türkçe metinde en sık yapılan şeydir — hele bir
arama kutusuna yapıştırılırken, yani tam olarak bu kapının koruduğu yolda.

Takım kaydı KUM HAVUZUNDA kurar: canlı `hafiza/muvekkil-adlari.txt` dosyasına
hiç dokunulmaz (B-34'ün dersi — o fixture bir zamanlar canlı kaydı yok etti).
"""
import importlib.util
import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


# --- kum havuzu: canlı kayda ASLA dokunulmaz ---------------------------
_KUM = tempfile.mkdtemp(prefix="ks_bn_")
os.makedirs(os.path.join(_KUM, "hafiza"), exist_ok=True)
os.makedirs(os.path.join(_KUM, ".claude", "hooks"), exist_ok=True)
shutil.copy(os.path.join(_KOK, ".claude", "hooks", "kapi.py"),
            os.path.join(_KUM, ".claude", "hooks", "kapi.py"))
io.open(os.path.join(_KUM, "hafiza", "muvekkil-adlari.txt"), "w",
        encoding="utf-8").write(
    "# kum havuzu kaydı — canlı dosya değildir\n"
    "İhsan Yılmaz\nIşık Holding\nProje Şahin\nÇağrı Öztürk\n")
os.environ["MAFIRM"] = _KUM
_spec = importlib.util.spec_from_file_location(
    "kapi_bn", os.path.join(_KUM, ".claude", "hooks", "kapi.py"))
kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapi)


def ates(metin, disari=True):
    return kapi.kapi_sir(metin, disari=disari) is not None


# --- BN-01 · kayıt gerçekten okunuyor (vakum değil) --------------------
# Boş bir kayıtla bu takımın hiçbir vakası bir şey sınamaz.
_kayit = kapi._ad_kaydi()
vaka("BN-01", "ad kaydı okunuyor ve dolu (ölçüt vakum değil)",
     len(_kayit) == 4 and "Işık Holding" in _kayit,
     "%d ad okundu: %s" % (len(_kayit), _kayit))

# --- BN-02 · kayıtlı ad, yazım varyantlarında yakalanıyor --------------
VARYANT = [
    ("birebir", "İhsan Yılmaz ile toplantı"),
    ("tümü büyük", "İHSAN YILMAZ ile toplantı"),
    ("noktasız büyük I", "IHSAN YILMAZ ile toplantı"),
    ("aksansız", "Isik Holding devralıyor"),
    ("aksansız + büyük", "ISIK HOLDING devralıyor"),
    ("aksansız çoklu", "Cagri Ozturk ile toplantı"),
    ("satır kaydırmalı", "Işık\nHolding devralıyor"),
    ("URL kodlu", "dosya proje%20sahin olarak kaydedildi"),
]
_kacan = [ad for ad, m in VARYANT if not ates(m)]
vaka("BN-02", "kayıtlı ad her yazım varyantında yakalanıyor",
     not _kacan, "%d varyant · kaçan: %s" % (len(VARYANT), _kacan or "yok"))

# --- BN-03 · kayıtsız ad bloklanmıyor (yanlış pozitif denetimi) -------
# Doğru işi bloklayan bir kapı, bir gün içinde kapatılır (§12).
TEMIZ = ["Mehmet Demir ile toplantı",
         "Rekabet Kurumu'na bildirim yapıldı",
         "2010/4 sayılı Tebliğ m.7 uygulanır"]
_yanlis = [m for m in TEMIZ if ates(m)]
vaka("BN-03", "kayıtta olmayan ad ve kurum adları bloklanmıyor",
     not _yanlis, "yanlış bloklanan: %s" % (_yanlis or "yok"))

# --- BN-04 · kapı YALNIZCA dışarı giden çağrıda ateşliyor -------------
# İçeride müvekkil adı yazmak zorunludur; kapı içeriyi bloklarsa pratik durur.
_iceride = [m for _ad, m in VARYANT if ates(m, disari=False)]
vaka("BN-04", "içeri yazmada ad kaydı ayağı hiç ateşlemiyor",
     not _iceride, "içeride ateşleyen: %s" % (_iceride or "yok"))

# --- BN-05 · takım canlı kayda dokunmuyor ------------------------------
# [B-34 · AL-02] Bu fixture bir zamanlar CANLI kaydı yok etti.
_canli = os.path.join(_KOK, "hafiza", "muvekkil-adlari.txt")
_canli_metin = io.open(_canli, encoding="utf-8").read() if os.path.exists(_canli) else ""
vaka("BN-05", "canlı ad kaydı değişmedi (kum havuzu gerçekten ayrı)",
     "kum havuzu kaydı" not in _canli_metin and _KUM.startswith(tempfile.gettempdir()),
     "canlı kayıt %d bayt · kum havuzu: %s" % (len(_canli_metin), _KUM))

shutil.rmtree(_KUM, ignore_errors=True)

BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BN-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
