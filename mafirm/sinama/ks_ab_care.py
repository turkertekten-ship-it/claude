#!/usr/bin/env python3
"""KÖR SINAMA AB — bloklanan kişi NE YAPACAĞINI öğreniyor mu.

Kitap §14'te bir kapının nasıl öldüğünü kendisi yazar:

    "Doğru işi bloklayan bir kapı bir gün içinde kapatılır; sonra hiçbir şey
     uygulanmaz."

On dördüncü tur bunu YANLIŞ POZİTİF ekseninde ölçtü. Ama ekonomi aynıdır:
DOĞRU bir blok da, uyulacak yolu söylemiyorsa her seferinde zaman yakar ve en
ucuz çözüm kapıyı kapatmaktır. Teşhis koyan ama çare söylemeyen bir kapı,
yanlış ateşleyen bir kapıyla aynı yerde biter.

Ölçülen üç şey:
  1. İleti bir ÇARE adlandırıyor mu (teşhis değil, EYLEM).
  2. Kitabın birden çok biçim kabul ettiği yerde ileti onları SAYIYOR mu.
  3. En sağlamı: iletinin söylediği çare BİREBİR uygulandığında kapı susuyor
     mu. Bu, "ileti iyi mi" sorusunu kanaatten ÖLÇÜME çevirir.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
KAPI = os.path.join(KOK, ".claude/hooks/kapi.py")
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def kanca(olay):
    r = subprocess.run([sys.executable, KAPI], input=json.dumps(olay),
                       capture_output=True, text=True)
    return r.returncode, (r.stderr or "").strip()


# İhlal eden metin -> çareyi uygulanmış hâli. İkinci sütun, iletinin
# SÖYLEMESİ gereken şeyin bizzat uygulanmış hâlidir.
KAPANIS = ("\n\n## Şimdi ne yapılmalı\n\nAdımları yürütün.\n\n"
           "## Yetkili avukat görüşü gereken konular\n\nHepsi.\n")
VAKALAR = [
    ("kanit", "dayanaksız eşik",
     "Ciro eşiği 3.000.000.000 TL'dir.\n",
     "Ciro eşiği 3.000.000.000 TL'dir (2010/4 sayılı Tebliğ m.7).\n"
     "Doğrulama: 2026-08-28\nKontrol edildi: rekabet.gov.tr (2026-08-28) "
     "· bulunamayan: yok\n"),
    ("kapsam", "avukat başlığı yok",
     "Kurul'a bildirimde bulunmanız gerekir.\n",
     "Kurul'a bildirimde bulunmanız gerekir.\n" + KAPANIS),
    ("guncellik", "doğrulama tarihi yok",
     "Eşik 1.000.000.000 TL (2010/4 sayılı Tebliğ m.7).\n",
     "Eşik 1.000.000.000 TL (2010/4 sayılı Tebliğ m.7).\n"
     "Kontrol edildi: rekabet.gov.tr (2026-08-28) · bulunamayan: yok\n"),
    ("arastirma", "Kontrol edildi satırı yok",
     "github.com/opensanctions/nomenklatura deposuna bak.\n" + KAPANIS,
     "github.com/opensanctions/nomenklatura deposuna bak.\n"
     "Kontrol edildi: GitHub API (2026-08-28) · bulunamayan: yok\n" + KAPANIS),
]

# --- AB-01 · ileti bir EYLEM adlandırıyor mu -------------------------
# Çare bir FİİL ya da somut bir biçim örneğidir. "atıf yok" teşhistir;
# "madde atfı ekleyin ya da Dayanak: satırı yazın" çaredir.
CARE = re.compile(r"→|çare|ekle|yaz|kullan|biçim|örnek|şöyle|:contentReference"
                  r"|Doğrulama:|Kontrol edildi:|## ", re.I)
caresiz = []
iletiler = {}
for kapi_ad, ad, ihlal, _duzeltilmis in VAKALAR:
    rc, err = kanca({"tool_name": "Write", "tool_input": {"content": ihlal}})
    satir = next((s for s in err.split("\n") if "[%s]" % kapi_ad in s), "")
    iletiler[kapi_ad] = satir
    if not satir:
        caresiz.append("%s (hiç ateşlemedi)" % kapi_ad)
    elif not CARE.search(satir):
        caresiz.append(kapi_ad)
vaka("AB-01", "her blok iletisi bir ÇARE adlandırıyor (teşhis değil eylem)",
     not caresiz,
     ("çaresiz: %s — bloklanan kişi neyi yazacağını iletiden öğrenemiyor"
      % ", ".join(caresiz)) if caresiz
     else "%d kapının iletisi de somut bir eylem gösteriyor" % len(VAKALAR))

# --- AB-02 · birden çok kabul edilen biçim SAYILIYOR mu --------------
# guncellik kapısı iki biçim kabul ediyor: "Doğrulama: <tarih>" (§3/§5.3) ve
# "Kontrol edildi: <kaynak> (<tarih>)" (§14). On dördüncü tur bu ikiliğin
# kitabın kendi çelişkisi olduğunu buldu. İleti ikisini de saymazsa,
# bloklanan kişi hangisinin işe yaradığını DENEYEREK bulmak zorunda.
g = iletiler.get("guncellik", "")
iki_bicim = "Doğrulama" in g and "Kontrol edildi" in g
vaka("AB-02", "birden çok kabul edilen biçim varsa ileti hepsini sayıyor",
     iki_bicim,
     "guncellik iletisi: %r" % g[:150] if not iki_bicim
     else "iki biçim de iletide adlandırılıyor")

# --- AB-03 · iletinin ÇARESİ birebir uygulanınca kapı susuyor mu -----
# En sağlam ölçüt: kanaat değil davranış.
tutmayan = []
for kapi_ad, ad, ihlal, duzeltilmis in VAKALAR:
    rc1, _ = kanca({"tool_name": "Write", "tool_input": {"content": ihlal}})
    rc2, err2 = kanca({"tool_name": "Write",
                       "tool_input": {"content": duzeltilmis}})
    hala = "[%s]" % kapi_ad in err2
    if rc1 != 2 or hala:
        tutmayan.append("%s (ihlal çıkış %d, çare sonrası %s)"
                        % (kapi_ad, rc1, "hâlâ ateşliyor" if hala else "temiz"))
vaka("AB-03", "iletinin gösterdiği çare uygulanınca o kapı susuyor",
     not tutmayan, "; ".join(tutmayan) if tutmayan
     else "%d kapının dördü de çare sonrası susuyor" % len(VAKALAR))

# --- AB-03b · İLETİNİN ÖNERDİĞİ biçim gerçekten işe yarıyor mu ------
# AB-03'ün ilk hâli YETERSİZDİ: benim sınamaya yazdığım düzeltilmiş metinleri
# deniyordu, iletinin ÖNERDİĞİ biçimi değil. Mutasyon bunu sağ kalarak
# gösterdi — kapıya kasten YANLIŞ bir çare yazdım ("dosyanın sonuna 'BITTI'
# yazın") ve takım yeşil kaldı. Bir çareyi sınamak, kendi niyetimi değil
# SİSTEMİN İDDİASINI sınamak demektir.
#
# Ölçüt: iletideki tek tırnaklı her biçim ÖRNEĞİ çıkarılır, yer tutucuları
# doldurulur, ihlalli metne eklenir ve o kapının SUSMASI beklenir. En az bir
# örnek işe yaramıyorsa ileti yanlış yol tarif ediyordur.
def _somutla(kalip):
    return (kalip.replace("YYYY-AA-GG", "2026-08-28")
                 .replace("<kaynak>", "rekabet.gov.tr")
                 .replace("<tarih>", "2026-08-28")
                 .replace("<ne>", "yok")
                 .replace("...", "6102 sayılı Türk Ticaret Kanunu"))


yanlis_tarif = []
for kapi_ad, ad, ihlal, _d in VAKALAR:
    ileti = iletiler.get(kapi_ad, "")
    if "→" not in ileti:
        continue
    care = ileti.split("→", 1)[1]
    ornekler_ = [x for x in re.findall(r"'([^']{4,})'", care)
                 if not x.startswith("##")]
    basliklar = re.findall(r"'(##[^']+)'", care)
    denenen, tutan = 0, 0
    for orn in ornekler_ + basliklar:
        somut = _somutla(orn)
        aday = ihlal.rstrip("\n") + "\n" + somut + "\n"
        if basliklar and orn in basliklar:
            aday = ihlal.rstrip("\n") + "\n\n" + somut + "\n\nHepsi.\n"
        denenen += 1
        _rc, e = kanca({"tool_name": "Write", "tool_input": {"content": aday}})
        if "[%s]" % kapi_ad not in e:
            tutan += 1
    if denenen and not tutan:
        yanlis_tarif.append("%s (%d örnek denendi, hiçbiri susturmadı)"
                            % (kapi_ad, denenen))
# Boşa geçmesin: hiçbir iletide çare YOKSA sınanacak bir iddia da yoktur.
# Bunu "geçti" diye yazmak, ölçtüğünü sanmaktır — kitaba sadık kapıda tam
# olarak bu oluyordu (hiçbir ileti "→" taşımıyor, döngü hiç dönmüyor).
_careli = sum(1 for k in iletiler if "→" in iletiler.get(k, ""))
vaka("AB-03b", "iletinin ÖNERDİĞİ biçim gerçekten o kapıyı susturuyor",
     (not yanlis_tarif) and _careli > 0,
     ("YANLIŞ YOL TARİFİ: %s" % "; ".join(yanlis_tarif)) if yanlis_tarif
     else ("%d kapının iletisindeki biçimlerin en az biri tutuyor" % _careli)
     if _careli else
     "SINANACAK İDDİA YOK: hiçbir ileti çare göstermiyor — bu bir geçiş "
     "değil, ölçülecek bir şeyin bulunmamasıdır (bkz. AB-01)")

# --- AB-04 · çok kapılı blokta bütün çareler BİR KEREDE veriliyor ----
# "Ciro eşiği 3.000.000.000 TL'dir." üç kapıyı birden ateşliyor. Kullanıcı
# birini düzeltip yeniden koşarsa ikinciye çarpar: üç tur, tek tur yerine.
rc, err = kanca({"tool_name": "Write",
                 "tool_input": {"content": "Ciro eşiği 3.000.000.000 TL'dir.\n"}})
ates_eden = re.findall(r"BLOKLANDI \[(\w+)\]", err)
vaka("AB-04", "çok kapılı blokta bütün ihlaller tek seferde bildiriliyor",
     len(ates_eden) >= 3,
     "%d kapı birden bildirildi (%s) — kullanıcı tek turda hepsini görüyor"
     % (len(ates_eden), ", ".join(ates_eden)))

# --- AB-05 · takım DETERMİNİST mi ------------------------------------
# Aynı girdiye iki farklı cevap veren bir sınama, kırmızıyı görmezden gelmeyi
# öğretir — bu takımın bütün amacının tersi. Hiç ölçmemiştim.
_spec = importlib.util.spec_from_file_location("kapi_ab", KAPI)
_k = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_k)
ornekler = [v[2] for v in VAKALAR] + ["Toplantı 15.00'e alındı.\n"]
sapan = []
for metin in ornekler:
    ilk = None
    for _ in range(5):
        simdi = tuple(sorted(a for a, _m in _k.denetle(metin, bugun=None)))
        if ilk is None:
            ilk = simdi
        elif simdi != ilk:
            sapan.append(metin[:40])
            break
vaka("AB-05", "aynı girdi beş koşumda aynı kapı kümesini veriyor",
     not sapan, "sapan girdi: %s" % "; ".join(sapan) if sapan
     else "%d girdi × 5 koşum, sapma yok" % len(ornekler))


BEKLENEN_VAKA = 6


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AB-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA AB — bloklanan kişi ne yapacağını öğreniyor mu")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, _ = beklenen.durum(kod, gecti)
        print("%s %-7s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _s, _c = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _c["GEÇTİ"], _c["BEKLENEN"], _s))
    return _s


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
