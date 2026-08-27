#!/usr/bin/env python3
"""Bir birleşme devralma pratiğinin her esaslı çıktısındaki dört kapı.

Bunlar neden otomatik kontrol, neden CLAUDE.md'de bir kural değil. Belgedeki
bir kurala model sakinken uyulur, görev uzayınca atlanır. Aşağıdaki dört kusur
bir taslağa değil bir müvekkile zarar verenlerdir; bu yüzden 2 çıkış kodu
döndüren bir süreçle uygulanırlar.

  arastirma   araştırılmadan anılan bir eşik rakamı ya da depo
  kapsam      hukuki görüş gibi okunan ama avukat satırı taşımayan çıktı
  kanit       dayanağı yanında olmayan bir mevzuat eşiği ya da maddesi
  sir         müvekkili tanıtan bilginin dışarıya giden bir çağrıya girmesi
  guncellik   doğrulama tarihi bayatlamış bir eşiğe dayanılması

Her kapı iki yönde de sınanır: kusurlu vakada ateşlemeli, doğru vakada susmalı.
Yalnızca geçen bir kapı, kapı değildir.
"""
import json
import re
import sys
from datetime import date, datetime

# Hukuki görüş gibi okunan cümleler. Bilerek dar: "değerlendirilebilir"
# tartışmadır, "bildirimde bulunmanız gerekir" görüştür.
TAVSIYE = re.compile(
    r"(bildirimde bulunmanız gerek|imzalamanız gerek|beyan etmeniz gerek"
    r"|ödemeniz gerek|bu bir hukuki görüştür|tavsiye ederiz"
    r"|hukuka uygundur|yasal olarak yapabilirsiniz)", re.I)

# Mevzuat dayanağı: madde, tebliğ ya da kanun numarası.
DAYANAK = re.compile(
    r"(madde\s+\d+|m\.\s?\d+|Tebliğ|sayılı Kanun|Kanun[,\s]+madde"
    r"|Resmî Gazete|II-\d+\.\d+|\d{4}/\d+\s+sayılı)", re.I)

# Eşiğe benzeyen rakam. TÜRKÇE BİÇİM: binlik ayırıcı NOKTA. İngilizce
# virgüllü biçimi de kabul eder, çünkü alıntılanan kaynak öyle olabilir.
ESIK = re.compile(r"\d{1,3}(?:[.,]\d{3}){2,}\s?(?:TL|₺|EUR|USD|avro|dolar)", re.I)

GEREKLI_BASLIK = "yetkili avukat görüşü gereken konular"

# Altı ay, gün olarak. İşletim sözleşmesindeki güncellik kuralı.
BAYAT_GUN = 183


def kapi_kapsam(metin):
    """Görüş biçiminde bir çıktı, avukat başlığını taşımak zorundadır."""
    if TAVSIYE.search(metin) and GEREKLI_BASLIK not in metin.lower():
        m = TAVSIYE.search(metin)
        return ("kapsam", "görüş gibi okunuyor, avukat başlığı yok: "
                + repr(metin[max(0, m.start() - 30):m.end() + 30].strip()))
    return None


def kapi_kanit(metin):
    """Bir eşik rakamı, metinde bir yerde mevzuat dayanağı ister."""
    if ESIK.search(metin) and not DAYANAK.search(metin):
        m = ESIK.search(metin)
        return ("kanit", "dayanaksız eşik: "
                + repr(metin[max(0, m.start() - 40):m.end() + 20].strip()))
    return None


def kapi_sir(metin, disari=False):
    """Müvekkili tanıtan bilgi makineden çıkmamalı.

    Yalnızca DIŞARI giden çağrıda ateşler. Aynı metnin yerel bir dosyaya
    yazılması pratiğin olağan işidir ve bloklanmamalıdır; bloklanırsa kapı
    bir gün içinde kapatılır.
    """
    if not disari:
        return None
    for kalip, ad in ((r"\bProje\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\b", "işlem kod adı"),
                      (r"\b[A-ZÇĞİÖŞÜ][\wçğıöşü]+\s+(?:A\.Ş\.|Ltd\.\s*Şti\.)",
                       "şirket unvanı")):
        m = re.search(kalip, metin)
        if m:
            return ("sir", "%s makineden çıkıyor: %r" % (ad, m.group(0)))
    return None


def kapi_guncellik(metin, bugun=None):
    """Altı aydan eski bir doğrulama tarihi bayattır."""
    bugun = bugun or date.today()
    for m in re.finditer(r"[Dd]oğrulama:?\s*(\d{4}-\d{2}-\d{2})", metin):
        try:
            d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            continue
        yas = (bugun - d).days
        if yas > BAYAT_GUN:
            return ("guncellik", "%s doğrulaması %d günlük; yeniden çek"
                    % (m.group(1), yas))
    return None


KONTROL = re.compile(r"^Kontrol edildi:", re.M)
# Belirsiz bir BİÇİMİ değil, kesin bir SİNYALİ ara. İlk sürüm `sahip/depo`
# kalıbını biçiminden yakalıyordu ve bir depoyu `emsal/spa.md` dosya yolundan
# ya da olağan "ve/veya" ifadesinden ayırt edemiyordu. Doğru işi bloklayan bir
# kapı bir gün içinde kapatılır; sonra hiçbir şey uygulanmaz.
GITHUB = re.compile(r"github\.com/[\w.-]+/[\w.-]+", re.I)


def kapi_arastirma(metin):
    """Bir eşik rakamı ya da GitHub adresi, Kontrol edildi satırı ister."""
    if (ESIK.search(metin) or GITHUB.search(metin)) and not KONTROL.search(metin):
        return ("arastirma", "rakam ya da depo anıldı, Kontrol edildi satırı yok")
    return None


def denetle(metin, disari=False, bugun=None):
    """Beş kapının hepsi. (kapı, ileti) listesi döner."""
    return [b for b in (kapi_kapsam(metin), kapi_kanit(metin),
                        kapi_sir(metin, disari), kapi_guncellik(metin, bugun),
                        kapi_arastirma(metin))
            if b]


def _selftest():
    h = 0
    V = [
        # (metin, disari, beklenen kapılar)
        ("Kurul'a bildirimde bulunmanız gerekir.", False, {"kapsam"}),
        ("Kurul'a bildirimde bulunmanız gerekir.\n"
         "## Yetkili avukat görüşü gereken konular\nHepsi.", False, set()),
        ("Eşik, birleşik ciro için 3.000.000.000 TL'dir.", False, {"kanit"}),
        ("2010/4 sayılı Tebliğ eşiği 3.000.000.000 TL olarak belirler.",
         False, set()),
        ("Proje Şahin işlemin kod adıdır.", True, {"sir"}),
        ("Proje Şahin işlemin kod adıdır.", False, set()),
        ("Hedef Acme Gıda A.Ş. şirketidir.", True, {"sir"}),
        ("Madde 7 uyarınca. Doğrulama: 2020-01-01", False, {"guncellik"}),
        ("Madde 7 uyarınca. Doğrulama: 2026-08-27", False, set()),
        ("github.com/opensanctions/nomenklatura adresine bak", False, {"arastirma"}),
        ("github.com/opensanctions/nomenklatura\nKontrol edildi: API (2026-08-27)", False, set()),
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
    print("SELFTEST %s" % ("OK" if not h else "HATA %d" % h))
    return h


def main():
    if "--self-test" in sys.argv:
        return _selftest()
    try:
        olay = json.load(sys.stdin)
    except Exception:
        return 0
    metin = json.dumps(olay.get("tool_input", {}), ensure_ascii=False)
    arac = olay.get("tool_name", "")
    disari = arac in ("WebSearch", "WebFetch") or arac.startswith("mcp__")
    bulgular = denetle(metin, disari)
    if bulgular:
        for k, m in bulgular:
            print("BLOKLANDI [%s] %s" % (k, m), file=sys.stderr)
        return 2          # 2 çıkış kodu işlemi bloklar
    return 0


if __name__ == "__main__":
    sys.exit(main())
