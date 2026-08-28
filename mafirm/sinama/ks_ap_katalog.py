#!/usr/bin/env python3
"""KÖR SINAMA AP — §13 araç kataloğunun kurulumdaki hâli.

Yönelim (otuz dördüncü tur). Otuz üçüncü tur bir kök adlandırdı: kitap
kontrolleri OLAYLARA değil ANLARA bağlıyor. İki örneği vardı (§11 eşikler,
§8 çatışma). Bir kök mü yoksa iki tesadüf mü olduğunu anlamanın yolu üçüncü
bir yere bakmaktır. §13 araç kataloğu en iyi aday: kaydettiği her alan —
lisans, yıldız, son güncelleme — ZAMANLA BOZULUR ve kitabın "Karar" sütunu
onlara dayanır.

Ölçüm beklediğimden ağır çıktı. §13'ün kataloğu kurulumda **hiçbir dosya
bırakmıyor**. §2 klasörleri kuruyor (birimler, emsal, hafiza, dosyalar,
cikti) ve hiçbiri araç kataloğu için değil. Kitap "Hepsi 27 Ağustos 2026
tarihinde GitHub API'siyle doğrulandı" diyor — ama o cümle KİTAPTA, kurulan
sistemde değil. Sonuç: kurulumu yapan hukukçunun elinde

  * hangi araçların incelendiğine dair yerel bir kayıt YOK,
  * eskiyecek bir doğrulama tarihi YOK,
  * §16 denetiminin ya da herhangi bir komutun bakabileceği bir şey YOK.

Ve bozulma varsayımsal değil: yirmi dokuzuncu tur iki alanın çoktan
bozulduğunu ölçtü — bir depo 5 Ağustos 2024'te ARŞİVLENMİŞ, bir başkasının
VERİSİ CC BY-NC 4.0 (ticari kullanım yasak) iken kodu MIT.

Üçüncü bir bulgu da buradan çıktı: kitabın tazeleme becerisi `once-arastir`
GitHub API'sinden DÖRT alan okuyor — full_name, license.spdx_id,
stargazers_count, pushed_at. `archived` bunların arasında DEĞİL. Yani
kitabın kendi tazeleme aracı, yirmi dokuzuncu turda bulunan arşiv olgusunu
çalıştırıldığında bile GÖREMEZ.
"""
import importlib.util
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
    return re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", " ", m, flags=re.S))


# [AE-03 · altıncı kez, yazıldığı turda yakalandı] Çıplak .lower() Türkçede
# "İ" harfini i+U+0307'ye çevirir. Depo adları ASCII olduğu için bu örnekte
# zararsızdı — ama "bu örnek zararsız" muhakemesi tam olarak sınıfın dört kez
# sızmasına izin veren muhakemedir. Kapının kendi yardımcısı kullanılır.
_spec = importlib.util.spec_from_file_location(
    "kapi_ap", os.path.join(_KOK_COZ, ".claude/hooks/kapi.py"))
_kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_kapi)
kucult = _kapi.tr_kucult


ARASTIR = duz(oku(".claude", "skills", "once-arastir", "SKILL.md"))

# Kitabın §13'te adı geçen depolar. Katalog kurulumda ARANIR.
DEPOLAR = ("diff-match-patch", "lexnlp", "Blackstone", "courtlistener",
           "opensanctions", "nomenklatura")

# --- AP-01 · katalog kurulumda YERELDE duruyor mu ---------------------
# Ölçüt: kitabın kendi teslimatları (RAPOR/ERRATA/sınama takımı DEĞİL)
# içinde, en az iki deponun adını ve bir karar/lisans bilgisini taşıyan
# bir dosya olmalı. Yoksa katalog yalnızca kitapta yaşıyor demektir.
_haric = ("RAPOR.md", "KITAP-ERRATA.md", "kor-sinama-raporu.html")
_katalog = []
for kok, klasorler, dosyalar in os.walk(_KOK_COZ):
    klasorler[:] = [k for k in klasorler
                    if k not in (".git", "__pycache__", "sinama", "yamalar")]
    for ad in dosyalar:
        if ad in _haric or not ad.endswith((".md", ".txt")):
            continue
        icerik = oku(os.path.relpath(os.path.join(kok, ad), _KOK_COZ))
        # [kendi kusurum · aynı turda yakalandı] İlk ölçüt "dosyada iki
        # depo adı VE bir 'lisans/karar' sözcüğü geçiyor mu" diyordu ve
        # YEŞİL verdi. Yakaladığı dosya `hafiza/dogrulama-bulgulari.md` —
        # yani BENİM kör sınama sırasında ürettiğim bir teslimat, kitabın
        # kurduğu bir şey değil. Kendi yamalarım ağaçta dururken kitabı
        # ölçmek, ikisini birbirine karıştırır ve kitabı OLDUĞUNDAN İYİ
        # gösterir. Ölçüt §13'ün KENDİ yapısına indirildi: bir katalog,
        # SATIR SATIR her depoyu bir lisansla ve bir kararla eşleştirir.
        # Açık bulguları anlatan bir düzyazı dosyası bunu yapmaz.
        LISANS = r"MIT|Apache|AGPL|LGPL|GPL|BSD|MPL|CC[ -]BY|Unlicense"
        KARAR = r"kullan|kurulmaz|okunur|karar|reddedil|önerilm"
        satir_sayisi = 0
        for satir in icerik.splitlines():
            if not any(kucult(d) in kucult(satir) for d in DEPOLAR):
                continue
            if re.search(LISANS, satir) and re.search(KARAR, satir, re.I):
                satir_sayisi += 1
        if satir_sayisi >= 2:
            _katalog.append("%s (%d satır)"
                            % (os.path.relpath(os.path.join(kok, ad),
                                               _KOK_COZ), satir_sayisi))
vaka("AP-01", "§13 araç kataloğu kurulumda yerel bir dosya olarak duruyor",
     bool(_katalog),
     "katalog dosyası: %s — yoksa hangi aracın incelendiği, ne zaman "
     "doğrulandığı ve kararın ne olduğu yalnızca KİTAPTA yaşar"
     % (_katalog or "yok"))

# --- AP-02 · tazeleme becerisi `archived` alanını okuyor mu -----------
# §13'ün "Karar" sütunu bakım durumuna dayanıyor; arşivlenmişlik bunun
# YETKİLİ hâlidir ve API onu döndürür. pushed_at bir vekildir, olgu değil.
_alanlar = re.search(r"api\.github\.com/repos.{0,700}", ARASTIR, re.S)
_metin = _alanlar.group(0) if _alanlar else ""
_arsiv = "archived" in _metin
vaka("AP-02", "tazeleme becerisi deponun ARŞİVLENMİŞ olduğunu okuyor",
     _arsiv,
     "okunan alanlar arasında 'archived' yok — yirmi dokuzuncu turda "
     "bulunan arşiv olgusu (5 Ağustos 2024) bu araçla görülemezdi")

# --- AP-03 · kod lisansı ile VERİ lisansı ayrılıyor mu ---------------
# G-03: kod MIT, veri CC BY-NC 4.0 (ticari kullanım yasak). Tek bir
# "Lisans" alanı bu ayrımı taşıyamaz; API'nin license alanı da yalnızca
# deponun beyan ettiği KOD lisansını döndürür.
_veri_lisansi = re.search(r"veri lisans|data licen|veri.{0,20}lisans|CC BY",
                          ARASTIR, re.I) is not None
vaka("AP-03", "lisans kontrolü kod ile VERİ lisansını ayırıyor",
     _veri_lisansi,
     "beceri yalnızca deponun beyan ettiği kod lisansını okuyor; G-03'te "
     "kod MIT iken VERİ CC BY-NC 4.0 (ticari kullanım yasak) çıktı")

# --- AP-04 · OLUMLU KONTROL: hafızadan cevaplamak yasak --------------
_hafiza = (re.search(r"hafızadan cevaplama|Asla hafızadan", ARASTIR, re.I)
           is not None
           and "Kontrol edildi:" in ARASTIR)
vaka("AP-04", "tazeleme becerisi hafızadan cevaplamayı yasaklıyor",
     _hafiza, "mekanizma doğru: önce kaynak, sonra 'Kontrol edildi:' satırı"
     if _hafiza else "yasak ya da Kontrol edildi satırı eksik")

# --- AP-05 · OLUMLU KONTROL: var olan dosyalarda tarih disiplini var --
# §16 denetimi yöntem dosyalarının 'Doğrulama:' satırını sağlıyor. Yani
# disiplin KİTAPTA VAR; eksik olan onu araç kataloğuna uygulamak.
DENETIM = oku("denetim.sh")
_disiplin = re.search(r"Doğrulama:", DENETIM) is not None and \
    re.search(r"yontem", DENETIM) is not None
vaka("AP-05", "tarih disiplini var olan dosyalarda denetleniyor",
     _disiplin,
     "denetim yöntem dosyalarında 'Doğrulama:' arıyor — disiplin var, "
     "araç kataloğuna uygulanmamış" if _disiplin else "disiplin bulunamadı")


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AP-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
