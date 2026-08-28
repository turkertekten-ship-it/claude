#!/usr/bin/env python3
"""KÖR SINAMA AM — kararın hukuki sürümü ve geriye dönük geçersizleşme.

Yönelim (otuz birinci tur). Otuzuncu tura kadar ölçülen her şey APARATIN
kendisiyle ilgiliydi. Bu takım İŞ ÜRÜNÜNE bakar: bir eşik değişince, o
eşiğe dayanarak verilmiş görüşe ne oluyor?

Kitap riski KENDİ SÖZLERİYLE adlandırıyor. §11'in `/esik-denetle` komutu
şöyle diyor:

    "Hiçbir dosyayı düzenleme — bir eşik değişikliği insan kararıdır, çünkü
     CANLI BİR DOSYADA VERİLMİŞ BİR GÖRÜŞÜ GEÇERSİZ KILABİLİR."

ve şöyle bitiyor:

    "Şununla bitir: kaç eşik kontrol edildi, kaçı bayat ve ŞU ANDA HANGİ
     DOSYALAR bayat bir rakama dayanıyor."

Ama prosedürünün birinci adımı yalnızca şurayı tarıyor:

    "`birimler/*/yontem/` altındaki 'Doğrulama:' satırı taşıyan her dosya"

§2 kitabın kendi sözlüğünü kuruyor: "dosyalar/ CANLI İŞLERİ ... tutar".
Yani kapanış cümlesinin vaadi canlı işler üzerinde; prosedürü ise o dizini
HİÇ AÇMIYOR. Vaadin kapsamı ile prosedürün kapsamı ayrışıyor.

Ve ikinci yol da kapalı: `dosyalar/` kural 6 gereği `.gitignore`'dadır
(Y-02 yaması), yani sürüm geçmişinden de sorulamaz. "Eşik değişti, hangi
müvekkile yanlış şey söyledik?" sorusunun sistemde İKİ cevap yolu vardı ve
ikisi de kapalıydı.

Bu, otuzuncu turun §2 bulgusunun ikinci yüzüdür: gizlilik mekanizması
dayanıklılığı feda ediyordu; burada da GERİYE DÖNÜK ERİŞİMİ feda ediyor.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def oku(*parca):
    yol = os.path.join(_KOK_COZ, *parca)
    try:
        with open(yol, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


KOMUT = oku(".claude", "commands", "esik-denetle.md")

# [AE sınıfı · kendi kusurum] İlk sürüm vaadi `hangi dosyalar[^\n]*bayat`
# diye arıyordu. Komutun kapanış cümlesi tam da o iki kelimenin ARASINDA
# satır kırıyor ("...hangi dosyalar\nbayat bir rakama dayanıyor."), desen
# eşleşmedi ve AM-01 VAKUM olarak yeşile döndü. Yirmi dokuzuncu turda AI-02
# aynı tuzağı yakalamıştı; satır kırılması bir metnin anlamını değiştirmez,
# ölçütün ona duyarlı olması bir ölçüm kusurudur. Boşluklar düzleştirilir.
# [AF-02 sınıfı · kendi kusurum] Ölçüt önce `dosyalar/` dizgesini METNİN
# HERHANGİ BİR YERİNDE arıyordu — yamayı açıklayan HTML yorumu dâhil.
# Mutasyonda prosedür silinse bile yorum kalıyor ve vaka yeşil kalıyordu:
# yani ölçüt PROSEDÜRÜ değil, prosedürden söz eden bir cümleyi ölçüyordu.
# Yorumlar atılır; kalan metin işin kendisidir.
def _yorumsuz(metin):
    return re.sub(r"<!--.*?-->", " ", metin, flags=re.S)


KOMUT_DUZ = re.sub(r"\s+", " ", _yorumsuz(KOMUT))

# --- AM-01 · vaadin kapsamı ile prosedürün kapsamı ---------------------
# Komut "hangi DOSYALAR bayat bir rakama dayanıyor" diye bitiyorsa,
# prosedürü `dosyalar/` dizinini taramak ZORUNDADIR. Ölçüt komutun KENDİ
# kapanış cümlesinden gelir; dışarıdan bir şart uydurulmuyor.
_vaat = re.search(r"hangi dosyalar.{0,40}bayat", KOMUT_DUZ, re.I) is not None
_tarama = re.search(r"(^|[^/\w])dosyalar/", KOMUT_DUZ) is not None
vaka("AM-01", "eşik denetiminin vaadi ile taradığı kapsam örtüşüyor",
     (not _vaat) or _tarama,
     "kapanış 'hangi dosyalar' diyor=%s · prosedür dosyalar/ tarıyor=%s"
     % (_vaat, _tarama))

# --- AM-02 · OLUMLU KONTROL: bayatlığı fark eden mekanizma var ---------
# Bulgu "hiç mekanizma yok" değil, "mekanizmanın erişimi eksik". Aradaki
# fark önemli: birincisi kitabı haksız yere ağır suçlar.
_mekanizma = ("Doğrulama:" in KOMUT_DUZ and "BAYAT" in KOMUT_DUZ
              and re.search(r"birincil kayna", KOMUT_DUZ, re.I) is not None)
vaka("AM-02", "eşik bayatlığını fark eden bir mekanizma var",
     _mekanizma,
     "komut Doğrulama: satırını okuyup birincil kaynakla karşılaştırıyor"
     if _mekanizma else "mekanizma bulunamadı")

# --- AM-03 · geriye dönük erişimin İKİ yolu ----------------------------
# (a) canlı işleri tarayan bir mekanizma, (b) sürüm geçmişi. En az biri
# açık olmalı; ikisi birden kapalıysa soru sorulamaz hâle gelir.
_tarayan = []
for kok, _d, dosyalar in os.walk(os.path.join(_KOK_COZ, ".claude")):
    for ad in dosyalar:
        if not ad.endswith(".md"):
            continue
        icerik = _yorumsuz(open(os.path.join(kok, ad), encoding="utf-8",
                                errors="replace").read())
        # dosyalar/ tarayan VE bayat/eşik bağlamı taşıyan
        if re.search(r"(^|[^/\w])dosyalar/", icerik) and \
           re.search(r"bayat|eşik", icerik, re.I):
            _tarayan.append(ad)

_git_gormuyor = True
try:
    r = subprocess.run(["git", "-C", _KOK_COZ, "check-ignore", "dosyalar/"],
                       capture_output=True, text=True, timeout=30)
    _git_gormuyor = (r.returncode == 0)      # 0 = yok sayılıyor
except (OSError, subprocess.SubprocessError):
    _git_gormuyor = True

_acik = bool(_tarayan) or (not _git_gormuyor)
vaka("AM-03", "eşik değişince eski görüşe ulaşmanın en az bir yolu açık",
     _acik,
     "canlı işleri bayatlık için tarayan: %s · sürüm geçmişi görüyor: %s"
     % (_tarayan or "yok", not _git_gormuyor))

# --- AM-04 · bayatlık eşiği TEK sayı mı --------------------------------
# §3 "altı ay", komut "altı aydan eski", kapı BAYAT_GUN. Üçü ayrışırsa bir
# çıktı bir yerde bayat, başka yerde taze sayılır.
KAPI = oku(".claude", "hooks", "kapi.py")
m = re.search(r"^BAYAT_GUN\s*=\s*(\d+)", KAPI, re.M)
_gun = int(m.group(1)) if m else None
_komut_alti_ay = re.search(r"altı ay", KOMUT_DUZ, re.I) is not None
_uyumlu = _gun is not None and 175 <= _gun <= 190 and _komut_alti_ay
vaka("AM-04", "bayatlık eşiği kapı ile komutta aynı süreyi anlatıyor",
     _uyumlu,
     "kapı BAYAT_GUN=%s · komut 'altı ay' diyor=%s" % (_gun, _komut_alti_ay))

# --- AM-05 · sonucun hangi mevzuat sürümüyle verildiği yazılıyor mu ----
# §3 güncellik kuralı: "çıktı hangi tarihte kontrol edildiğini yazar".
# Hesap aracı bunu yapıyor mu — yani sonucun yanında sürüm/tarih var mı?
ESIK = oku("birimler", "rekabet", "kod", "esik.py")
_surum = re.search(r"20\d\d/\d+\s*sayılı Tebliğ", ESIK) is not None
_tarih = re.search(r"^DOGRULAMA\s*=", ESIK, re.M) is not None
_yazdiriyor = re.search(r"print\([^)]*DOGRULAMA|DOGRULAMA[^\n]*print", ESIK) \
    is not None or "doğrulama tarihi" in ESIK.lower()
vaka("AM-05", "hesap aracı sonucun mevzuat sürümünü ve tarihini yazıyor",
     _surum and _tarih and _yazdiriyor,
     "tebliğ sürümü=%s · DOGRULAMA sabiti=%s · çıktıya yazılıyor=%s"
     % (_surum, _tarih, _yazdiriyor))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AM-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
