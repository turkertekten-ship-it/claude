#!/usr/bin/env python3
"""KÖR SINAMA BL — kapılar ANMA ile TAŞIMA'yı ayırt ediyor mu.

Yönelim (elli dokuzuncu tur). Elli sekizinci turda kapsam kapısı, zorunlu
başlığın ADINI anan bir cümleyle susturulabiliyordu: gerçek bölümü silip
yerine ondan SÖZ EDEN bir cümle bırakmak yetiyordu. Bu, raporun kitapta
bulduğu merkezî kusurun aynısıdır — *bir kontrolü kaldırıp yerine onu
anlatan bir cümle bırakmak denetimi yeşil tutar* — ve o tur kendi kapımızda
çıktı.

Ama düzeltilen TEK kapıydı. Yedi kapı var ve altısına bu soru hiç
sorulmadı. Yirmi yedinci turun kuralı: bir kusur bir yerde düzeltilince
sınıf kapanmaz.

Bu takım her kapıya AYNI çifti verir:

    TAŞIYAN metin  — kapının istediği şeyi gerçekten içerir  → SUSMALI
    ANAN metin     — yalnızca o şeyden SÖZ EDER              → ATEŞLEMELİ

İkisi arasındaki farkı göremeyen bir kapı, kendisinden söz edilerek
kandırılabilir.
"""
import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "kapi_bl", os.path.join(_KOK, ".claude", "hooks", "kapi.py"))
kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapi)

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def ates(metin, yol="deneme.md", disari=False):
    return {a for a, _ in kapi.denetle(metin, disari=disari, yol=yol)}


# --- her kapı için (taşıyan, anan) çifti -------------------------------
# [BO · altmış dördüncü tur] Bu sözlük ÜÇ kapı taşıyordu. Takımın kendi
# başlığı ise şunu yazıyordu: "Yedi kapı var ve altısına bu soru hiç
# sorulmadı... bir kusur bir yerde düzeltilince sınıf kapanmaz." Sınıfı ADIYLA
# ANAN takım, sınıfı 3/7 kapatmıştı — ve atlanan dört kapının İKİSİ gerçekten
# sızdırıyordu (onay ve koltuk, olumsuzlanmış bir beyanla susturulabiliyordu).
# BL-10 artık listeyi KEŞİFLE tutar: denetle()'nin çağırdığı her kapı burada
# olmak zorundadır.
#
# Kapının ARADIĞI ŞEYİN TÜRÜ kutupları ters çevirir ve bu, sözlükte AÇIKÇA
# beyan edilir (varsayılmaz):
#
#   yasak=False · kapı ZORUNLU bir şey arar (başlık, tarih, dayanak, onay,
#                 kaynak beyanı):  TAŞIYAN susturur, ANAN ateşler.
#   yasak=True  · kapı YASAK bir şey arar (müvekkil kimliği):
#                 TAŞIYAN ateşler, ANAN (yalnızca kuraldan söz eden) susar.
#
# Kutup beyan edilmeseydi sır kapısı için "anan ateşlemeli" diye sınanır ve
# takım kendi ölçütünü kırardı — ölçüt değil, çerçeve yanlış olurdu.
_AVUKAT = "## Yetkili avukat görüşü gereken konular\n- teyit\n"
_GORUS = "Bu işlem bildirime tabidir.\n\n" + _AVUKAT

CIFTLER = {
    "kapsam": dict(
        yasak=False, yol="deneme.md", disari=False,
        tasiyan="Bu işlem bildirime tabi değildir.\n\n" + _AVUKAT,
        anan="Bu işlem bildirime tabi değildir.\n\n"
             "Yukarıda yetkili avukat görüşü gereken konular başlığından söz "
             "edilmiştir ve bu başlık önemlidir.\n"),
    "guncellik": dict(
        yasak=False, yol="deneme.md", disari=False,
        tasiyan="Eşik 1.000.000.000 TL'dir (2010/4 sayılı Tebliğ m.7).\n"
                "Doğrulama: 2026-08-27\n"
                "Kontrol edildi: rekabet.gov.tr (2026-08-27)\n",
        # [Kendi kusurum] İlk anan metnim GERÇEK bir tarih taşıyordu; kapı
        # haklı olarak susuyordu ve ben bunu kapının kusuru sandım. Anan
        # metin, anılan şeyi TAŞIMAMALIDIR — yoksa sınadığı şey kendisidir.
        anan="Eşik 1.000.000.000 TL'dir (2010/4 sayılı Tebliğ m.7).\n"
             "Her eşik bir Doğrulama tarihi taşımalıdır; bu kural §3'te "
             "yazılıdır.\n"),
    "arastirma": dict(
        yasak=False, yol="deneme.md", disari=False,
        tasiyan="Depo https://github.com/google/diff-match-patch incelendi.\n"
                "Kontrol edildi: github.com (2026-08-27)\n",
        # [Kendi kusurum] İlk sürümde depo adı düz metindi ve kapının deposu
        # github.com alan adını arıyor: tetikleyici hiç kurulmamıştı, yani
        # kapı ateşlemediği için değil, ateşleyecek bir sebep olmadığı için
        # sessizdi. Tetiklenmemiş bir kapı, sınanmamış bir kapıdır.
        anan="Depo https://github.com/google/diff-match-patch incelendi.\n"
             "Kitap her çıktının bir Kontrol edildi satırıyla bitmesini "
             "ister.\n"),
    "kanit": dict(
        yasak=False, yol="deneme.md", disari=False,
        tasiyan="Eşik 1.000.000.000 TL'dir (2010/4 sayılı Tebliğ m.7).\n"
                "Kontrol edildi: rekabet.gov.tr (2026-08-27)\n",
        anan="Eşik 1.000.000.000 TL'dir.\n"
             "Her rakam yanında dayanağını taşır; bu kural §1'de yazılıdır.\n"
             "Kontrol edildi: rekabet.gov.tr (2026-08-27)\n"),
    "onay": dict(
        yasak=False, yol="cikti/nota.md", disari=True,
        tasiyan=_GORUS + "TASLAK — onaylanmamıştır.\n",
        # Olumsuzlanmış bir beyan, beyanın ANILMASIDIR: cümle belgenin NİHAİ
        # olduğunu söylüyor, yani §9'un tam da var olma sebebini kuruyor.
        anan=_GORUS + "Bu belge TASLAK DEĞİLDİR.\n"),
    "koltuk": dict(
        yasak=False, yol="birimler/_koltuklar/deneme.md", disari=False,
        tasiyan="# Deneme — KOLTUK BOŞ\n\nBu koltuk bilerek boştur.\n",
        anan="# Deneme\n\nBu koltuk KOLTUK BOŞ değildir.\n\n"
             "## Getirdiği mercek\nBir şey.\n"),
    "sir": dict(
        yasak=True, yol=None, disari=True,
        # TAŞIYAN: yasak şeyin KENDİSİ metinde — kapı ateşlemeli.
        tasiyan="Hedef Acme Gıda A.Ş. şirketidir.\n",
        # ANAN: yalnızca kuraldan söz ediyor, hiçbir kimlik taşımıyor —
        # kapı SUSMALI. Bu, kural 6'nın kendi öngördüğü soyutlanmış yoldur.
        anan="Kural 6 uyarınca hedefin unvanı, işlem kod adı ve bedel dışarı "
             "çıkmaz; sorgu hukuki soruya soyutlanır.\n"),
}


def _kod(ad):
    return "BL-%02d" % (1 + sorted(CIFTLER).index(ad))


for _ad in sorted(CIFTLER):
    _c = CIFTLER[_ad]
    _at = ates(_c["tasiyan"], yol=_c["yol"], disari=_c["disari"])
    _aa = ates(_c["anan"], yol=_c["yol"], disari=_c["disari"])
    if _c["yasak"]:
        _t, _a = (_ad in _at), (_ad not in _aa)
        _b = ("yasak şeyi TAŞIYAN ateşledi: %s · yalnızca ANAN sustu: %s"
              % (_t, _a))
    else:
        _t, _a = (_ad not in _at), (_ad in _aa)
        _b = "taşıyan susturdu: %s · anan ateşledi: %s" % (_t, _a)
    vaka(_kod(_ad), "%s kapısı anma ile taşımayı ayırt ediyor" % _ad,
         _t and _a, _b)

# --- BL-08 · ölçüt vakum değil ----------------------------------------
# Kapılar hiç ateşlemiyorsa yukarıdaki çiftler hiçbir şey sınamaz.
_hic = ates("Bu işlem bildirime tabi değildir. Eşik 1.000.000.000 TL.")
vaka("BL-08", "kapılar çıplak metinde gerçekten ateşliyor (vakum değil)",
     len(_hic) >= 2, "çıplak metinde ateşleyen kapı: %s" % sorted(_hic))

# --- BL-09 · kapı öz-sınaması bu ayrımı kendi de taşıyor --------------
# [Elli sekizinci tur] Ayrım kapının KENDİ öz-sınamasında yoksa, kapıyı
# değiştiren biri onu farkında olmadan geri alabilir.
_ks = open(os.path.join(_KOK, ".claude", "hooks", "kapi.py"),
           encoding="utf-8").read()
vaka("BL-09", "kapının öz-sınaması anma/taşıma ayrımını içeriyor",
     "anma başlık sayılmaz" in _ks and "gerçek başlık susturur" in _ks,
     "öz-sınamada ayrım vakaları: %s"
     % ("anma başlık sayılmaz" in _ks and "gerçek başlık susturur" in _ks))

# --- BL-10 · KEŞİFLE: hiçbir kapı bu taramanın dışında kalmıyor -------
# Elle yazılan liste ölçtüğü şeyden sürüklenir — P (TESLIMATLAR), M (önekler),
# R (terimler), BJ (birimler), Q (muafiyetler) ve bu takımın KENDİSİ aynı
# sınıfa düştü. Liste artık denetle()'nin gövdesinden KEŞFEDİLİR.
_govde = re.search(r"def denetle\(.*?if b\]", _ks, re.S)
KAPILAR = sorted(set(re.findall(r"kapi_([a-z_]+)\(",
                                _govde.group(0) if _govde else "")))
_eksik = [k for k in KAPILAR if k not in CIFTLER]
_fazla = [k for k in CIFTLER if k not in KAPILAR]
vaka("BL-10", "denetle()'nin çağırdığı her kapının anma/taşıma çifti var",
     bool(KAPILAR) and not _eksik and not _fazla,
     "kapılar %s · çifti olmayan: %s · artık çift: %s"
     % (KAPILAR or "KEŞFEDİLEMEDİ — ölçüt vakumda",
        _eksik or "yok", _fazla or "yok"))


BEKLENEN_VAKA = 10



def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BL-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
