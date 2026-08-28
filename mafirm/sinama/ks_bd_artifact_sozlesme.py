#!/usr/bin/env python3
"""KÖR SINAMA BD — yayımlanan belgenin işletim sözleşmesine uyumu.

Yönelim (ellinci tur). Kırk sekiz ve kırk dokuzuncu turlar aynı biçimi iki
kez gösterdi: bir ölçüt teslimatlardan BİRİNE uygulanmış, ötekine değil.
Yirmi yedinci turun kuralı gereği üçüncü örnek bir sınıftır — ve üçüncüsü
aranınca en ağırı çıktı.

R takımı raporun §4 (cevapla başla), §5 (iki zorunlu kapanış başlığı) ve
§9 (onay durumu) uyumunu kırk dokuz tur boyunca sınadı. **Artifact hiç
sınanmadı.** Ölçülünce görüldü ki yayımlanan belge — okuyucunun açtığı,
paylaşabildiği belge — şunları taşımıyordu:

  * §5'in "Şimdi ne yapılmalı" başlığı: YOK
  * §5'in kapsam beyanı ("hukuki görüş değildir"): YOK
  * §9'un onay durumu beyanı: YOK
  * ve belge iki zorunlu başlıkla BİTMİYORDU

"Yetkili avukat görüşü" ifadesi belgede geçiyordu — ama bir BAŞLIK olarak
değil, §12'nin kapısını ANLATAN bir cümlenin içinde. Yirmi dokuzuncu turdan
beri tekrarlayan sınıfın bir kez daha görünüşü: **anmak, taşımak değildir.**

Bu, biçimsel bir eksiklik değildir. §5 ile §9 tam olarak bu belgenin
paylaşılabilir olması için vardır: hukuki analiz gibi okunan, kaydedilip
iletilebilen bir metin, "bu hukuki görüş değildir" ve "onaylanmamıştır"
demeden dolaşıma girmemelidir.
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


HAM = oku("kor-sinama-raporu.html")

# Başlıklar YAPIDAN okunur, düzyazıdan değil: bir cümlenin içinde geçen
# "Yetkili avukat görüşü" bir başlık DEĞİLDİR. [anmak ≠ taşımak]
BASLIKLAR = [re.sub(r"<[^>]+>", "", m.group(1)).strip()
             for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", HAM, re.S)]

ZORUNLU = ["Şimdi ne yapılmalı", "Yetkili avukat görüşü gereken konular"]


def duz(metin):
    metin = re.sub(r"<style.*?</style>|<script.*?</script>", " ", metin, flags=re.S)
    metin = re.sub(r"<[^>]+>", " ", metin)
    return re.sub(r"\s+", " ", metin)


DUZ = duz(HAM)

# --- BD-01 · iki zorunlu başlık VAR, BAŞLIK olarak ---------------------
_eksik = [b for b in ZORUNLU if b not in BASLIKLAR]
vaka("BD-01", "§5'in iki zorunlu başlığı gerçek başlık olarak var",
     not _eksik, "eksik: %s · toplam %d h2" % (_eksik or "yok", len(BASLIKLAR)))

# --- BD-02 · ve belgenin SONUNDA, bu sırayla ---------------------------
# §5 "biter" der. Sondan iki başlık, sırasıyla bunlar olmalı.
_son_iki = BASLIKLAR[-2:] if len(BASLIKLAR) >= 2 else BASLIKLAR
vaka("BD-02", "belge iki zorunlu başlıkla ve doğru sırayla bitiyor",
     _son_iki == ZORUNLU, "son iki başlık: %s" % (_son_iki,))

# --- BD-03 · §5 kapsam beyanı ------------------------------------------
KAPSAM = re.compile(r"hukuki görüş değil", re.I)
vaka("BD-03", "§5 kapsam beyanı yazılı (hukuki görüş değildir)",
     bool(KAPSAM.search(DUZ)), "bulundu: %s" % bool(KAPSAM.search(DUZ)))

# --- BD-04 · §9 onay durumu --------------------------------------------
# [AR takımının kuralı] Kusur, onayın YOKLUĞU değil, onay durumu hakkındaki
# SESSİZLİKTİR. Belge ya onaylandığını ya da onaylanmadığını söylemelidir.
ONAY = re.compile(r"onaylanmamıştır|onaylanmadan|onay bekliyor|TASLAK", re.I)
vaka("BD-04", "§9 onay durumu açıkça yazılı",
     bool(ONAY.search(DUZ)), "bulundu: %s" % bool(ONAY.search(DUZ)))

# --- BD-05 · ikinci başlık BOŞ değil -----------------------------------
# §5: "Gerçek bir dosyada ikinci başlık asla boş kalmaz."
_i = HAM.find(ZORUNLU[1])
_govde = HAM[_i:HAM.find("</section>", _i)] if _i > 0 else ""
_madde = len(re.findall(r"<li>", _govde))
vaka("BD-05", "yetkili avukat başlığı boş değil",
     _madde >= 5, "%d madde" % _madde)

# --- BD-06 · iki teslimat da cevabın İKİ YARISINI birden taşıyor -------
# İlk yazım raporun BİREBİR cümlesini artifact'te arıyordu. Yanlıştı: bu,
# ikinci belgeyi birincinin sözcüklerini tekrar etmeye zorlar ve ayrışmayı
# değil, üslubu ölçer. Ölçülmesi gereken İDDİADIR: cevabın iki yarısı —
# övgü ve kusur — ikisinde de bulunmalı. Yalnızca övgüyü taşıyan bir
# teslimat, okuyucuyu yanlış yere bırakır.
_r = oku("RAPOR.md")
OVGU = re.compile(r"iyi bir kitap", re.I)
KUSUR = re.compile(r"harfiyen izlen\w*[^.]{0,60}"
                   r"(dönmüyor|çalışmıyor|geçmiyor|geçemiyor)", re.I)
_eksik_yarim = []
for _ad, _m in (("RAPOR", _r), ("ARTIFACT", DUZ)):
    if not OVGU.search(_m):
        _eksik_yarim.append("%s: övgü yarısı yok" % _ad)
    if not KUSUR.search(_m):
        _eksik_yarim.append("%s: kusur yarısı yok" % _ad)
vaka("BD-06", "cevabın iki yarısı da her iki teslimatta var",
     not _eksik_yarim, "eksik: %s" % (_eksik_yarim or "yok"))


BEKLENEN_VAKA = 6


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BD-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
