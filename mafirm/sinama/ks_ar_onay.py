#!/usr/bin/env python3
"""KÖR SINAMA AR — onay ihtiyacının BEYANI ile onayın KENDİSİ.

Yönelim (otuz altıncı tur). Otuz beşinci turun taraması her kontrolü "neye
bağlı" diye sınıfladı. Sormadığı soru şu: bir kontrol, ONAY GEREKTİĞİNİ
söylemekle ONAYIN VERİLDİĞİNİ kaydetmeyi ayırt edebiliyor mu?

§9 açık: "Şu çıktılar ADI BELLİ BİR İNSAN ONAYLAMADAN KULLANILMAZ: müvekkile
ya da karşı tarafa gidecek her şey, her başvuru metni, yönetim kuruluna
sunulacak her rakam ve süreye bağlı bir adımda dayanılacak her Türk hukuku
beyanı."

§12'nin kapsam kapısı ise "Yetkili avukat görüşü gereken konular" BAŞLIĞININ
varlığını arıyor. O başlık bir onay kaydı değil, onay İHTİYACININ beyanıdır —
tam tersi. Ölçüldü: müvekkile giden, başlığı taşıyan, hiçbir onay kaydı
olmayan bir metin dışarı giden yolda HİÇBİR kapıya takılmıyor.

Kitap onay verecek kişinin ADINI kaydediyor (§9'un `dosya-ac` KAPSAM.md
şablonunda "İnsan onayı verecek kişi"). Yani sistem kimin onaylayacağını
biliyor; onayladığını hiçbir yerde kaydetmiyor. Söz ile kayıt arasındaki
fark, bu incelemenin baştan beri ölçtüğü farkın ta kendisi.
"""
import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    "kapi_ar", os.path.join(_KOK_COZ, ".claude/hooks/kapi.py"))
kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapi)

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def oku(*p):
    try:
        with open(os.path.join(_KOK_COZ, *p), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


# §9 sınıfına giren, müvekkile gidecek, onaysız bir çıktı.
ONAYSIZ = """Müvekkile giden not

Bu işlem bildirime tabidir ve Kurul'a başvurulmalıdır.

## Şimdi ne yapılmalı
Başvuru hazırlanır.

## Yetkili avukat görüşü gereken konular
Hepsi.

Kontrol edildi: mevzuat (2026-08-27)
"""

# --- AR-01 · DİNAMİK: onaysız §9 çıktısı kapıya takılıyor mu ---------
_bulunan = {k for k, _ in kapi.denetle(ONAYSIZ, True, None)}
vaka("AR-01", "onay kaydı olmayan §9 çıktısı dışarı giden yolda yakalanıyor",
     "onay" in _bulunan,
     "müvekkile giden, başlıklı, ONAYSIZ metinde ateşleyen kapılar: %s — "
     "başlık onayın beyanıdır, kaydı değil" % (sorted(_bulunan) or "hiçbiri"))

# --- AR-02 · sistemde bir ONAY KAYDI biçimi tanımlı mı --------------
# Bir kayıt biçimi olmadan "onaylandı" iddiası doğrulanamaz. §9 "adı belli
# bir insan" diyor: kayıt bir AD ve bir TARİH taşımalı.
_kaynaklar = (oku("CLAUDE.md"), oku(".claude", "hooks", "kapi.py"),
              oku(".claude", "skills", "dosya-ac", "SKILL.md"))
_bicim = any(re.search(r"Onay(?:layan)?\s*:", m) for m in _kaynaklar)
vaka("AR-02", "onay kaydı için bir biçim tanımlı",
     _bicim,
     "hiçbir yerde 'Onay: <ad> · <tarih>' türü bir kayıt biçimi yok; "
     "sistem kimin onaylayacağını biliyor, onayladığını bilmiyor")

# --- AR-03 · OLUMLU KONTROL: onaylayacak kişi kaydediliyor ----------
_kim = re.search(r"[İI]nsan onayı verecek kişi",
                 oku(".claude", "skills", "dosya-ac", "SKILL.md")) is not None
vaka("AR-03", "dosya açılırken onayı verecek kişi kaydediliyor",
     _kim, "KAPSAM.md şablonunda 'İnsan onayı verecek kişi' var" if _kim
     else "onaylayacak kişi kaydedilmiyor")

# --- AR-04 · OLUMLU KONTROL: bu inceleme kendi §9'una uyuyor --------
# Rapor, onaylanmadığını AÇIKÇA yazmak zorunda. Kendi kuralına uymayan bir
# inceleme, kuralı ölçemez.
RAPOR = oku("RAPOR.md")
_kendi = re.search(r"adı belli bir insan tarafından\s+onaylanmamıştır",
                   re.sub(r"\s+", " ", RAPOR), re.I) is not None
vaka("AR-04", "bu raporun kendisi onaylanmadığını açıkça yazıyor",
     _kendi, "rapor §9'a uyuyor" if _kendi
     else "rapor onay durumunu beyan etmiyor")

# --- AR-05 · YANLIŞ POZİTİF: onay kaydı taşıyan çıktı geçmeli -------
# Bir kapı, doğru olanı da bloklarsa kullanılmaz hâle gelir (V takımının
# dersi). Onay kaydı taşıyan aynı metin susmalı.
ONAYLI = ONAYSIZ.replace("Kontrol edildi:",
                         "Onay: Av. A. Yılmaz · 2026-08-28\nKontrol edildi:")
_bulunan2 = {k for k, _ in kapi.denetle(ONAYLI, True, None)}
vaka("AR-05", "onay kaydı taşıyan aynı çıktı onay kapısına takılmıyor",
     "onay" not in _bulunan2,
     "onaylı metinde ateşleyen kapılar: %s" % (sorted(_bulunan2) or "hiçbiri"))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AR-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
