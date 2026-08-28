#!/usr/bin/env python3
"""KÖR SINAMA AQ — yaptırım taramasının zaman ekseni.

Yönelim (otuz beşinci tur). Kök üç kez göründü (§11 eşikler, §8 çatışma,
§13 katalog): kitap kontrolleri OLAYLARA değil ANLARA bağlıyor. Üç örnek bir
sınıftır ve yirmi yedinci turun dersi şudur — bir örneği düzeltmek sınıfı
kapatmaz. Bu yüzden sistemdeki bütün kontrol noktaları tarandı:

  * altı KAPI  — yazma anına bağlı. DOĞRU bağlanma: saklanan bir sonuç
                 taşımazlar, üretildiği anda metni denetlerler. Muaf.
  * denetim    — yapıya bakar; yapı dış bir olayla bozulmaz. Muaf.
  * eşik/çatışma/katalog — üç bulgu, üç yama (31, 33, 34. turlar).
  * `yaptirim-taramasi` — sonucu EN HIZLI bozulan kontrol.

Yaptırım taraması diğerlerinden farklı: kitap burada zaman sorusunu SORUYOR
ve üç kontrol noktası veriyor — "gizlilik sözleşmesinden önce, münhasırlıktan
önce, imzadan önce". Yani kitabın en iyi bağlanmış kontrolü budur.

Ama üçü de İMZAYA kadar. Ve kitabın KENDİ §5.1'i imza ile kapanış arasına bir
bekleme koyuyor: bildirime tabi bir işlem izin alınana kadar askıdadır. O
aralık ayları bulabilir; yaptırım listelerine atama ise haftalık yapılır.
Kapanış kontrol listesinde yeniden tarama adımı YOK.

Sonuç, bu incelemede bulunan en ağır sonuçlu boşluktur: imzada temiz olan bir
taraf, izin beklenirken listeye girebilir ve işlem kapatılır. Yanlış bir eşik
bildirimi etkiler; bu, işlemin tamamlanmasının hukuka uygun olup olmadığını
etkiler.
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
    return re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", " ", m, flags=re.S))


TARAMA = duz(oku(".claude", "skills", "yaptirim-taramasi", "SKILL.md"))
KAPANIS = duz(oku(".claude", "skills", "kapanis-listesi", "SKILL.md"))
KAPANIS_K = duz(oku(".claude", "commands", "kapanis.md"))
REKABET = duz(oku("birimler", "rekabet", "yontem", "esikler.md")) or \
    duz(oku("birimler", "rekabet", "yontem", "tr-esikler.md"))

# --- AQ-01 · tarama kontrol noktaları KAPANIŞI kapsıyor mu ------------
# Ölçüt kitabın kendi cümlesinden: "Ne taranır, ne zaman — Üç nokta: ...".
# O listeye kapanış (ya da izin sonrası) dâhil mi?
# [yakınlık tuzağı · bu oturumda DÖRDÜNCÜ kez, yine kendi ölçütümde]
# Ölçüt önce "Ne taranır, ne zaman" başlığından sonraki 300 KARAKTERE
# bakıyordu. Yama o pencereye bir de AÇIKLAMA paragrafı ekledi ("İmza ile
# kapanış arasındaki aralık…") ve mutasyonda kontrol noktası geri alınsa
# bile pencerede "kapanış" kaldığı için vaka yeşil kalıyordu.
# Kalıcı ders: iddiayı taşıyan EN KÜÇÜK sözdizimsel birimi ölç — cümle ya da
# cümlecik — asla bir karakter penceresi. Pencere, komşuyu kanıt sanar.
_nokta = re.search(r"(?:Üç|Dört|Beş|İki)\*{0,2}\s+nokta:[^.]*\.", TARAMA)
_liste = _nokta.group(0) if _nokta else ""
_kapanis_var = re.search(r"kapanış", _liste, re.I) is not None
vaka("AQ-01", "yaptırım taramasının kontrol noktaları kapanışı da kapsıyor",
     _kapanis_var,
     "kontrol noktaları imzaya kadar; §5.1 imza ile kapanış arasına izin "
     "beklemesi koyuyor ve listelere atama haftalık yapılır")

# --- AQ-02 · kapanış listesi yeniden tarama adımı taşıyor mu ---------
_yeniden = any(re.search(r"yaptırım|OFAC|yeniden tara|tarama", m, re.I)
               for m in (KAPANIS, KAPANIS_K))
vaka("AQ-02", "kapanış kontrol listesi yaptırım yeniden taramasını içeriyor",
     _yeniden,
     "kapanış listesi izin yazısını ve organ kararlarını teyit ediyor; "
     "tarafların hâlâ temiz olup olmadığını sormuyor")

# --- AQ-03 · OLUMLU KONTROL: aralık kitabın KENDİ tasarımından doğuyor
# Boşluğun varsayımsal olmadığını gösterir: bekleme kitabın kendi kuralı.
# [aynı ders, aynı turda üçüncü kez] Ölçüt önce serbest bir sözcük listesi
# arıyordu ve `re.I` yüzünden bir BAŞLIĞA ("İzin Alın") takılıyordu — kuralın
# kendisine değil. Ölçüt kuralı taşıyan cümleye bağlandı; kitabın kendi
# cümlesi zaten bu turun tam konusudur: "İmza serbesttir; kapanış değildir."
_askida = False
for _c in re.split(r"(?<=[.;])\s+", REKABET):
    if not re.search(r"izin|bildirim", _c, re.I):
        continue
    if re.search(r"geçerlilik kazanmaz|kapanış değildir|askıda", _c, re.I):
        _askida = True
        break
vaka("AQ-03", "imza-kapanış aralığı kitabın kendi kuralından doğuyor",
     _askida,
     "§5.1 bildirime tabi işlemi izne bağlıyor — aralık kitabın tasarımı"
     if _askida else "rekabet yöntem dosyasında bekleme kuralı bulunamadı")

# --- AQ-04 · OLUMLU KONTROL: boş sonuç temizlik kanıtı değil ---------
_bos = re.search(r"eşleşmenin yokluğu temizlik kanıtı değil", TARAMA, re.I) \
    is not None
# [kırk birinci tur · KREDİ DÜZELTMESİ] Bu vaka kurulu beceriyi ölçer ve
# ölçtüğü cümle KİTABIN DEĞİL, BENİM yamamdır. Alıntı doğrulaması (AW)
# gösterdi ki "eşleşmenin yokluğu temizlik kanıtı değildir" kitapta hiç
# geçmiyor; §14 aynı ilkeyi GitHub aramaları için kuruyor ama §13.3 onu
# yaptırım taramasına taşımıyor. Otuz beşinci turda bu cümleyi kitaba
# atfedip kitabı övmüştüm — kendi yamamı kitabın metni sanarak.
vaka("AQ-04", "kurulu beceride boş sonuç tuzağı kapalı",
     _bos,
     "kurulu becerede var — AMA bu cümle YAMADIR; kitabın §13.3'ü boş "
     "sonucun ne anlama geldiğini söylemiyor (bkz. errata §13.3)" if _bos
     else "boş sonuç tuzağı ele alınmamış")

# --- AQ-05 · OLUMLU KONTROL: sır kuralı burada mutlak ----------------
_sir = (re.search(r"dış aramaya G[İI]RMEZ|dış aramaya girmez", TARAMA)
        is not None
        and re.search(r"insan kararı", TARAMA, re.I) is not None)
vaka("AQ-05", "gerçek ad dış aramaya girmiyor, taranması insan kararı",
     _sir, "kural 6 burada mutlak ve istisnası insana bırakılmış" if _sir
     else "sır kuralı ya da insan kararı ifadesi eksik")


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AQ-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
