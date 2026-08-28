#!/usr/bin/env python3
"""KÖR SINAMA AO — çıkar çatışmasının yönü ve zamanı.

Yönelim (otuz üçüncü tur). §8 tek cümle: "Bir dosya AÇILMADAN ÖNCE
`hafiza/cikar-catismasi.md` KARŞI TARAFLAR İÇİN kontrol edilir. Çatışma bir
uyarı değil, durma sebebidir." Bu cümlede iki bağ var ve ikisi de sınanmamış:

  YÖN   — kontrol "karşı taraflar için" yapılıyor. `/dosya-ac`'ın birinci
          adımı bunu birebir uyguluyor: "verilen KARŞI TARAF adlarını ara".
          Ama çatışma simetrik bir ilişkidir. En ağır hâli şudur: yeni
          dosyanın MÜVEKKİLİ, açık bir dosyanın KARŞI TARAFIDIR — yani
          şu anda aleyhine çalıştığımız kişi için çalışmaya başlıyoruz.
          Kayıt biçimi `<taraf adı> · <dosya> · <hangi tarafta> · <tarih>`
          bu soruyu cevaplayacak veriyi TAŞIYOR; prosedür hiç sormuyor.

  ZAMAN — kontrol açılış anına bağlı. Kayda sonradan bir ad girdiğinde
          çatışma o an doğar, ama hiçbir şey geriye bakmıyor. Otuz birinci
          turdaki eşik sorusunun ("mevzuat değişti, verilmiş görüşe ne
          oluyor") çıkar çatışması ayağındaki hâli.

Kitap iki şeyi DOĞRU yapıyor ve bu takım onları olumlu kontrol olarak tutar:
boş kayıt "temiz" sayılmıyor (§18.9 ile birlikte beyan edilmiş bir sınır) ve
eşleşme bir uyarı değil DURMA sebebi.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def oku(*p):
    try:
        with open(os.path.join(_KOK_COZ, *p), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def duz(m):
    """Yorumları at, boşlukları düzleştir. [AM dersi] Satır kırılması bir
    metnin anlamını değiştirmez; ölçütün ona duyarlı olması ölçüm kusurudur.
    [AN dersi] Bir kuralı ANLATAN yorum, kuralın KENDİSİ değildir."""
    return re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", " ", m, flags=re.S))


KOMUT = duz(oku(".claude", "commands", "dosya-ac.md"))
BECERI = duz(oku(".claude", "skills", "dosya-ac", "SKILL.md"))
ORNEK = duz(oku("hafiza", "cikar-catismasi.ornek.md"))
SOZLESME = duz(oku("CLAUDE.md"))

# --- AO-01 · OLUMLU KONTROL: kayıt "hangi tarafta"yı tutuyor -----------
# Yön sorusunun cevaplanabilmesi için verinin VAR olması gerekir. Varsa,
# bulgu "veri yok" değil "prosedür sormuyor" olur — aradaki fark, kitabı
# haksız yere suçlamakla doğru yerde suçlamak arasındaki farktır.
_yon_verisi = "hangi tarafta" in ORNEK
vaka("AO-01", "çatışma kaydı kimin hangi tarafta olduğunu tutuyor",
     _yon_verisi,
     "kayıt biçiminde 'hangi tarafta' alanı var" if _yon_verisi
     else "kayıt yön bilgisi taşımıyor")

# --- AO-02 · açılış kontrolü İKİ YÖNLÜ mü ------------------------------
# Şart: prosedür yalnızca yeni dosyanın karşı taraflarını değil,
# MÜVEKKİLİNİ de mevcut kayıtlara karşı aramalı.
def _iki_yonlu(metin):
    """ARAMA TALİMATININ KENDİSİ müvekkili de anıyor mu?

    Bu ölçüt ÜÇ KEZ fazla geniş çıktı; üçü de aynı sınıf — yakınlık kanıt
    değildir (AF-04 kelime örtüşmesi, AN yorum tuzağı):
      1. 600 karakterlik PENCERE: bulduğu "müvekkil" üçüncü adımdan, yani
         KAPSAM.md'ye yazan bambaşka bir talimattan geliyordu.
      2. CÜMLE ölçeği: yamanın açıklama cümlesi ("çatışma simetriktir ve en
         ağır hâli, yeni dosyanın MÜVEKKİLİNİN…") arama talimatıyla aynı
         cümlede, iki nokta üst üstenin ardında duruyordu. Mutasyonda arama
         talimatından müvekkil çıkarıldı, AÇIKLAMA kaldı ve vaka yeşil kaldı.
      3. Ayrıca `ara\b` çekimlenmiş gövdeyi görmüyordu (AE sınıfı).
    Ölçüt CÜMLECİĞE indirildi: nokta, noktalı virgül, iki nokta ve madde
    işaretiyle bölünür. Bir cümlecik hem arama fiilini, hem müvekkili, hem de
    neyin içinde arandığını (kayıt/çatışma/liste) taşımak zorundadır.
    """
    if not metin:
        return False
    parcalar = re.split(r"[.;:]|\s-\s|\s\u2013\s", metin)
    for c in parcalar:
        if not re.search(r"\bara(?:n|r|y|t|ş|\b)\w*|sorgula"
                         r"|\btara(?:n|r|y|\b)\w*|karşılaştır", c, re.I):
            continue
        if not re.search(r"müvekkil", c, re.I):
            continue
        if re.search(r"kayıt|kayıtta|çatışma|cikar-catismasi|liste", c, re.I):
            return True
    return False


_k = _iki_yonlu(KOMUT)
_b = _iki_yonlu(BECERI)
vaka("AO-02", "açılış kontrolü yeni MÜVEKKİLİ de mevcut kayda karşı arıyor",
     _k and _b,
     "komut iki yönlü=%s · beceri iki yönlü=%s — çatışma simetriktir: yeni "
     "dosyanın müvekkili açık bir dosyanın karşı tarafı olabilir" % (_k, _b))

# --- AO-03 · kayıt SONRADAN büyüdüğünde açık dosyalar yeniden bakılıyor -
_geriye = []
for kok, _d, dosyalar in os.walk(os.path.join(_KOK_COZ, ".claude")):
    for ad in dosyalar:
        if not ad.endswith(".md"):
            continue
        icerik = duz(open(os.path.join(kok, ad), encoding="utf-8",
                          errors="replace").read())
        if not re.search(r"cikar-catismasi|çıkar çatışması", icerik, re.I):
            continue
        # açık dosyaları geriye dönük tarayan bir adım var mı
        if re.search(r"(^|[^/\w])dosyalar/", icerik) and \
           re.search(r"açık dosya|var olan dosya|yeniden kontrol|geriye",
                     icerik, re.I):
            _geriye.append(ad)
vaka("AO-03", "kayda ad eklendiğinde açık dosyalar yeniden kontrol ediliyor",
     bool(_geriye),
     "geriye dönük kontrol yapan: %s — çatışma açılış anında doğmayabilir"
     % (_geriye or "yok"))

# --- AO-04 · OLUMLU KONTROL: boş kayıt "temiz" sayılmıyor --------------
_bos = (re.search(r"temiz.{0,40}değil", ORNEK, re.I) is not None
        and re.search(r"temiz.{0,30}DEĞİL", KOMUT) is not None)
vaka("AO-04", "boş çatışma kaydı 'temiz' sayılmıyor",
     _bos, "örnek ve komut boş kaydı temiz saymıyor" if _bos
     else "boş kayıt ayrımı eksik")

# --- AO-05 · OLUMLU KONTROL: eşleşme DURMA sebebi ---------------------
# [kendi kusurum] Ölçüt "eşleşme varsa dur" DİZGESİNİ arıyordu. Otuz üçüncü
# turun yaması cümleye bir ara söz ekleyince ("eşleşme varsa —hangi yönde
# olursa olsun— DUR") ölçüt kırmızıya döndü, oysa durma dili yerinde
# duruyordu. Bir ölçüt bir CÜMLEYİ değil bir ANLAMI sınamalı: eşleşmeden söz
# eden cümle, durmayı da söylemek zorundadır.
def _durma_dili(metin):
    for cumle in re.split(r"(?<=[.!?])\s+", metin):
        if re.search(r"eşleşme", cumle, re.I) and re.search(r"\bDUR", cumle):
            return True
    return False


_durma = (re.search(r"uyarı değil.{0,30}durma", SOZLESME, re.I) is not None
          and _durma_dili(KOMUT))
vaka("AO-05", "çatışma eşleşmesi uyarı değil durma sebebi",
     _durma, "§8 ve komut aynı şeyi söylüyor" if _durma
     else "durma dili eksik")


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AO-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
