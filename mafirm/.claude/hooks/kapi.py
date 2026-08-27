#!/usr/bin/env python3
"""Bir birleşme devralma pratiğinin her esaslı çıktısındaki beş kapı.

Bunlar neden otomatik kontrol, neden CLAUDE.md'de bir kural değil. Belgedeki
bir kurala model sakinken uyulur, görev uzayınca atlanır. Aşağıdaki kusurlar
bir taslağa değil bir müvekkile zarar verenlerdir; bu yüzden 2 çıkış kodu
döndüren bir süreçle uygulanırlar.

  kapsam      hukuki görüş gibi okunan ama avukat satırı taşımayan çıktı
  kanit       dayanağı YANINDA olmayan bir mevzuat eşiği ya da maddesi
  sir         müvekkili tanıtan bilginin dışarıya giden bir çağrıya girmesi
  guncellik   doğrulama tarihi bayatlamış ya da hiç olmayan bir eşik
  arastirma   araştırılmadan anılan bir eşik rakamı ya da depo

Her kapı iki yönde de sınanır: kusurlu vakada ateşlemeli, doğru vakada susmalı.
Yalnızca geçen bir kapı, kapı değildir.

KÖR SINAMA SONRASI SÜRÜM. Kitaba sadık sürüm yamalar/kitaba-sadik/kapi.py
içindedir. Her değişiklik, kapattığı kör sınama vakasının kimliğiyle
işaretlenmiştir; gerekçeler yamalar/DEGISIKLIKLER.md dosyasındadır.
"""
import json
import os
import re
import sys
import unicodedata
from datetime import date, datetime

# ---------------------------------------------------------------------------
# Türkçe küçük harf. [C-yama B-10] Python'un str.lower()'ı 'İ' harfini
# 'i' + U+0307 (birleşen üst nokta) yapar; "YETKİLİ".lower() != "yetkili".
# Sonuç: avukat başlığı BÜYÜK harfle yazıldığında kapı onu göremez ve DOĞRU
# çıktıyı bloklar. Doğru işi bloklayan kapı bir gün içinde kapatılır.
# ---------------------------------------------------------------------------
def tr_kucult(s):
    return (s.replace("İ", "i").replace("I", "ı")
             .replace("İ", "i").replace("I", "ı").lower())


def _sadelestir(s):
    """Birleşen aksanları normalleştir ki 'i̇' ile 'i' aynı sayılsın."""
    return unicodedata.normalize("NFC", s)


# --- Tavsiye biçimleri [B-02..B-06] ----------------------------------------
# Kitabın sürümü sekiz sabit ifadeydi. Bir hukukçunun gerçekten yazdığı
# cümlelerin çoğu o sekizin dışında kalıyordu.
TAVSIYE = re.compile(
    r"("
    r"\w+m[ae](?:nız|niz|nuz|nüz)\s+gerek"          # bildirimde bulunmanız gerekir
    r"|\w+(?:manız|meniz|manız)\s+(?:şart|zorunlu)"  # imzalamanız şarttır
    r"|\w+(?:malısınız|melisiniz)"                   # bildirim yapmalısınız
    r"|\btabidir\b|\btabi\s+olacak"                  # bildirime tabidir
    r"|\bzorunludur\b|\bzorunlu\s+hale\s+gel"
    r"|\bşarttır\b|\bgereklidir\b"
    r"|bu bir hukuki görüştür|tavsiye ederiz"
    r"|hukuka uygundur|yasal olarak yapabilirsiniz"
    r")", re.I)

# --- Olumsuz iddia [B-07..B-09] · CLAUDE.md §2, önceden HİÇ kapısı yoktu ----
OLUMSUZ = re.compile(
    r"("
    r"\bgerekmez\b|\bgerekmemektedir\b"
    r"|\btabi\s+değil"
    r"|böyle\s+bir\s+yükümlülük\s+(?:yok|bulunma)"
    r"|\byükümlülük\s+(?:yoktur|bulunmamaktadır)"
    r"|\bdüzenlemeye\s+tabi\s+değil"
    r"|\bmuaf(?:tır)?\b"
    r")", re.I)

# --- Mevzuat dayanağı ------------------------------------------------------
DAYANAK = re.compile(
    r"(madde\s+\d+|m\.\s?\d+|\d{4}/\d+\s+sayılı|sayılı\s+(?:Kanun|Tebliğ)"
    r"|Resmî\s+Gazete|II-\d+\.\d+|TTK\s+m\.?\s?\d+)", re.I)

# --- Eşiğe benzeyen rakam [B-13..B-16] -------------------------------------
# {2,} -> {1,}: 250.000 TL gibi bir milyonun altındaki rakamlar da eşiktir.
# Sözle yazılmış rakam ve oran biçimi eklendi; TRY ve lira para birimi eklendi.
PARA = r"(?:TL|TRY|₺|EUR|USD|€|\$|avro|dolar|lira)"
ESIK = re.compile(
    "("
    + r"\d{1,3}(?:[.,]\d{3}){1,}\s?" + PARA                       # 3.000.000.000 TL
    + r"|\d+(?:[.,]\d+)?\s*(?:bin|milyon|milyar|trilyon)\s*" + PARA  # 3 milyar TL
    + r"|binde\s+\w+|yüzde\s+\w+|%\s?\d+(?:[.,]\d+)?"           # binde bir, yüzde 98
    + ")", re.I)

GEREKLI_BASLIK = "yetkili avukat görüşü gereken konular"
KONTROL = re.compile(r"^[ \t]*Kontrol edildi:", re.M)   # [B-33] girinti serbest
GITHUB = re.compile(r"github\.com/[\w.-]+/[\w.-]+", re.I)
BAYAT_GUN = 183

# Dayanağın rakama YAKIN olması gerekir [B-17, B-18]. Belge düzeyinde bir
# kontrol, kırk satır önceki bir atıfla ilgisiz bir rakamı aklıyor.
YAKINLIK = 300

# ... ama hukuk metni paragraf paragraf atıf vermez: bir "Dayanak:" satırı
# kendinden sonrasını yönetir. [C-01] Yakınlık tek başına uygulandığında
# kitabın KENDİ tr-esikler.md dosyası bloklanıyordu — başlıktaki Dayanak
# bloğu, listedeki rakamlardan 300 karakterden uzakta. Açık bir Dayanak
# beyanı, yazarın o bölümün temelini beyan etmesidir; düzyazıda geçen
# "tebliğ" kelimesi değildir.
DAYANAK_BEYAN = re.compile(r"^[ \t]*(?:\*\*)?Dayanak(?:\*\*)?\s*:", re.M)

# --- Sır kalıpları [B-25..B-29] --------------------------------------------
# Ayırıcı: boşluk, +, %20, _, - . Bir kod adı sorgu dizesine girdiğinde
# boşluk '+' ya da '%20' olur; yalnızca \s arayan bir desen onu göremez.
AYR = r"(?:\s|\+|%20|_|-)+"

SIR_KALIPLARI = (
    (r"\b(?:Proje|Project|Projekt)" + AYR + r"[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ]*\b",
     "işlem kod adı"),
    (r"\b[A-ZÇĞİÖŞÜ][\wçğıöşü]+(?:" + AYR + r"[A-ZÇĞİÖŞÜ\wçğıöşü]+){0,4}" + AYR
     + r"(?:A\.Ş\.|A\.Ş\b|Ltd\.(?:\s|\+|%20)*Şti\.|Anonim" + AYR + r"Şirketi"
       r"|Limited" + AYR + r"Şirketi)",
     "şirket unvanı"),
    (r"(?:bedel|fiyat|değer)[^.\n]{0,40}?\d{1,3}(?:[.,]\d{3}){1,}\s?" + PARA,
     "işlem bedeli"),
)

# Yerel başvuru malzemesi ile müvekkile giden çıktı ayrımı.
# [C-01, C-03] Kitabın kendi yöntem dosyaları "esaslı çıktı" değildir:
# birimler/ ve emsal/ altındaki dosyalar pratiğin kendi başvuru malzemesidir
# ve her biri zaten dayanak ile doğrulama tarihi taşır. Avukat başlığını ve
# "Kontrol edildi" satırını onlardan istemek, doğru işi bloklamaktır.
BASVURU_YOLU = re.compile(r"(^|/)(birimler|emsal|yamalar|sinama)/", re.I)


def _basvuru_malzemesi(yol):
    return bool(yol) and bool(BASVURU_YOLU.search(str(yol)))


def kapi_kapsam(metin, yol=None, disari=False):
    """Görüş biçiminde bir çıktı, avukat başlığını taşımak zorundadır."""
    if _basvuru_malzemesi(yol) and not disari:
        return None
    m = TAVSIYE.search(metin) or OLUMSUZ.search(metin)
    if not m:
        return None
    if GEREKLI_BASLIK in _sadelestir(tr_kucult(metin)):
        return None
    tur = "olumsuz iddia" if OLUMSUZ.match(m.group(0)) or OLUMSUZ.search(m.group(0)) \
        else "görüş"
    return ("kapsam", "%s gibi okunuyor, avukat başlığı yok: %r"
            % (tur, metin[max(0, m.start() - 30):m.end() + 30].strip()))


def kapi_kanit(metin):
    """Bir eşik rakamı, YANINDA mevzuat dayanağı ister.

    İki yoldan biri yeter: rakamın ±YAKINLIK karakterinde bir atıf, ya da
    rakamdan ÖNCE gelen açık bir "Dayanak:" beyanı.
    """
    for m in ESIK.finditer(metin):
        pencere = metin[max(0, m.start() - YAKINLIK):m.end() + YAKINLIK]
        onceki = metin[:m.start()]
        if DAYANAK_BEYAN.search(onceki) and DAYANAK.search(onceki):
            continue
        if not DAYANAK.search(pencere):
            return ("kanit", "dayanaksız eşik (±%d karakterde atıf yok): %r"
                    % (YAKINLIK, metin[max(0, m.start() - 40):m.end() + 20].strip()))
    return None


def _ad_kaydi():
    """hafiza/muvekkil-adlari.txt — satır başına bir ad.

    [B-28] Gerçek kişi ve tescilli olmayan kurum adları desenle yakalanamaz:
    "Ayşe Yılmaz" ile herhangi iki büyük harfli kelimeyi ayırt eden bir kural
    yoktur ve denemek, doğru işi bloklayan bir kapı üretir. Tek dürüst çözüm
    bir KAYITTIR. Kayıt yoksa bu kural kapsanmıyor demektir ve sistem bunu
    saklamak yerine söyler (bkz. denetim.sh "müvekkil ad kaydı" satırı).
    """
    yol = os.path.expanduser("~/mafirm/hafiza/muvekkil-adlari.txt")
    try:
        with open(yol, encoding="utf-8") as f:
            return [a.strip() for a in f if a.strip()
                    and not a.lstrip().startswith("#")]
    except OSError:
        return []


def kapi_sir(metin, disari=False):
    """Müvekkili tanıtan bilgi makineden çıkmamalı."""
    if not disari:
        return None
    for ad in _ad_kaydi():
        if re.search(re.escape(ad).replace(r"\ ", AYR), metin, re.I):
            return ("sir", "kayıtlı müvekkil/karşı taraf adı makineden çıkıyor: %r"
                    % ad)
    for kalip, ad in SIR_KALIPLARI:
        m = re.search(kalip, metin)
        if m:
            return ("sir", "%s makineden çıkıyor: %r" % (ad, m.group(0).strip()))
    return None


def kapi_guncellik(metin, bugun=None):
    """Bayatlamış, gelecek tarihli ya da HİÇ OLMAYAN doğrulama tarihi."""
    bugun = bugun or date.today()
    bulunan = []
    for m in re.finditer(r"[Dd]oğrulama:?\s*"
                         r"(\d{4}-\d{2}-\d{2}|\d{2}[./]\d{2}[./]\d{4})", metin):
        ham = m.group(1)
        for bicim in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):   # [B-21] Türkçe biçim
            try:
                bulunan.append((ham, datetime.strptime(ham, bicim).date()))
                break
            except ValueError:
                continue
    if not bulunan:
        # [B-22] Tarihsiz bir eşik, bayat bir eşikten kötüdür: hiç kontrol
        # edilmemiş olduğu bile bilinmez.
        if ESIK.search(metin):
            return ("guncellik", "eşik rakamı var ama doğrulama tarihi yok")
        return None
    for ham, d in bulunan:
        yas = (bugun - d).days
        if yas > BAYAT_GUN:
            return ("guncellik", "%s doğrulaması %d günlük; yeniden çek" % (ham, yas))
        if yas < 0:                                          # [B-23] gelecek tarih
            return ("guncellik", "%s doğrulaması GELECEK tarihli (%d gün)"
                    % (ham, -yas))
    return None


def kapi_arastirma(metin, yol=None, disari=False):
    """Bir eşik rakamı ya da GitHub adresi, Kontrol edildi satırı ister."""
    if _basvuru_malzemesi(yol) and not disari:
        return None
    if (ESIK.search(metin) or GITHUB.search(metin)) and not KONTROL.search(metin):
        return ("arastirma", "rakam ya da depo anıldı, Kontrol edildi satırı yok")
    return None


def denetle(metin, disari=False, bugun=None, yol=None):
    """Beş kapının hepsi. (kapı, ileti) listesi döner."""
    return [b for b in (kapi_kapsam(metin, yol, disari),
                        kapi_kanit(metin),
                        kapi_sir(metin, disari),
                        kapi_guncellik(metin, bugun),
                        kapi_arastirma(metin, yol, disari))
            if b]


# ---------------------------------------------------------------------------
# ÜRETİM YOLU  [C-01, C-02, C-03, C-10]
# Kitap metni json.dumps(tool_input) ile düzleştiriyordu. json.dumps gerçek
# satır sonlarını iki karakterlik \n dizisine çevirir; re.M ile ^ çapası
# artık hiçbir satır başına denk gelmez ve "^Kontrol edildi:" ÜRETİMDE ASLA
# eşleşmez. Öz-sınama ham dize verdiği için bunu göremez.
# Çözüm: tool_input içindeki dize değerleri toplanır ve GERÇEK satır sonuyla
# birleştirilir. Öz-sınama yolu ile üretim yolu artık aynı metni görür.
# ---------------------------------------------------------------------------
def metni_cikar(nesne, toplam=None):
    if toplam is None:
        toplam = []
    if isinstance(nesne, str):
        toplam.append(nesne)
    elif isinstance(nesne, dict):
        for v in nesne.values():
            metni_cikar(v, toplam)
    elif isinstance(nesne, (list, tuple)):
        for v in nesne:
            metni_cikar(v, toplam)
    elif nesne is not None:
        toplam.append(str(nesne))
    return toplam


# [C-05..C-07, C-09] Bash dışarı giden en geniş kanaldır: curl, git push, her
# paket aracı. Kitabın disari kümesi onu içermiyordu ve settings.json'daki
# matcher onu hiç çağırmıyordu.
DISARI_ARACLAR = ("WebSearch", "WebFetch", "Bash", "BashOutput")
DISARI_BASH = re.compile(
    r"\b(curl|wget|git\s+push|git\s+remote|scp|rsync|ssh|nc|"
    r"pip\s+install|npm\s+(?:publish|install)|gh\b|aws\b|az\b|gcloud)\b", re.I)


def disari_mi(arac, tool_input):
    if arac.startswith("mcp__"):
        return True
    if arac in ("WebSearch", "WebFetch"):
        return True
    if arac in ("Bash", "BashOutput"):
        return bool(DISARI_BASH.search(" ".join(metni_cikar(tool_input))))
    return False


def _selftest():
    h = 0
    V = [
        # (metin, disari, beklenen kapılar)   — kitabın dokuz vakası
        ("Kurul'a bildirimde bulunmanız gerekir.", False, {"kapsam"}),
        ("Kurul'a bildirimde bulunmanız gerekir.\n"
         "## Yetkili avukat görüşü gereken konular\nHepsi.", False, set()),
        ("Eşik, birleşik ciro için 3.000.000.000 TL'dir.", False,
         {"kanit", "guncellik", "arastirma"}),
        ("2010/4 sayılı Tebliğ eşiği 3.000.000.000 TL olarak belirler.",
         False, {"guncellik", "arastirma"}),
        ("Proje Şahin işlemin kod adıdır.", True, {"sir"}),
        ("Proje Şahin işlemin kod adıdır.", False, set()),
        ("Hedef Acme Gıda A.Ş. şirketidir.", True, {"sir"}),
        ("Madde 7 uyarınca. Doğrulama: 2020-01-01", False, {"guncellik"}),
        ("Madde 7 uyarınca. Doğrulama: 2026-08-27", False, set()),
        # §14'ün yedi vakası
        ("github.com/opensanctions/nomenklatura adresine bak", False, {"arastirma"}),
        ("github.com/opensanctions/nomenklatura\nKontrol edildi: API (2026-08-27)",
         False, set()),
        ("birimler/rekabet/yontem/tr-esikler.md dosyasını oku", False, set()),
        ("emsal/spa.md dosyasındaki biçime bak", False, set()),
        ("ve/veya alıcı tercih edebilir", False, set()),
        ("Başvuru otuz gün içinde yapılır.", False, set()),
        ("cd ~/mafirm && ls birimler/ çalıştır", False, set()),
    ]
    bugun = date(2026, 8, 27)
    for metin, disari, bekle in V:
        bulunan = {k for k, _ in denetle(metin, disari, bugun)}
        if bulunan != bekle:
            print("  HATA %r -> %s, beklenen %s"
                  % (metin[:44], bulunan or "{}", bekle or "{}"))
            h += 1
    print("SELFTEST %s (%d vaka)" % ("OK" if not h else "HATA %d" % h, len(V)))
    return h


def main():
    if "--self-test" in sys.argv:
        return _selftest()
    try:
        olay = json.load(sys.stdin)
    except Exception as e:
        # [C-08] Ayrıştırılamayan bir olay bir politika ihlali değil, bir iç
        # arızadır. Dışarı giden bir çağrıda hata KAPALI yönde çözülür: kapıyı
        # görmeden dışarı veri göndermek, sır kuralının kabul edemeyeceği şey.
        # İçeride hata AÇIK yönde çözülür, yoksa pratik durur.
        # Ayrıştırılamayan bir olayda araç adı okunamaz; dolayısıyla çağrının
        # dışarı gidip gitmediği BİLİNEMEZ. Sır kuralı, bilinmeyen bir kanalda
        # veri göndermeyi kabul edemez. Bozuk olay rutin değil alarmdır.
        print("BLOKLANDI [ayrıstirma] olay ayrıştırılamadı, kanal bilinmiyor: %s"
              % e, file=sys.stderr)
        return 2
    tool_input = olay.get("tool_input", {})
    arac = olay.get("tool_name", "")
    metin = "\n".join(metni_cikar(tool_input))
    yol = tool_input.get("file_path") or tool_input.get("path") \
        if isinstance(tool_input, dict) else None
    disari = disari_mi(arac, tool_input)
    bulgular = denetle(metin, disari, yol=yol)
    if bulgular:
        for k, m in bulgular:
            print("BLOKLANDI [%s] %s" % (k, m), file=sys.stderr)
        return 2          # 2 çıkış kodu işlemi bloklar
    return 0


if __name__ == "__main__":
    sys.exit(main())
