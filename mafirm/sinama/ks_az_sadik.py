#!/usr/bin/env python3
"""KÖR SINAMA AZ — "kitaba sadık" kopyalar gerçekten kitaba sadık mı.

Yönelim (kırk dördüncü tur). Kırk bir, iki ve üçüncü turlar raporun kitap
hakkındaki SÖZLERİNİ sınadı: alıntılar, sayılar, olumsuz iddialar, atıflar.
Dördüncü kardeş: raporun kitabın KODU hakkındaki iddiaları — ve onların
dayandığı taban.

Raporun bütün ÖNCE/SONRA karşılaştırması `yamalar/kitaba-sadik/` altındaki
kopyalara dayanıyor. AG-01..05 o dosyaların var olduğunu, canlı sürümden
farklı olduğunu ve kitabın bilinen kusurlarını taşıdığını ölçüyor — ama
hiçbiri **kitabın metniyle** karşılaştırmıyordu. Yani "sadık" sıfatı kırk üç
tur boyunca sınanmamış bir iddiaydı, üstelik raporun bütün "önce" ölçümleri
onun üstünde duruyordu.

Karşılaştırıldı: 262 esaslı satırın 258'i kitapta birebir bulundu. Kalan
dördü `kapi.py`nin beş kapılı `denetle()` bölümünde: §12 fonksiyonu DÖRT
kapıyla basıyor, §14 beşinciyi verip "denetle() içine diğer dördün yanına
eklenir" diyor — yani kitap sonucu basmıyor, TALİMATI veriyor. O dört satır
kitabın harfi değil, kitabın talimatının uygulanmış hâli.

Uydurma değiller; ama "kitabın metni" de değiller ve fark yazılmalı — kırk
birinci turda kendi yamamı kitabın metni sanıp kitaba kredi vermiştim.
Beyan `yamalar/kitaba-sadik/TURETME.md` içinde; bu takım hem beyanı hem de
beyan edilmeyen her satırı sınar.
"""
import html
import io
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402
from kitap import metin as kitap_metni_ortak  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_SADIK = os.path.join(_KOK_COZ, "yamalar", "kitaba-sadik")
_DOCX = ("/root/.claude/uploads/a0f718bf-fd01-52d5-a508-48d77db2834c/"
         "0ca2aeab-RePieArelMAAvukatClaudeKurulumKitabi.docx")

# Kitabın BASTIĞI dosyalar. Sonradan eklenen beceri kopyaları (dosya-ac,
# kapanis-listesi, yaptirim-taramasi, esik-denetle) kitapta kod bloğu olarak
# değil düzyazı/beceri metni olarak geçiyor; onlar AW'nin alanı.
DOSYALAR = {"esik.py": 12, "kapi.py": 12, "denetim.sh": 12,
            "settings.json": 12, "tr-esikler.md": 12, "gitignore": 6}

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def kitap():
    """[BE/AW, 51. tur] Ortak çıkarıcı. Eski yerel sürüm Word'ün
    yumuşak satır sonunu (<w:br/>) siliyordu ve iki yanındaki
    sözcükleri YAPIŞTIRIYORDU; kitaba yapılan birebir aramalar bir
    satır sonunu geçtiğinde sessizce başarısız oluyordu."""
    return kitap_metni_ortak()


def duz(s):
    return re.sub(r"\s+", " ", s).strip()


K = kitap()
KN = duz(K) if K else None
TUR = os.path.join(_SADIK, "TURETME.md")
TURETME = io.open(TUR, encoding="utf-8").read() if os.path.exists(TUR) else ""

# Beyan tablosundan türetilmiş satırlar: | dosya | satır | `metin` | dayanak |
BEYAN = {}
for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|"
                     r"\s*([^|]+)\|", TURETME, re.M):
    BEYAN[(m.group(1).strip(), int(m.group(2)))] = (m.group(3).strip(),
                                                    m.group(4).strip())

if KN is None:
    for k, b in (("AZ-01", "her sadık satır kitapta ya da beyanda"),
                 ("AZ-02", "her türetme beyanı dayanağını yazıyor"),
                 ("AZ-03", "beyan listesi kaçış deliği değil"),
                 ("AZ-04", "ölçüt gerçekten satır sınıyor")):
        vaka(k, b, False, "kitap kaynağı yok — DOĞRULANAMADI")
else:
    _eksik, _toplam = [], 0
    for ad, esik in DOSYALAR.items():
        yol = os.path.join(_SADIK, ad)
        if not os.path.exists(yol):
            _eksik.append("%s: dosya yok" % ad)
            continue
        for no, satir in enumerate(
                io.open(yol, encoding="utf-8").read().splitlines(), 1):
            s = satir.strip()
            if len(s) < esik:
                continue
            _toplam += 1
            if duz(s) in KN:
                continue
            if (ad, no) in BEYAN:
                continue
            _eksik.append("%s:%d %r" % (ad, no, s[:46]))

    # --- AZ-01 · her satır ya kitapta ya beyanda ---------------------
    vaka("AZ-01", "kitaba sadık her satır kitapta birebir ya da beyanlı",
         not _eksik,
         "%d satır sınandı · beyansız ve kitapta yok: %s"
         % (_toplam, "; ".join(_eksik[:3]) if _eksik else "yok"))

    # --- AZ-02 · her beyan DAYANAĞINI yazıyor ------------------------
    # "Türetilmiş" demek yetmez: hangi talimatın uygulandığı yazılmalı.
    _dayanaksiz = [k for k, (m, d) in BEYAN.items() if len(d) < 15]
    _talimat = duz("denetle() içine diğer dördün yanına eklenir") in KN
    vaka("AZ-02", "her türetme beyanı kitaptaki talimata dayanıyor",
         BEYAN and not _dayanaksiz and _talimat,
         "%d beyan · dayanaksız: %s · §14 talimatı kitapta: %s"
         % (len(BEYAN), _dayanaksiz or "yok", _talimat))

    # --- AZ-03 · beyan bir KAÇIŞ DELİĞİ değil ------------------------
    # Beyan edilen bir satır kitapta GEÇİYORSA, gereksiz yere muaf
    # tutulmuş demektir — liste küçük ve dürüst kalmalı.
    _gereksiz = [k for k, (m, d) in BEYAN.items() if duz(m) in KN]
    vaka("AZ-03", "beyan edilen hiçbir satır aslında kitapta değil",
         not _gereksiz, "kitapta olduğu hâlde beyanlı: %s" % (_gereksiz or "yok"))

    # --- AZ-04 · OLUMLU KONTROL: ölçüt vakum değil -------------------
    vaka("AZ-04", "ölçüt gerçekten satır sınıyor (vakum değil)",
         _toplam >= 200, "%d esaslı satır kitapla karşılaştırıldı" % _toplam)


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 4


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AZ-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
