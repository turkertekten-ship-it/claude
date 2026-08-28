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
# Taşıyan metin kapıyı susturmalı; anan metin ateşlemeli.
CIFTLER = {
    "kapsam": (
        "Bu işlem bildirime tabi değildir.\n\n"
        "## Yetkili avukat görüşü gereken konular\n- teyit\n",
        "Bu işlem bildirime tabi değildir.\n\n"
        "Yukarıda yetkili avukat görüşü gereken konular başlığından söz "
        "edilmiştir ve bu başlık önemlidir.\n"),
    "guncellik": (
        "Eşik 1.000.000.000 TL'dir (2010/4 sayılı Tebliğ m.7).\n"
        "Doğrulama: 2026-08-27\n"
        "Kontrol edildi: rekabet.gov.tr (2026-08-27)\n",
        # [Kendi kusurum] İlk anan metnim GERÇEK bir tarih taşıyordu; kapı
        # haklı olarak susuyordu ve ben bunu kapının kusuru sandım. Anan
        # metin, anılan şeyi TAŞIMAMALIDIR — yoksa sınadığı şey kendisidir.
        "Eşik 1.000.000.000 TL'dir (2010/4 sayılı Tebliğ m.7).\n"
        "Her eşik bir Doğrulama tarihi taşımalıdır; bu kural §3'te yazılıdır.\n"),
    "arastirma": (
        "Depo https://github.com/google/diff-match-patch incelendi.\n"
        "Kontrol edildi: github.com (2026-08-27)\n",
        # [Kendi kusurum] İlk sürümde depo adı düz metindi ve kapının deposu
        # github.com alan adını arıyor: tetikleyici hiç kurulmamıştı, yani
        # kapı ateşlemediği için değil, ateşleyecek bir sebep olmadığı için
        # sessizdi. Tetiklenmemiş bir kapı, sınanmamış bir kapıdır.
        "Depo https://github.com/google/diff-match-patch incelendi.\n"
        "Kitap her çıktının bir Kontrol edildi satırıyla bitmesini ister.\n"),
}


def _kod(ad):
    return "BL-%02d" % (1 + sorted(CIFTLER).index(ad))


_sonuc = {}
for _ad in sorted(CIFTLER):
    _tasiyan, _anan = CIFTLER[_ad]
    _t = _ad not in ates(_tasiyan)      # taşıyan susturmalı
    _a = _ad in ates(_anan)             # anan ateşlemeli
    _sonuc[_ad] = (_t, _a)
    vaka(_kod(_ad), "%s kapısı anma ile taşımayı ayırt ediyor" % _ad,
         _t and _a,
         "taşıyan susturdu: %s · anan ateşledi: %s" % (_t, _a))

# --- BL-04 · ölçüt vakum değil ----------------------------------------
# Kapılar hiç ateşlemiyorsa yukarıdaki çiftler hiçbir şey sınamaz.
_hic = ates("Bu işlem bildirime tabi değildir. Eşik 1.000.000.000 TL.")
vaka("BL-04", "kapılar çıplak metinde gerçekten ateşliyor (vakum değil)",
     len(_hic) >= 2, "çıplak metinde ateşleyen kapı: %s" % sorted(_hic))

# --- BL-05 · kapı öz-sınaması bu ayrımı kendi de taşıyor --------------
# [Elli sekizinci tur] Ayrım kapının KENDİ öz-sınamasında yoksa, kapıyı
# değiştiren biri onu farkında olmadan geri alabilir.
_ks = open(os.path.join(_KOK, ".claude", "hooks", "kapi.py"),
           encoding="utf-8").read()
vaka("BL-05", "kapının öz-sınaması anma/taşıma ayrımını içeriyor",
     "anma başlık sayılmaz" in _ks and "gerçek başlık susturur" in _ks,
     "öz-sınamada ayrım vakaları: %s"
     % ("anma başlık sayılmaz" in _ks and "gerçek başlık susturur" in _ks))


BEKLENEN_VAKA = 5


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
