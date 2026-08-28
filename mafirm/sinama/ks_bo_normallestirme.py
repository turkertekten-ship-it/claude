#!/usr/bin/env python3
"""KÖR SINAMA BO — normalleştirmenin İKİ TARAFA da uygulanması.

Yönelim (altmış dördüncü tur). Altmış üçüncü tur sır kapısının AD KAYDI
ayağına Türkçe aksan katlaması ekledi: kayıtta "Işık Holding" varken dışarı
giden metinde "Isik Holding" yazılması kapıyı sessizce geçiyordu. Yama
çalıştı. Yamanın yanına yazdığım yorum ise şunu diyordu:

    "Katlama YALNIZCA ad kaydı karşılaştırmasında uygulanır: desen
     ayağındaki kalıplar (A.Ş., Ltd. Şti.) Türkçe harf İÇERİR ve metni
     katlayıp deseni katlamamak onları kırardı."

Cümle doğru, sonucu yanlıştı. O, katlamanın YARISINA karşı bir argümandır.
Ad kaydı ayağı zaten iki tarafı birden katlıyordu; desen ayağı ise hiç
katlanmadı — ve bu, bir tam koşum, bir mutasyon süpürmesi ve bir denetimden
YEŞİL geçti, çünkü hiçbir şey desen ayağının normalleştirmesini ölçmüyordu.

Ölçüldü (altmış dördüncü tur, yamadan önce) — beş sessiz kaçış:

    Hedef Acme Gida A.S. sirketidir.        GEÇTİ
    Target is Acme Gida A.S.                GEÇTİ
    Hedef Acme Gida Anonim Sirketi'dir.     GEÇTİ
    Hedef Acme Gida Ltd. Sti.               GEÇTİ
    Islem degeri 1.250.000.000 TL           GEÇTİ

"A.S.", bir Türk unvanının İngilizce bir SPA'da, bir veri odası dizin
listesinde ya da bir arama kutusunda aldığı EN YAYGIN biçimdir. Yani kaçış
kenar durum değil, ana yoldur.

Sınıf (yeni ve duran): İKİ TARAFI KARŞILAŞTIRAN HER KAPI AYAĞI, İKİ TARAFA
DA AYNI NORMALLEŞTİRMEYİ UYGULAR. Yarım uygulanan bir normalleştirme hiç
uygulanmayandan TEHLİKELİDİR: ölçen kişi kapatıldığını sanır.

Sınıfın ikinci yüzü de burada beyan edilir. Normalleştirme eksikliğinin YÖNÜ
kapının ne aradığına bağlıdır:

  * YASAK bir şeyi arayan ayakta (sır kapısı) eksik normalleştirme =
    SESSİZ KAÇIŞ. Tehlikeli yön.
  * ZORUNLU bir şeyi arayan ayakta (avukat başlığı, onay kaydı, kaynak
    beyanı) eksik normalleştirme = YANLIŞ BLOK. Can sıkıcı ama KAPALI yönde
    arızalanır ve kapının iletisi doğru yazımı zaten söyler.

BO-06 ikinci yönü davranışla sabitler: zorunlu bir şeyi arayan hiçbir kapı,
o şeyin normalleştirilmemiş bir varyantıyla SUSTURULAMAZ. Susturulursa bu,
tehlikeli yöne geçmiş yeni bir sızıntıdır.
"""
import importlib.util
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

KAPI_YOL = os.path.join(_KOK_COZ, ".claude/hooks/kapi.py")
KAYNAK = io.open(KAPI_YOL, encoding="utf-8").read()
_spec = importlib.util.spec_from_file_location("kapi", KAPI_YOL)
kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapi)

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


# --- BO-01 · sır kapısı, aksansız yazımı da yakalıyor ---------------
# Vakalar kapi.py'nin desenlerinden DEĞİL, bir hukukçunun gerçekten yazacağı
# cümlelerden türetildi: İngilizce bir belgede unvan, bir veri odası yolu,
# bir yatırım komitesi notunda bedel.
YASAK = [
    ("Hedef Acme Gıda A.Ş. şirketidir.",        "kitabın kendi vakası"),
    ("Hedef Acme Gida A.S. sirketidir.",        "aynı unvan, aksansız"),
    ("Target is Acme Gida A.S.",                "İngilizce belgede unvan"),
    ("Hedef Acme Gida Anonim Sirketi'dir.",     "açık unvan, aksansız"),
    ("Hedef Acme Gıda Anonim Şirketi'dir.",     "açık unvan, aksanlı"),
    ("Hedef Acme Gida Ltd. Sti.",               "limited, aksansız"),
    ("Hedef Acme Gıda Ltd. Şti.",               "limited, aksanlı"),
    ("Islem degeri 1.250.000.000 TL",           "bedel, aksansız"),
    ("İşlem değeri 1.250.000.000 TL",           "bedel, aksanlı"),
    ("Proje Sahin islemin kod adidir.",         "kod adı, aksansız"),
    ("dosyalar/Acme-Gida-devralma/ dizinine bak", "canlı iş yolu"),
]
_kacan = [ne for m, ne in YASAK if kapi.kapi_sir(m, disari=True) is None]
vaka("BO-01", "yasak biçimlerin aksansız yazımları da bloklanıyor",
     not _kacan,
     "%d yazımdan kaçan: %s" % (len(YASAK), _kacan or "yok"))

# --- BO-02 · yanlış pozitif yönü ------------------------------------
# Katlama, doğru işi bloklamamalı. Soyutlanmış sorgu KURAL 6'nın kendi
# öngördüğü yoldur: adı çıkar, yalnızca hukuki soruyu sor. O sorgular
# aksanlı da aksansız da yazılabilir ve ikisi de geçmelidir.
MESRU = [
    "Türkiye'de anonim şirket pay devri şekil şartı nedir?",
    "Turkiye'de anonim sirket pay devri sekil sarti nedir?",
    "2010/4 sayılı Tebliğ m.7 eşiği nedir?",
    "4054 sayılı Kanun m.10 askıya alma etkisi",
    "TTK m.595/2 sinirli sorumlu ortaklikta pay devri",
    "Limited sirket pay devri noter sarti",
    "site:rekabet.gov.tr birlesme devralma tebligi 2026/2",
]
_yanlis = [m for m in MESRU if kapi.kapi_sir(m, disari=True) is not None]
# İÇERİDE hiçbir yasak biçim ateşlemez: kural 6 DIŞARI kuralıdır.
_iceride = [ne for m, ne in YASAK if kapi.kapi_sir(m, disari=False) is not None]
vaka("BO-02", "soyutlanmış sorgular geçiyor, kapı yalnızca DIŞARI'da çalışıyor",
     not _yanlis and not _iceride,
     "yanlış bloklanan: %s · içeride ateşleyen: %s"
     % (_yanlis or "yok", _iceride or "yok"))

# --- BO-03 · kanıt ORİJİNAL metinden kesiliyor ----------------------
# Katlanmış metinde bulunan bir eşleşmenin ofsetleriyle ORİJİNALDEN kesmek,
# ancak katlama 1:1 ise doğrudur. Tabloya çok karakterli bir eşleme girerse
# (ör. "ş" -> "sh") ofsetler sessizce kayar: kapı sızıntıyı yakalar ama
# YANLIŞ metni gösterir — ve gösterdiği şey, insanın düzelteceği şeydir.
_bire_bir = all(len(chr(a).translate(kapi.TR_ASCII)) == 1
                for a in kapi.TR_ASCII)
_aksanli = "Hedef Acme Gıda Ltd. Şti."
_ileti = (kapi.kapi_sir(_aksanli, disari=True) or ("", ""))[1]
_alinti = re.search(r"'([^']*)'", _ileti)
_kesit = _alinti.group(1) if _alinti else ""
vaka("BO-03", "katlama 1:1 ve gösterilen kanıt orijinal metnin dilimi",
     _bire_bir and bool(_kesit) and _kesit in _aksanli,
     "1:1 %s · gösterilen kanıt %r · orijinalde var mı: %s"
     % (_bire_bir, _kesit, _kesit in _aksanli))

# --- BO-04 · KEŞİFLE: sır kapısında katlanmamış karşılaştırma yok ---
# Elle liste bayatlar (P, M, R, BJ, Q takımlarının dersi). Ölçüt, kapının
# GÖVDESİNİ okur: kapi_sir içindeki her re.search/re.finditer çağrısının
# hedefi katlanmış metin (_duz) olmalıdır. Yeni bir ayak eklenip ham `metin`
# üzerinde aranırsa bu vaka onu ADINI BİLMEDEN yakalar.
_i = KAYNAK.index("def kapi_sir(")
_j = KAYNAK.index("\ndef ", _i + 1)
GOVDE = KAYNAK[_i:_j]
_aramalar = re.findall(r"re\.(?:search|finditer|match|fullmatch)\("
                       r"[^,]+,\s*([A-Za-z_][A-Za-z0-9_]*)", GOVDE)
_ham = [h for h in _aramalar if h != "_duz"]
vaka("BO-04", "sır kapısındaki her arama KATLANMIŞ metin üzerinde",
     bool(_aramalar) and not _ham,
     "bulunan arama hedefleri: %s · katlanmamış: %s"
     % (_aramalar or "HİÇ ARAMA YOK — ölçüt vakumda", _ham or "yok"))

# --- BO-05 · katman kuralı: kapının KENDİ öz-sınaması da tutuyor ----
# Bu takım tek başına tutarsa, katlama geri alındığında kapının kendi
# öz-sınaması YEŞİL kalır ve kusur yalnızca burada görünür. Denetleyen
# takımın denetlediği şeyi tek başına tutması, bu incelemenin dört kez
# ihlal ettiği katman kuralıdır.
_k = KAYNAK.index("def _selftest")
OZ = KAYNAK[_k:KAYNAK.index("SELFTEST %s")]
_aksansiz_vaka = [s for s in re.findall(r'\("([^"]{6,90})"', OZ)
                  if kapi._aksansiz(s) == s and re.search(
                      r"A\.S\.|Ltd\. Sti\.|Anonim Sirketi", s)]
vaka("BO-05", "kapının öz-sınaması aksansız unvan vakası taşıyor",
     bool(_aksansiz_vaka),
     "öz-sınamadaki aksansız unvan vakaları: %s"
     % (_aksansiz_vaka or "YOK — katlama yalnızca BO tarafından tutuluyor"))

# --- BO-06 · ters yön: ZORUNLU şeyi arayan kapı susturulamıyor ------
# Sır kapısı YASAK bir şey arar: eksik normalleştirme = sessiz kaçış.
# Kapsam/onay kapıları ZORUNLU bir şey arar: eksik normalleştirme = yanlış
# blok, yani KAPALI yönde arıza. Bu vaka ikinci yönü sabitler — zorunlu bir
# şeyin normalleştirilmemiş varyantı kapıyı SUSTURMAMALI. Susarsa, eksik
# normalleştirme tehlikeli yöne geçmiş demektir.
#
# [Kendi kusurum · altmış dördüncü tur] İlk yazdığım sonda metni
# "TASLAK olmayan bir sey; onaylanmamistir." idi ve vaka kırmızı yandı. Kapı
# haklıydı: metin literal olarak TASLAK kelimesini TAŞIYOR ve kapı onu
# beyan sayıp susuyordu. Sonda YANLIŞ HEDEFE indi — mutasyon disiplininin
# aynı kuralı: hedefi ıskalayan bir sonda hiçbir şey sınamaz.
#
# Ama ıskalayan sonda BAŞKA bir şeye çarptı: "TASLAK olmayan" cümlesi
# yedinci kapıyı susturuyordu. Ölçüldü — üç OLUMSUZLANMIŞ beyan da
# susturuyordu:
#     "Bu belge TASLAK DEĞİLDİR." · "taslak aşaması geçilmiştir."
#     "Artık onay bekliyor değildir."  ve koltukta "KOLTUK BOŞ değildir."
# Üçü de belgenin NİHAİ olduğunu söyler, yani §9'un var olma sebebidir.
# Kapılar `_beyan_tasiyor` ile olumsuzlamaya duyarlı hâle getirildi ve sınıf
# BL takımında yedi kapıya birden, KEŞİFLE süpürüldü (BL-10). BO burada
# yalnızca normalleştirme eksenini tutar.
GORUS = ("Bu işlem bildirime tabidir.\n"
         "## Yetkili avukat görüşü gereken konular\nHepsi.\n")
_susturma_denemeleri = [
    # (sonda metni, susturmaması gereken kapı, ne denendi)
    ("Bu işlem bildirime tabidir.\n"
     "## Yetkili avukat gorusu gereken konular\nHepsi.\n",
     "kapsam", "avukat başlığı aksansız"),
    (GORUS + "Bu rapor onaylanmamistir.\n",
     "onay", "onay yokluk beyanı aksansız"),
]
_sustu = []
for _m, _kapi_adi, _ne in _susturma_denemeleri:
    _bulunan = {k for k, _ in kapi.denetle(_m, disari=True,
                                           yol="cikti/nota.md")}
    if _kapi_adi not in _bulunan:
        _sustu.append("%s (%s)" % (_ne, _kapi_adi))
# Sonda gerçekten hedefe iniyor mu: aynı metnin AKSANLI hâli kapıyı
# SUSTURMALI. Susturmuyorsa ölçüt normalleştirmeyi değil başka bir şeyi
# ölçüyordur ve yukarıdaki sonuç anlamsızdır.
_hedefte = ("kapsam" not in {k for k, _ in kapi.denetle(
    GORUS, disari=True, yol="cikti/nota.md")}
    and "onay" not in {k for k, _ in kapi.denetle(
        GORUS + "Bu rapor onaylanmamıştır.\n", disari=True,
        yol="cikti/nota.md")})
vaka("BO-06", "zorunlu bir şeyi arayan kapı, normalleştirilmemiş varyantla "
              "susturulamıyor",
     not _sustu and _hedefte,
     "susturulabilen kapı: %s · sonda hedefte mi (aksanlı hâl susturuyor mu): "
     "%s" % (_sustu or "yok", _hedefte))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 6


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BO-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
