#!/usr/bin/env python3
"""KÖR SINAMA V — kapılar DOĞRU işi bloklıyor mu.

Kitap bu başarısızlık biçimini KENDİSİ adlandırıyor ve fatal sayıyor:

    "Doğru işi bloklayan bir kapı bir gün içinde kapatılır; sonra hiçbir şey
    uygulanmaz."

On üç tur boyunca KAÇIRMA yüzeyini ölçtüm: B takımı kapıdan neyin sızdığını,
O takımı sır kapısının nasıl atlatıldığını sayıyor. Bunun AYNASINI hiç
ölçmedim — kapılar meşru iş ürününde kaç kez ateşliyor. Tek bir örnek
kazayla bulunmuştu (B-10, Türkçe büyük harfli başlık), yani sınıf boş değil.

Yöntem: bir Türk M&A avukatının GERÇEKTEN üreteceği metinler yazıldı —
kapı koduna göre değil, kitabın §0 çıktı sözleşmesine ve becerilerin
belgelenmiş çıktı biçimlerine göre. Her metin için hangi kapının ateşlemesi
GEREKTİĞİ önceden yazıldı. Sonra yedi kapı koşuldu.

  ateşlemesi gerekmiyor + ateşledi   -> YANLIŞ POZİTİF  (ölümcül sınıf)
  ateşlemesi gerekiyor  + susmuş     -> KAÇIRMA
"""
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "kapi_v", os.path.join(KOK, ".claude/hooks/kapi.py"))
kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapi)

BUGUN = "2026-08-28"
KAPANIS = "\n\n## Şimdi ne yapılmalı\n\nYukarıdaki adımları sırayla yürütün.\n\n" \
          "## Yetkili avukat görüşü gereken konular\n\nDayanılmadan önce hepsi.\n"
KONTROL = "\nKontrol edildi: rekabet.gov.tr (2026-08-28) · bulunamayan: yok\n"

# (kod, başlık, metin, ateşlemesi BEKLENEN kapılar kümesi, gerekçe)
KORPUS = [
    ("V-01", "rekabet eşiği değerlendirmesi — tam biçimli",
     "# Bildirim değerlendirmesi\n\n"
     "İşlem bildirime tabidir. B ayağı karşılanıyor: devralınan tarafın "
     "Türkiye cirosu 1.400.000.000 TL, eşik 1.000.000.000 TL "
     "(2010/4 sayılı Tebliğ m.7, 2026/2 ile değişik). Devralan grubun "
     "dünya cirosu eşiği de aşılıyor.\n" + KONTROL + KAPANIS,
     set(), "eşik rakamı DAYANAKLI, Kontrol edildi var, avukat başlığı var"),

    ("V-02", "kapanış kontrol listesi — tablo",
     "# Kapanış kontrol listesi\n\n"
     "| belge | imzalayan | biçim | sıra |\n"
     "|---|---|---|---|\n"
     "| Pay devir sözleşmesi | taraflar | noter | 1 |\n"
     "| Genel kurul kararı | ortaklar | ıslak | 2 |\n"
     "| Pay defteri kaydı | müdür | ıslak | 3 |\n" + KAPANIS,
     set(), "hiçbir rakam, tavsiye kipi ya da sır yok"),

    ("V-03", "SPA madde incelemesi — bulgu",
     "# Madde 8.3 — Tazminat tavanı\n\n"
     "Tavan bedelin yüzde onu olarak yazılmış. Alıcı açısından dar; "
     "piyasada bu büyüklükte bir işlemde yüzde yirmi beş görülür. "
     "Değişiklik önerisi taslağa işlendi.\n" + KAPANIS,
     set(), "oran bir SÖZLEŞME şartıdır, mevzuat eşiği değil"),

    ("V-04", "yönetim kurulu notu — cevap önce",
     "# Yönetim kuruluna not\n\n"
     "## Cevap\n\nİşlem önerilen takvimde kapatılamaz.\n\n"
     "## Gerekçe\n\nRekabet Kurulu izni bekleticidir ve nihai tarih yalnızca "
     "birinci aşamaya göre konmuş.\n" + KAPANIS,
     set(), "tavsiye var ama avukat başlığı da var"),

    ("V-05", "büyük harfli Türkçe başlık",
     "# İNCELEME BULGULARI\n\n"
     "Pay defteri fiilen tutulmuyor. Bu bir kapanış öncesi koşula "
     "dönüştürülmelidir.\n\n"
     "## ŞİMDİ NE YAPILMALI\n\nDefterin tesisi istenir.\n\n"
     "## YETKİLİ AVUKAT GÖRÜŞÜ GEREKEN KONULAR\n\nDefterin geçmişe etkisi.\n",
     set(), "başlık BÜYÜK harfle yazılmış — Türkçe İ/ı tuzağı [B-10]"),

    ("V-06", "karşı tarafın görüşünün AKTARIMI",
     "# Müzakere notu\n\n"
     "Satıcı vekili, işlemin *\"bildirime tabi olmadığı\"* görüşünde. "
     "Bu görüşe katılmıyoruz; devralınan tarafın cirosu eşiği aşıyor "
     "(2010/4 sayılı Tebliğ m.7).\n" + KONTROL + KAPANIS,
     set(), "olumsuz iddia AKTARILIYOR, kurulmuyor — ve çürütülüyor"),

    ("V-07", "dosya yolu, depo adresi değil",
     "# Not\n\n"
     "Eşik yöntemi `birimler/rekabet/yontem/tr-esikler.md` dosyasında; "
     "emsal biçimi `emsal/spa.md` içinde.\n" + KAPANIS,
     set(), "eğik çizgili yol bir GitHub deposu değildir [kitabın kendi vakası]"),

    ("V-08", "pay oranı, mevzuat oranı değil",
     "# Ortaklık yapısı\n\n"
     "Kurucu ortak payların yüzde altmış yedisini, finansal yatırımcı "
     "yüzde otuz üçünü elinde tutuyor. Devir sonrası alıcı yüzde yetmiş "
     "beşe ulaşır.\n" + KAPANIS,
     set(), "oranlar PAY oranıdır; hiçbir mevzuat eşiği anılmıyor"),

    ("V-09", "dava ve dosya numaraları",
     "# Uyuşmazlık envanteri\n\n"
     "İstanbul 3. Asliye Ticaret Mahkemesi 2024/1157 E. sayılı dosya "
     "derdest. Ayrıca 2023/4412 E. sayılı dosyada karar kesinleşti.\n"
     + KAPANIS,
     set(), "rakamlar DOSYA numarasıdır, eşik değil"),

    ("V-10", "Türkçe tarih biçimi",
     "# İnceleme notu\n\n"
     "Veri odası 14 Mart 2026 tarihinde açıldı; son yükleme "
     "27.08.2026 tarihlidir.\n" + KAPANIS,
     set(), "tarihler Türkçe biçimde — güncellik kapısı susmalı [B-21]"),

    ("V-11", "koltuk dosyası — kaynak beyanlı",
     "# Martin Lipton\n\n## Kaynak durumu\n\n"
     "Bu koltuk, adı geçen hukukçunun yayımlanmış yazılarına dayanır.\n\n"
     "## Konuşmadığı yer\n\nTürk hukuku.\n",
     set(), "koltuk kapısının istediği beyan var",
     "birimler/_koltuklar/deneme.md"),

    ("V-12", "müvekkil kod adı — iç yazışma",
     "# Proje Anadolu — durum\n\n"
     "Karşı taraf inceleme cevaplarını bu hafta veriyor.\n" + KAPANIS,
     set(), "kod adı zaten ANONİMLEŞTİRMEDİR, sızıntı değil"),

    ("V-13", "emsal metni — sözleşme dili",
     "# Emsal madde\n\n"
     "\"Satıcı, Kapanış Tarihi itibarıyla Hedef Şirket'in paylarının "
     "tamamının maliki olduğunu beyan ve taahhüt eder.\"\n" + KAPANIS,
     set(), "beyan bir SÖZLEŞME hükmüdür, hukuki görüş değil"),

    ("V-14", "kısa iç not — çıktı değil",
     "Toplantı 15.00'e alındı.\n",
     set(), "esaslı çıktı değil; hiçbir kapı ateşlememeli"),

    ("V-15", "yaptırım taraması — soyutlanmış sorgu",
     "# Yaptırım taraması\n\n"
     "Karşı taraf ve gerçek lehtarlar OFAC, AB ve OFSI listelerinde "
     "aratıldı. Eşleşme yok. Sorgu soyutlanarak yapıldı; gerçek ad dış "
     "aramaya sokulmadı.\n" + KONTROL + KAPANIS,
     set(), "\"eşleşme yok\" olumsuz iddia AMA yöntemi ve kapsamı yazılı"),

    ("V-17", "düzenleyici yüzde — tam biçimli ve DAYANAKLI",
     "# Pay alım teklifi zorunluluğu\n\n"
     "Hedefin oy haklarının yüzde ellisinden fazlasının devri, SPK'nın "
     "II-26.1 sayılı Tebliği uyarınca zorunlu pay alım teklifi doğurur. "
     "Ortaklıktan çıkarma hakkı için aranan oran yüzde doksan sekizdir.\n"
     + KONTROL + KAPANIS,
     set(), "yüzde DÜZENLEYİCİ bağlamda — dayanak, tarih ve Kontrol edildi "
            "var, dolayısıyla üç kapı da susmalı"),

    ("V-16", "mevzuat metninin doğrudan alıntısı",
     "# TTK m.595 metni\n\n"
     "\"Esas sermaye payının devri ve devir borcunu doğuran işlemler yazılı "
     "şekilde yapılır ve tarafların imzaları noterce onanır.\"\n" + KAPANIS,
     set(), "birebir alıntı; kapı alıntıyı iddia sanmamalı"),
]

# Bilerek İHLALLİ metinler — kapı bunlarda ateşlemeli. Bunlar takımın
# kendi körlüğünü ölçer: hepsi "temiz" çıkarsa kapılar ölmüş demektir.
IHLALLI = [
    ("V-20", "dayanaksız eşik rakamı",
     "Ciro eşiği 3.000.000.000 TL'dir.\n" + KAPANIS,
     {"kanit", "guncellik", "arastirma"},
     "rakam var; dayanak YOK, doğrulama tarihi YOK, Kontrol edildi YOK — "
     "üç kapı da haklı ateşler. İlk sürümde yalnızca kanit beklenmişti; "
     "dar bir BEKLENTİ de bir sınama kusurudur"),
    ("V-21", "avukat başlığı olmayan tavsiye",
     "# Not\n\nKurul'a bildirimde bulunmanız gerekir.\n",
     {"kapsam"}, "tavsiye kipi, avukat başlığı yok"),
    ("V-22", "kaynak beyansız koltuk",
     "# Yeni Koltuk\n\nGörüşü şudur: beyanlar dar tutulmalıdır.\n",
     {"koltuk"}, "koltuk dosyası, Kaynak durumu yok",
     "birimler/_koltuklar/beyansiz.md"),
    ("V-24", "dayanaksız DÜZENLEYİCİ yüzde eşiği",
     "# Not\n\nZorunlu pay alım teklifi eşiği yüzde ellidir.\n" + KAPANIS,
     {"kanit", "guncellik", "arastirma"},
     "Daraltmanın açtığı olası delik: düzenleyici bağlamdaki bir yüzde, "
     "dayanaksız kaldığında HÂLÂ bloklanmalı. Bloklanmıyorsa V-03/V-08 "
     "düzeltmesi kaçırma yüzeyi açmış demektir"),

    ("V-23", "Kontrol edildi satırı olmayan depo atfı",
     "github.com/opensanctions/nomenklatura deposuna bakın.\n" + KAPANIS,
     {"arastirma"}, "depo anıldı, Kontrol edildi yok"),
]

_yanlis_yerlesim = [k[0] for k in IHLALLI if not k[3]]
assert not _yanlis_yerlesim, (
    "IHLALLI listesinde sıfır beklentili kayıt var: %s. Böyle bir kayıt "
    "V-30'un canlılık sayımını sahte biçimde yükseltir (set() & X == set() "
    "her zaman doğrudur). Meşru metinler KORPUS'a aittir."
    % _yanlis_yerlesim)

sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def ates(metin, yol=None):
    return {k for k, _ in kapi.denetle(metin, bugun=BUGUN, yol=yol)}


yanlis_pozitif, kacirma = [], []
for kayit in KORPUS + IHLALLI:
    kod, baslik, metin, bekleniyor, gerekce = kayit[:5]
    yol = kayit[5] if len(kayit) > 5 else None
    gercek = ates(metin, yol)
    fazla = gercek - bekleniyor
    eksik = bekleniyor - gercek
    if fazla:
        yanlis_pozitif.append("%s: %s" % (kod, ", ".join(sorted(fazla))))
    if eksik:
        kacirma.append("%s: %s" % (kod, ", ".join(sorted(eksik))))
    vaka(kod, baslik, not (fazla or eksik),
         ("YANLIŞ POZİTİF: %s ateşledi (%s)"
          % (", ".join(sorted(fazla)), gerekce)) if fazla
         else ("KAÇIRMA: %s susmuş" % ", ".join(sorted(eksik))) if eksik
         else gerekce)

# --- V-30 · takım kendi körlüğünü ölçer -------------------------------
# Meşru korpusun tamamı temiz çıkıyorsa iki açıklama vardır: kapılar iyi
# ayarlanmıştır, YA DA kapılar ölüdür. İHLALLİ metinler bu ikisini ayırır.
ihlal_yakalandi = sum(
    1 for k in IHLALLI
    if (k[3] & ates(k[2], k[5] if len(k) > 5 else None)) == k[3])
vaka("V-30", "kapılar bu korpusta CANLI (ihlalli metinler yakalanıyor)",
     ihlal_yakalandi == len(IHLALLI),
     "%d/%d ihlalli metin yakalandı — meşru korpusun temiz çıkması "
     "kapıların ölü olmasından değil" % (ihlal_yakalandi, len(IHLALLI)))

# --- V-31 · oran ------------------------------------------------------
vaka("V-31", "meşru iş ürününde yanlış pozitif yok",
     not yanlis_pozitif,
     "; ".join(yanlis_pozitif) if yanlis_pozitif
     else "%d meşru metnin hiçbirinde kapı ateşlemedi" % len(KORPUS))


BEKLENEN_VAKA = 24  # sessizce kaybolan bir vaka, kırmızı vakadan kötüdür


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("V-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA V — kapılar DOĞRU işi bloklıyor mu")
    print("=" * 96)
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, _ = beklenen.durum(kod, gecti)
        print("%s %-6s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    _sinyal, _sayim = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("-" * 96)
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _sayim["GEÇTİ"], _sayim["BEKLENEN"], _sinyal))
    return _sinyal


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
