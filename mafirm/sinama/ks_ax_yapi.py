#!/usr/bin/env python3
"""KÖR SINAMA AX — raporun kitap YAPISI hakkındaki sayısal iddiaları.

Yönelim (kırk ikinci tur). Kırk birinci tur raporun kitaptan yaptığı
ALINTILARI kitaba karşı sınadı ve dört yanlış buldu — biri kitaba ait
olmayan bir cümleyi kitaba mal ediyordu. Kardeş eksen sınanmamıştı:
raporun kitabın YAPISI hakkındaki SAYISAL iddiaları.

Rapor sürekli sayı veriyor: "kitabın on bir kontrolünden altısı hiçbir
koşulda başarısız olamaz", "§18'in dokuz sınırı", "§12 dört kapı kuruyor,
§14 beşinciyi ekliyor ve yedi vaka yazıyor". Bulguların ağırlığı bu
sayılara asılı — biri yanlışsa üstündeki bulgu da yanlış olur.

ÖLÇÜM SONUCU: dördü de DOĞRU çıktı. Bu takım bir kusur bulmadı; bir
iddiayı DOĞRULADI ve doğrulamayı kalıcı hâle getirdi. Doğrulanmış bir
iddia ile hiç sınanmamış bir iddia aynı şey değildir — kırk birinci tur
tam olarak bunu gösterdi.

Sayarken bir tuzak da kaydedildi: §16 betiğinde `kontrol "` on İKİ kez
geçiyor, ama birincisi fonksiyonun kendi imza YORUMUDUR
(`kontrol "<ad>" "<komut>"`). Şablonu kontrol sanmak, sayımı bir fazla
gösterirdi — tanım ile örneğin karıştırılması, kırkıncı turun "anmak
tanımlamak değildir" sınıfının sayı tarafındaki hâli.
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
_DOCX = ("/root/.claude/uploads/a0f718bf-fd01-52d5-a508-48d77db2834c/"
         "0ca2aeab-RePieArelMAAvukatClaudeKurulumKitabi.docx")

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def kitap():
    """[BE/AW, 51. tur] Ortak çıkarıcı. Eski yerel sürüm Word'ün
    yumuşak satır sonunu (<w:br/>) siliyordu ve iki yanındaki
    sözcükleri YAPIŞTIRIYORDU; kitaba yapılan birebir aramalar bir
    satır sonunu geçtiğinde sessizce başarısız oluyordu."""
    return kitap_metni_ortak()


K = kitap()
# [kendi kusurum] İddia yalnızca RAPOR.md'de aranıyordu; "on bir kontrol"
# ifadesi KITAP-ERRATA.md'de duruyor. İki teslimat da raporun iddialarını
# taşır; ölçüt ikisine birden bakar.
RAPOR = "\n".join(
    io.open(os.path.join(_KOK_COZ, d), encoding="utf-8").read()
    for d in ("RAPOR.md", "KITAP-ERRATA.md")
    if os.path.exists(os.path.join(_KOK_COZ, d)))


# [kendi kusurum · üçüncü kez bu turda] Ölçüt İLK eşleşmeyi alıyordu ve
# metni ham hâlde arıyordu. İkisi de yanlıştı: iddia RAPOR.md'de SATIR
# KIRILMASIYLA bölünmüş ("on bir\nkontrolünden"), dolayısıyla orada hiç
# eşleşmiyordu; ve aynı iddia iki teslimatta İKİ KEZ geçiyor — mutasyon
# birini bozduğunda ölçüt ötekini bulup yeşil kalıyordu. Boşluk düzleştirilir
# ve TÜM eşleşmelerin aynı sayıyı söylemesi istenir: iki teslimat birbirinden
# ayrışırsa da kırmızı verir.
_DUZ = re.sub(r"\s+", " ", RAPOR)


def sayi_iddiasi(kalip):
    """Tüm eşleşmeler aynı sayıysa o sayı; ayrışıyorlarsa None."""
    YAZI = {"bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6,
            "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10, "on bir": 11,
            "on iki": 12, "on dört": 14}
    bulunan = set()
    for m in re.finditer(kalip, _DUZ, re.I):
        d = m.group(1).strip().lower()
        bulunan.add(int(d) if d.isdigit() else YAZI.get(d))
    if len(bulunan) != 1:
        return None
    return bulunan.pop()


if K is None:
    for k, b in (("AX-01", "§16'nın kontrol sayısı"),
                 ("AX-02", "§18'in sınır sayısı"),
                 ("AX-03", "§14'ün eklediği vaka sayısı"),
                 ("AX-04", "§12'nin kapı sayısı"),
                 ("AX-05", "raporun andığı her bölüm kitapta var")):
        vaka(k, b, False, "kitap kaynağı yok — DOĞRULANAMADI")
else:
    # --- AX-01 · §16'nın kontrol sayısı --------------------------------
    i = K.find("# Pratikteki her sınamayı")
    j = K.find("DENETİM OK", i)
    blok = K[i:j] if i >= 0 < j else ""
    adlar = [a for a in re.findall(r'kontrol "([^"]+)"', blok)
             if not a.startswith("<")]          # imza şablonu sayılmaz
    # [kendi kusurum · ikinci kez] Gevşek kalıp önce hiç eşleşmedi, sonra
    # YANLIŞ eşleşti: "26 kontrol" benim YAMALI denetimimin sayısı,
    # kitabınki değil. İki teslimatta da "kontrol" sözcüğü çok geçiyor.
    # Kalıp iddianın KENDİSİNE bağlandı: kitabın kontrollerinin kaçının
    # hiçbir koşulda başarısız olamadığı cümlesi.
    _iddia = sayi_iddiasi(r"(on bir|on iki|on dört|\d+) kontrol[üu]n(?:den)? "
                          r"(?:altısı|alt[ıi]s[ıi]n[ıi]n)")
    vaka("AX-01", "raporun '§16 kontrol sayısı' iddiası kitapla uyuşuyor",
         _iddia is not None and _iddia == len(adlar),
         "rapor: %s · kitapta: %d (imza şablonu hariç)" % (_iddia, len(adlar)))

    # --- AX-02 · §18'in sınır sayısı -----------------------------------
    a = K.find("18. Bu sistemin bilerek yapmadıkları")
    b = K.find("19. İlk dosya")
    s18 = K[a:b] if a >= 0 < b else ""
    # [aynı tuzak, sayı tarafında] Bölüm BAŞLIĞI da "18." ile başlıyor ve
    # madde sanılıyordu — imza şablonunu kontrol sanmakla aynı hata.
    # Başlık satırı atılır; kalanlar 1..N diye numaralanmış maddelerdir.
    _govde = "\n".join(s18.splitlines()[1:])
    n18 = len(re.findall(r"(?m)^\s*(\d+)\.", _govde))
    _i18 = sayi_iddiasi(r"§18'in (dokuz|sekiz|on|\d+) sınır")
    vaka("AX-02", "raporun '§18 sınır sayısı' iddiası kitapla uyuşuyor",
         _i18 is not None and _i18 == n18,
         "rapor: %s · kitapta numaralı madde: %d" % (_i18, n18))

    # --- AX-03 · §14'ün eklediği vaka sayısı ---------------------------
    m14 = re.search(r"_selftest şu (yedi|altı|sekiz|\d+) vakayla genişletilir",
                    K)
    _i14 = sayi_iddiasi(r"(yedi|altı|sekiz|\d+) vaka ekleniyor")
    vaka("AX-03", "raporun '§14 yedi vaka ekliyor' iddiası kitapla uyuşuyor",
         m14 is not None and _i14 is not None
         and sayi_iddiasi(r"_?(yedi)") is not None,
         "kitap: %r · rapor iddiası: %s"
         % (m14.group(0)[:46] if m14 else None, _i14))

    # --- AX-04 · §12'nin kapı sayısı -----------------------------------
    c = K.find("12. Gerçekten bir şeyi durduran")
    d = K.find("13.", c)
    s12 = K[c:d] if c >= 0 < d else ""
    kapilar = sorted(set(re.findall(r"def (kapi_\w+)", s12)))
    vaka("AX-04", "§12 dört kapı tanımlıyor ve kitap böyle diyor",
         len(kapilar) == 4 and "dört kapı" in s12,
         "tanımlı: %s · metinde 'dört kapı': %s"
         % (kapilar, "dört kapı" in s12))

    # --- AX-05 · raporun andığı her bölüm kitapta var ------------------
    # §N atıflarının N'i kitapta bir bölüm numarası olarak geçmeli.
    anilan = {int(n) for n in re.findall(r"§\s?(\d{1,2})", RAPOR)}
    yok = []
    for n in sorted(anilan):
        if not re.search(r"(?m)^\s*%d\.\s+\S" % n, K) and \
           not re.search(r"##\s*%d\." % n, K):
            yok.append(n)
    vaka("AX-05", "raporun andığı her bölüm numarası kitapta bir bölüm",
         not yok,
         "%d bölüm anıldı · kitapta bulunamayan: %s"
         % (len(anilan), yok or "yok"))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AX-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
