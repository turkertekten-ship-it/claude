#!/usr/bin/env python3
"""KÖR SINAMA BE — kitabın KENDİ iç atıfları.

Yönelim (elli birinci tur). Son beş tur aparatı ve teslimatları sınadı.
Bu tur kitaba döndü ve hiç sorulmamış bir soruyu sordu: **kitap kendi
bölümlerine doğru atıf yapıyor mu?**

Kırk beşinci ve ellinci turlarda RAPOR'un işletim sözleşmesi KURALLARINI
bölüm numarası gibi andığı bulunmuştu (AY-02 bunu sürekli sınıyor). Aynı
ölçüt kitaba hiç uygulanmamıştı. Uygulanınca **bir örnek** çıktı:

    "Müvekkil bilgisi makinede kalır (işletim sözleşmesi §6)."

İşletim sözleşmesi kitabın §3'üdür; kuralları §3'ün İÇİNDE 1–11 diye
numaralanır ve 6. kural sır saklama kuralıdır. Kitabın kendi yazım geleneği
ise "§N" ile BÖLÜM'ü işaret eder (§12'deki kapı, §16'daki denetim). Sigili
izleyen okuyucu §6'ya, yani "Sınır ötesi katman"a gider — sır saklamayla
ilgisi olmayan bir bölüme. Kusur bu tek yerdedir ve kitabın metnindedir;
yamalanamaz, KİTAP-ERRATA'ya yazılır ve burada BEYANLI taban olarak durur.

Ayrıca bir ders: ölçüt önce §18.6 ile §18.9 atıflarımı "karşılıksız" saydı.
Değillerdi — §18'in maddeleri metinde "1.", "2." diye, noktadan sonra
BOŞLUKSUZ yazılmış ve çıkarıcı onları görmüyordu. Bir ölçüt kırmızıya
dönünce ilk şüpheli ölçüttür; bu kural iki geçerli atıfı "düzeltmekten"
kurtardı.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402
import kitap as kitapmod  # noqa: E402

_KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_DOCX = ("/root/.claude/uploads/a0f718bf-fd01-52d5-a508-48d77db2834c/"
         "0ca2aeab-RePieArelMAAvukatClaudeKurulumKitabi.docx")

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def oku(*p):
    y = os.path.join(_KOK, *p)
    return io.open(y, encoding="utf-8").read() if os.path.exists(y) else ""


K = kitapmod.metin()
DUZ = re.sub(r"\s+", " ", K)

# --- kitabın gerçek yapısı: Word'ün KENDİ biçeminden -------------------
# İlk sürüm yapıyı "^N. Başlık" desenine soruyordu. O desen yalnızca BOZUK
# metin üzerinde çalışıyordu: yumuşak satır sonları geri gelince numaralı
# liste maddeleri de satır başında "N." ile başladı ve başlıklardan ayırt
# edilemez oldu. Word bunu zaten biliyor — bölümler Heading2, alt bölümler
# Heading3 — ve yapı artık oradan okunuyor.
BOLUM = kitapmod.bolumler()
ALT = kitapmod.altbolumler()


def cozulur(atif):
    if atif in ALT:
        return True
    n, m = (int(x) for x in atif.split("."))
    return m in kitapmod.maddeler(n)


# --- BE-01 · her §N atfı var olan bir bölümü gösteriyor ----------------
_kirik = sorted({int(m.group(1)) for m in re.finditer(r"§\s*(\d{1,2})(?![0-9.])", DUZ)}
                - set(BOLUM))
vaka("BE-01", "kitabın her §N atfı var olan bir bölümü gösteriyor",
     not _kirik, "%d bölüm · var olmayan bölüme atıf: %s"
     % (len(BOLUM), _kirik or "yok"))

# --- BE-02 · kural numarası, bölüm sigiliyle anılmıyor -----------------
# İşletim sözleşmesinin kuralları §3'ün içindedir. "§N" onları değil, N.
# BÖLÜMÜ gösterir. AY-02 bunu RAPOR için sınıyor; bu vaka KİTAP için.
KURAL_KONU = {1: "kanıt", 2: "olumsuz iddia", 3: "güncellik|bayat",
              4: "cevapla başla", 5: "hukuki görüş", 6: "sır|müvekkil bilgisi",
              7: "iki hukuk", 8: "çatışma", 9: "onay", 10: "dil",
              11: "önce araştır"}
_karisan = []
for _n, _konu in KURAL_KONU.items():
    for _m in re.finditer(r"§\s*%d(?![0-9.])" % _n, DUZ):
        _b = max(DUZ.rfind(".", 0, _m.start()), DUZ.rfind(":", 0, _m.start())) + 1
        _s = DUZ.find(".", _m.end())
        _p = DUZ[_b:_s + 1 if _s > 0 else len(DUZ)]
        if re.search(_konu, _p, re.I):
            _karisan.append("§%d…%s" % (_n, _konu.split("|")[0]))
vaka("BE-02", "kitap, sözleşme kurallarını bölüm sigiliyle anmıyor",
     not _karisan,
     "karışma: %s — kitapta §6=%s, kural 6=sır saklama"
     % (sorted(set(_karisan)) or "yok", BOLUM.get(6, "?")))

# --- BE-03 · kitabın alt bölüm atıfları çözülüyor ----------------------
_alt = sorted({m.group(1) for m in re.finditer(r"§\s*(\d{1,2}\.\d{1,2})", DUZ)})
_coz = [a for a in _alt if not cozulur(a)]
vaka("BE-03", "kitabın her §N.M atfı gerçek bir maddeye çözülüyor",
     not _coz, "%d atıf: %s · çözülmeyen: %s" % (len(_alt), _alt, _coz or "yok"))

# --- BE-04 · teslimatların alt bölüm atıfları da çözülüyor -------------
_r = oku("RAPOR.md") + oku("KITAP-ERRATA.md")
_ralt = sorted({m.group(1) for m in re.finditer(r"§\s*(\d{1,2}\.\d{1,2})", _r)})
_rcoz = [a for a in _ralt if not cozulur(a)]
vaka("BE-04", "raporun her §N.M atfı kitapta gerçek bir maddeye çözülüyor",
     not _rcoz, "%d atıf · çözülmeyen: %s" % (len(_ralt), _rcoz or "yok"))

# --- BE-05 · çıkarıcı vakum değil --------------------------------------
# İlk çıkarıcı §18'in maddelerini hiç görmüyordu ve BE-04'ü yanlış kırmızı
# yapıyordu. Bu vaka, çıkarıcının gerçekten madde bulduğunu güvenceye alır.
_18 = len(kitapmod.maddeler(18))
vaka("BE-05", "çıkarıcı bölümleri, alt bölümleri ve maddeleri gerçekten buluyor",
     len(BOLUM) == 20 and len(ALT) == 18 and _18 == 9,
     "%d bölüm (Heading2) · %d alt bölüm (Heading3) · §18=%d madde"
     % (len(BOLUM), len(ALT), _18))


BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BE-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
