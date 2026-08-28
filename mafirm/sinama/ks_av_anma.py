#!/usr/bin/env python3
"""KÖR SINAMA AV — "anmak, tanımlamak değildir" sınıfının taraması.

Yönelim (kırkıncı tur). Son yedi turda bulunan ölçüm kusurlarının çoğu tek
bir sınıfa indi ve sınıf beş ayrı kılıkta göründü:

  AN-05  yamayı açıklayan HTML YORUMU, prosedürün yerine geçti
  AM-01  yamanın AÇIKLAMA CÜMLESİ, arama talimatının yerine geçti
  AE-03  kusuru anlatan BELGE DİZGESİ, kusurun kendisi sanıldı
  M-03   uydurma kimlik, onu anan FIXTURE ve YORUM sayesinde "tanımlı" oldu
  AQ-01  300 karakterlik PENCERE, komşu cümleyi kanıt saydı

AE Türkçe desen sınıfını tarıyor; bu sınıf için hiçbir tarama yoktu. Bu takım
onu kurar.

Ve tarama YAZILIRKEN sınıf bir kez daha göründü — bu kez taramanın kendisinde.
İlk sürüm bir takımın kaynağındaki her dizgeyi, o takımın okuduğu her dosyayla
eşleştiriyordu. Altı aday buldu; **beşi taramanın kendi yanlış atfıydı**:

    "mutasyon" in a          -> `a` bir DOSYA ADI (listdir), dosya içeriği değil
    "SELFTEST OK" in r.stdout-> ALT SÜREÇ ÇIKTISI, dosya değil   (iki takımda)
    "json.dumps" in ozgun_kapi-> okunan dosya kitaba SADIK sürüm, yamalı değil

Yani "aynı kaynakta geçiyor" ile "o dosyaya karşı sınanıyor" karıştırılmıştı:
sınıfın ta kendisi, sınıfı arayan araçta. Ölçüt hafif bir VERİ AKIŞINA
bağlandı: bir dizge, ancak o dosyanın metnini TUTAN DEĞİŞKENE karşı
sınanıyorsa o dosyaya ait sayılır.

Kalan tek aday gerçekti: AF-04, `"belirti" in _hepsi` diyordu ve epilog.py'den
belirti mantığının TAMAMI silindiğinde hâlâ geçiyordu — çünkü dizge hepsi.sh'in
bir yorumunda duruyordu. Üstelik o yorumu, ayrıştırmayı ANLATMAK için otuz
dokuzuncu turda ben yazmıştım. Kapsamayı koruyan şey kod değil, kodu anlatan
cümleydi.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
_S = os.path.join(_KOK_COZ, "sinama")

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def yorum_bolgeleri(t, uzanti):
    ar = []
    if uzanti in (".py", ".sh"):
        for m in re.finditer(r"(?m)^[ \t]*#[^\n]*", t):
            ar.append(m.span())
    if uzanti == ".py":
        for m in re.finditer(r'("""|\'\'\')(?:.|\n)*?\1', t):
            ar.append(m.span())
    if uzanti == ".md":
        for m in re.finditer(r"<!--(?:.|\n)*?-->", t):
            ar.append(m.span())
    return ar


def sadece_yorumda(t, lit, ar):
    yerler = [m.start() for m in re.finditer(re.escape(lit), t)]
    return bool(yerler) and all(any(a <= y < b for a, b in ar) for y in yerler)


def _oku(rel):
    try:
        return io.open(os.path.join(_KOK_COZ, rel), encoding="utf-8",
                       errors="replace").read()
    except OSError:
        return None


def tarama():
    """(takım, dosya, dizge) — yalnızca VERİ AKIŞIYLA bağlanmış çiftler."""
    bulgular = []
    for ad in sorted(os.listdir(_S)):
        if not ad.startswith("ks_") or not ad.endswith(".py"):
            continue
        src = io.open(os.path.join(_S, ad), encoding="utf-8").read()
        # 1) DEĞİŞKEN -> DOSYA eşlemesi. Yalnızca dosya metnini tutanlar.
        degisken = {}
        for m in re.finditer(
                r'^(\w+)\s*=\s*(?:oku|_oku)\(\s*(?:os\.path\.join\()?'
                r'((?:[^()\n]|\([^()]*\))*)\)', src, re.M):
            parcalar = re.findall(r'"([^"]+)"', m.group(2))
            if parcalar:
                degisken[m.group(1)] = "/".join(parcalar)
        for m in re.finditer(
                r'^(\w+)\s*=\s*(?:io\.)?open\([^)]*"([\w./-]+)"[^)]*\)'
                r'(?:\.read\(\)|[^\n]*read\(\))', src, re.M):
            degisken[m.group(1)] = m.group(2)
        # [kendi kusurum · üçüncü kez bu turda] Veri akışı TEK ADIMLIKTI:
        # yalnızca `X = oku(...)` görüyordu. AF ise `_ham = oku(...)` sonra
        # `_hepsi = _ham + oku(...)` yazıyor; dizge `_hepsi`ye karşı sınanıyor
        # ve eşleşme kurulamıyordu. Mutasyon (AF'nin yorum ayıklamasını geri
        # al) AV-01'i kırmızıya ÇEVİRMEDİ — yani ölçüt, aradığı tuzağın
        # bulunduğu yeri göremiyordu. Akış bir adım YAYILIR: bir değişken,
        # bilinen bir değişkenden türetiliyorsa onun dosyalarını da taşır.
        for _ in range(2):
            for m in re.finditer(r"^(\w+)\s*=\s*([^\n]+)$", src, re.M):
                hedef, ifade = m.group(1), m.group(2)
                if hedef in degisken:
                    continue
                # AYIKLANMIŞ bir değer artık yorum taşımaz. Yayılma bunu
                # görmezse ölçüt, ayıklamayı ZATEN YAPMIŞ bir takımı
                # suçlar — aradığı hatayı kendi yapmış olur (dördüncü kez).
                if re.search(r"_yorumsuz\w*|\bduz\(|belgesiz", ifade):
                    continue
                for kaynak_dv, dosya in list(degisken.items()):
                    if re.search(r"\b%s\b" % re.escape(kaynak_dv), ifade):
                        degisken[hedef] = dosya
                        break
        if not degisken:
            continue
        # 2) O DEĞİŞKENE KARŞI sınanan dizgeler
        for dv, rel in degisken.items():
            yol = rel if os.path.isfile(os.path.join(_KOK_COZ, rel)) \
                else os.path.join("sinama", rel)
            t = _oku(yol)
            if t is None:
                continue
            ar = yorum_bolgeleri(t, os.path.splitext(yol)[1])
            if not ar:
                continue
            litler = set(re.findall(
                r'"([^"\\]{4,60})"\s+in\s+%s\b' % re.escape(dv), src))
            litler |= set(re.findall(
                r're\.search\(r?"([^"\\]{4,60})"\s*,\s*%s\b' % re.escape(dv),
                src))
            for lit in litler:
                if sadece_yorumda(t, lit, ar):
                    bulgular.append((ad, yol, lit))
    return bulgular


# --- AV-01 · hiçbir ölçüt YALNIZCA bir yorumla tatmin olmuyor --------
_bulgular = tarama()
vaka("AV-01", "hiçbir ölçüt yalnızca yorumda geçen bir dizgeye dayanmıyor",
     not _bulgular,
     "; ".join("%s → %s: %r" % b for b in _bulgular[:4]) or
     "veri akışıyla bağlanmış hiçbir çift yalnız yorumda değil")

# --- AV-02 · geniş karakter penceresi kullanan ölçüt yok ------------
# AQ-01'in dersi: pencere komşuyu kanıt sanar. 100+ karakterlik pencere,
# araya bir açıklama paragrafı girdiğinde ölçütü sessizce yalancı yapar.
# [kendi kusurum · aynı turda, İKİ KEZ] İlk sürüm 100+ olan HER pencereyi
# işaretledi ve K-12'yi yakaladı — ama K-12 koltuk dosyalarında bir tırnaklı
# sözün yakınında ATIF arıyor ve atıf gerçekten bir yakınlık olgusudur;
# orada pencere DOĞRU araçtır. İkinci sürüm ölçütü "yorum taşıyan dosya"ya
# daralttı ve bu sefer AP-02'nin gerçek tuzağını KAÇIRDI: oradaki kirletici
# bir yorum değil, becerinin kendi AÇIKLAMA DÜZYAZISIYDI. Yani ne "her
# pencere kötü" ne de "yalnız yorumlu dosyalarda kötü" doğru.
#
# Doğru ayrım otomatikleştirilemez: pencere, ANCAK yakınlığın kendisi kanıt
# olduğunda meşrudur (atıf), vekil olduğunda değil (bir alanın komutta
# geçmesi). O yüzden ölçüt BEYAN İSTER: geniş pencere kullanan her satır,
# gerekçesini yazmak zorundadır. Muafiyet listesi küçük ve görünür kalır;
# yeni bir pencere kendini savunmak zorundadır (P'nin MUAF deseni).
_genis = []
_BEN = os.path.basename(os.path.abspath(__file__))
for ad in sorted(os.listdir(_S)):
    if not ad.startswith("ks_") or not ad.endswith(".py") or ad == _BEN:
        continue
    satirlar = io.open(os.path.join(_S, ad), encoding="utf-8").read().splitlines()
    for i, satir in enumerate(satirlar):
        if satir.lstrip().startswith("#"):
            continue
        genis = [int(x) for x in re.findall(r"\.\{0,(\d+)\}", satir)]
        genis += [int(x) for x in re.findall(r"start\(\)\s*[-+]\s*(\d+)", satir)]
        if not any(g >= 100 for g in genis):
            continue
        onceki = "\n".join(satirlar[max(0, i - 6):i])
        if "AV-02 MUAF" in onceki or "AV-02 MUAF" in satir:
            continue
        _genis.append("%s:%d" % (ad, i + 1))
vaka("AV-02", "geniş pencere kullanan her ölçüt gerekçesini beyan ediyor",
     not _genis, "beyansız geniş pencere: %s" % (_genis or "yok"))

# --- AV-03 · OLUMLU KONTROL: ayıklama disiplini gerçekten var ------
_ayiklayan = [a for a in sorted(os.listdir(_S))
              if a.startswith("ks_") and a.endswith(".py")
              and re.search(r"_yorumsuz|def duz\(|belgesiz|startswith\(\"#\"\)",
                            io.open(os.path.join(_S, a),
                                    encoding="utf-8").read())]
vaka("AV-03", "yorum ayıklama disiplini takımlarda uygulanıyor",
     len(_ayiklayan) >= 5,
     "%d takım yorumları ölçüm dışında tutuyor" % len(_ayiklayan))

# --- AV-04 · taramanın KENDİSİ yanlış atıf yapmıyor ----------------
# Beş yanlış atıf sabit birer olumlu kontrol olarak tutulur: bir dizge bir
# DOSYA ADINA, bir ALT SÜREÇ ÇIKTISINA ya da BAŞKA bir dosyaya karşı
# sınanıyorsa, tarama onu o dosyaya ait saymamalı.
_yanlis_atif = [b for b in _bulgular
                if (b[0], b[2]) in {("ks_al_yan_etki.py", "mutasyon"),
                                    ("ks_as_kapi_kapsama.py", "SELFTEST OK"),
                                    ("ks_s_yalitim.py", "SELFTEST OK"),
                                    ("ks_ag_referans.py", "json.dumps")}]
vaka("AV-04", "tarama dosya adını / alt süreç çıktısını dosya içeriği saymıyor",
     not _yanlis_atif,
     "yanlış atıf geri geldi: %s" % (_yanlis_atif or "yok"))

# --- AV-05 · taramanın ayırt gücü: sentetik tuzak yakalanıyor mu ---
# Vakuum olmasın diye: tarama gerçekten bir tuzağı görebiliyor mu?
_sahte_dosya = "sinama/epilog.py"
_t = _oku(_sahte_dosya) or ""
_ar = yorum_bolgeleri(_t, ".py")
# epilog.py'nin belge dizgesinde geçen, kodunda geçmeyen bir ifade
_deneme = "dört dakika"
vaka("AV-05", "tarama yalnız-yorumda olanı ayırt edebiliyor",
     sadece_yorumda(_t, _deneme, _ar),
     "'%s' epilog.py'de yalnız belge dizgesinde: %s"
     % (_deneme, sadece_yorumda(_t, _deneme, _ar)))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
BEKLENEN_VAKA = 5


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("AV-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
