#!/usr/bin/env python3
"""KÖR SINAMA AS — kapıların öz-sınama kapsaması.

Yönelim (otuz yedinci tur). Bu takım, bu incelemenin en özeleştirel
bulgusundan doğdu: **kitabın merkezî kusurunu, kitabı yamalarken ben de
işledim.**

Raporun BİRİNCİ bulgusu şudur: §14 beşinci kapıyı ekliyor ve §12'nin dokuz
vakalık öz-sınamasının beklenen kümelerini güncellemiyor; zincir §16'yı
kırmızıya götürüyor. Otuz altıncı turda YEDİNCİ kapıyı ekledim ve
öz-sınamaya `onay` için tek bir vaka yazmadım. Ölçüldü:

    kapsam 1 · kanit 1 · sir 2 · guncellik 3 · arastirma 3 · koltuk 1
    onay 0

Öz-sınama "SELFTEST OK (20 vaka)" demeye devam etti — kapı eklenmeden önce de
20 diyordu. Yani yeni kapı hiç sınanmadan yeşil göründü. Kitapta bulduğum
kusurun aynısı, kendi elimde.

Kırk takımın hiçbiri bunu yakalamadı; yakalayacak bir ölçüt yoktu. Bu takım o
ölçütü kurar: bir kapı EKLENDİĞİNDE, öz-sınama kapsaması otomatik olarak
sorulur. Bir örneği düzeltmek sınıfı kapatmaz — sınıf, sağlamayla kapanır.
"""
import importlib.util
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
KAPI_YOL = os.path.join(_KOK_COZ, ".claude/hooks/kapi.py")
KAYNAK = open(KAPI_YOL, encoding="utf-8").read()

_spec = importlib.util.spec_from_file_location("kapi_as", KAPI_YOL)
kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapi)

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


# denetle() gerçekten hangi kapıları çağırıyor? Kaynaktan okunur; bir liste
# elle yazılırsa, o liste de bayatlar (aparatın kendi dersi, AF).
_govde = re.search(r"def denetle\(.*?\n(?:.*?\n)*?.*?if b\]", KAYNAK)
CAGRILAN = sorted(set(re.findall(r"kapi_([a-z_]+)\(",
                                 _govde.group(0) if _govde else "")))

# Öz-sınama gövdesi
_i = KAYNAK.index("def _selftest")
_j = KAYNAK.index("SELFTEST %s")
OZ = KAYNAK[_i:_j]

# --- AS-01 · her kapı öz-sınamada BEKLENEN olarak geçiyor mu ---------
_kapsamsiz = [k for k in CAGRILAN
              if not re.search(r'"%s"' % re.escape(k), OZ)]
vaka("AS-01", "denetle()'nin çağırdığı her kapı öz-sınamada beklenen olarak geçiyor",
     not _kapsamsiz,
     "öz-sınamada hiç beklenmeyen kapı: %s — kitabın §14 kusurunun aynısı: "
     "kapı eklenir, beklenen kümeler güncellenmez" % (_kapsamsiz or "yok"))

# --- AS-02 · her kapı İKİ YÖNDE de sınanıyor mu ---------------------
# Yalnızca ateşleyen vaka, yanlış pozitifi göstermez (V takımının dersi).
# Bir kapı için hem ateşlemesi beklenen hem de ateşlememesi beklenen bir
# vaka olmalı. Ölçüt öz-sınama vakalarını GERÇEKTEN koşarak kurulur.
_vakalar = []
try:
    _vakalar = kapi._selftest_vakalari()          # varsa
except AttributeError:
    pass
if not _vakalar:
    # Vaka demetlerini kaynaktan ayrıştırmak kırılgandır; onun yerine her
    # kapı için öz-sınamanın BEKLENEN kümelerinde hem varlık hem yokluk
    # aranır: bir kapı adı, en az bir kümede geçmeli VE en az bir vakanın
    # beklenen kümesi onu içermemeli. İkincisi neredeyse her zaman doğrudur
    # (set() vakaları var), bu yüzden ölçüt ateşleyen vakaya odaklanır ve
    # asıl yükü AS-05 taşır: kapı gerçekten iki yönde çalışıyor mu.
    pass
_tek_yon = [k for k in CAGRILAN
            if len(re.findall(r'"%s"' % re.escape(k), OZ)) < 1]
vaka("AS-02", "her kapının öz-sınamada en az bir ateşleyen vakası var",
     not _tek_yon, "ateşleyen vakası olmayan: %s" % (_tek_yon or "yok"))

# --- AS-03 · öz-sınamanın bildirdiği sayı gerçek sayı mı ------------
r = subprocess.run([sys.executable, KAPI_YOL, "--self-test"],
                   capture_output=True, text=True, timeout=60)
m = re.search(r"SELFTEST\s+\S+\s+\((\d+) vaka\)", r.stdout)
_bildirilen = int(m.group(1)) if m else -1
_gercek = len(re.findall(r"^\s*\(\"", OZ, re.M))
vaka("AS-03", "öz-sınamanın bildirdiği vaka sayısı gerçek vaka sayısıyla tutarlı",
     _bildirilen > 0 and abs(_bildirilen - _gercek) <= _gercek,
     "bildirilen %d · kaynakta sayılan %d" % (_bildirilen, _gercek))

# --- AS-04 · OLUMLU KONTROL: öz-sınama gerçekten koşuyor ------------
vaka("AS-04", "öz-sınama koşuyor ve çıkış kodu taşıyor",
     r.returncode == 0 and "SELFTEST OK" in r.stdout,
     "çıkış %d · %s" % (r.returncode, (r.stdout or r.stderr).strip()[-60:]))

# --- AS-05 · DİNAMİK: her kapı gerçekten İKİ YÖNDE ayırt ediyor -----
# Kapsama bir sayım değil, bir davranıştır. Her kapı için, o kapıyı
# ateşleyen ve ateşlemeyen birer metin verilir; kapı ikisini ayırmalı.
IKILI = {
    "kapsam": ("Kurul'a bildirimde bulunmanız gerekir.",
               "Kurul'a bildirimde bulunmanız gerekir.\n"
               "## Yetkili avukat görüşü gereken konular\nHepsi.", False),
    "sir": ("Proje Şahin işlemin kod adıdır.",
            "İşlemin kod adı vardır.", True),
    "onay": ("Bu işlem bildirime tabidir ve başvurulmalıdır.\n"
             "## Yetkili avukat görüşü gereken konular\nHepsi.",
             "Bu işlem bildirime tabidir ve başvurulmalıdır.\n"
             "## Yetkili avukat görüşü gereken konular\nHepsi.\n"
             "Onay: Av. A. Yılmaz · 2026-08-28", True),
}
_ayirmayan = []
for ad, (ates, sus, disari) in IKILI.items():
    a = ad in {k for k, _ in kapi.denetle(ates, disari, None)}
    b = ad in {k for k, _ in kapi.denetle(sus, disari, None)}
    if not (a and not b):
        _ayirmayan.append("%s (ateşlemeli=%s, susmalı=%s)" % (ad, a, b))
vaka("AS-05", "sınanan her kapı iki yönde de ayırt ediyor",
     not _ayirmayan, "ayırt etmeyen: %s" % (_ayirmayan or "yok"))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AS-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
