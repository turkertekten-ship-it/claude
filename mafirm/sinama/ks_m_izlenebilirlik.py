#!/usr/bin/env python3
"""[AA-01] Takım adları TEK HARF varsayımı bu dosyada beş desende,
denetim.sh'te bir desende ve kapi.py'de bir yerde gömülüydü. Alfabe bitip
iki harfli takım (AA) eklenene kadar hiçbiri görünmedi: üç ayrı bileşen aynı
sessiz varsayımı taşıyordu ve üçü de "kapsıyorum" diyordu.

KÖR SINAMA M — errata ↔ sınama izlenebilirliği.

Bu rapor kitaba kırk küsur düzeltme öneriyor. Bir düzeltme önerisi, arkasında
onu gösteren çalışan bir sınama yoksa **bir kanaattir, bir bulgu değildir** —
ve kitabın kendi kanıt kuralı (CLAUDE.md §1) tam olarak bunu yasaklıyor:
"Dayanağı olmayan bir eşik yazılmaz."

Aynı ölçüt raporun kendisine uygulanır. Dört soru:

  M-01  her errata maddesi bir sınama vakasına atıf yapıyor mu
  M-02  atıf yapılan her vaka kimliği GERÇEKTEN var mı  (uydurma dayanak yok)
  M-03  [A] ve [B] maddelerinin atıfları kitaba sadık sistemde GERÇEKTEN
        başarısız oluyor mu (yoksa "bu kurulumu durdurur" sınanmamış demektir)
  M-04  ters kapsama: kitaba sadık sistemde başarısız olan her vaka
        errata'da ya da raporda açıklanmış mı

Bu takım kör sınamanın kendisini denetler.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402  — beyan edilmiş taban (XFAIL mantığı)


_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


# --- errata maddelerini ayrıştır -----------------------------------------
errata = open(os.path.join(_KOK_COZ, "KITAP-ERRATA.md"), encoding="utf-8").read()
satirlar = errata.splitlines()
maddeler = []          # (baslik, agirlik, [atifli kimlikler])
i = 0
while i < len(satirlar):
    m = re.match(r"^(?:- )?\*\*\[([ABC])\] (.+?)\*\*", satirlar[i])
    if m:
        agirlik, baslik = m.group(1), m.group(2)
        govde = [satirlar[i]]
        j = i + 1
        while j < len(satirlar) and not re.match(r"^(?:- )?\*\*\[[ABC]\] |^## ", satirlar[j]):
            govde.append(satirlar[j]); j += 1
        blok = "\n".join(govde)
        kimlikler = []
        for a in re.findall(r"\*\(([^)]+)\)\*", blok):
            for parca in re.split(r"[,;]", a):
                p = parca.strip().replace(" takımı", "")
                # ARALIK biçimi: B-07…B-09 / B-02..B-06  [M'nin kendi kusuru:
                # ilk sürüm yalnızca virgülle ayrılmışları görüyordu ve yedi
                # maddeyi "atıfsız" sanıyordu.]
                ar = re.match(r"^([A-Z]{1,2})-(\d+)\s*(?:…|\.\.\.|\.\.)\s*(?:[A-Z]{1,2}-)?(\d+)$", p)
                if ar:
                    h, b1, b2 = ar.group(1), int(ar.group(2)), int(ar.group(3))
                    kimlikler += ["%s-%02d" % (h, n) for n in range(b1, b2 + 1)]
                elif re.match(r"^[A-Z]{1,2}(-\d+[a-z]?)?$", p):
                    kimlikler.append(p)
        maddeler.append((baslik, agirlik, kimlikler))
        i = j
    else:
        i += 1

# --- suitelerdeki gerçek vaka kimliklerini topla -------------------------
tanimli = set()
takimlar = set()
for f in os.listdir(os.path.join(_KOK_COZ, "sinama")):
    if not (f.startswith("ks_") and f.endswith((".py", ".sh"))):
        continue
    icerik = open(os.path.join(_KOK_COZ, "sinama", f), encoding="utf-8").read()
    # [M'nin kendi kusuru] İlk sürüm yalnızca vaka("X-NN" biçimini görüyordu.
    # Gerçekte kimlikler üç biçimde doğuyor: doğrudan çağrı, sonuclar.append
    # ile ve BİÇİMLENDİRME ile ("J-07%s" % etiket). Üçü de taranır.
    for k in re.findall(r'"([A-Z]{1,2}-\d+[a-z]?)"', icerik):
        tanimli.add(k); takimlar.add(k[0])
    for kok_id, sonek in re.findall(r'"([A-Z]{1,2}-\d+)%s"\s*%\s*(\w+)', icerik):
        for e in re.findall(r'\("(\w)",', icerik):
            tanimli.add(kok_id + e)
        tanimli.add(kok_id)
# D ve E takımı kabuk betikleri: vaka kimlikleri yok, takım düzeyinde atıf
takimlar |= {"D", "E", "G", "H", "I"}
# G/H/I markdown raporlarındaki kimlikler
for f in ("ks_g_depolar.md", "ks_h_kaynaklar.md", "ks_i_mevzuat.md"):
    p = os.path.join(_KOK_COZ, "sinama", f)
    if os.path.exists(p):
        for k in re.findall(r"^###?\s*([GHI]-\d+)", open(p, encoding="utf-8").read(), re.M):
            tanimli.add(k)

# --- M-01 ---------------------------------------------------------------
atifsiz = [b for b, a, k in maddeler if not k]
vaka("M-01", "her errata maddesi bir sınama vakasına atıf yapıyor",
     not atifsiz,
     "%d madde · atıfsız %d: %s" % (len(maddeler), len(atifsiz),
                                    atifsiz or "yok"))

# --- M-02 ---------------------------------------------------------------
uydurma = []
for b, a, kimlikler in maddeler:
    for k in kimlikler:
        if len(k) == 1:
            if k not in takimlar:
                uydurma.append((b[:40], k))
        elif k not in tanimli:
            uydurma.append((b[:40], k))
vaka("M-02", "atıf yapılan her vaka kimliği gerçekten tanımlı",
     not uydurma,
     "%d tanımlı kimlik · uydurma dayanak: %s"
     % (len(tanimli), uydurma or "yok"))

# --- M-03 ---------------------------------------------------------------
# Kitaba sadık koşumun ham çıktısı: hangi vakalar KALDI?
once = os.path.join(_KOK_COZ, "sinama", "SONUC-once.txt")
kaldi_once = set()
if os.path.exists(once):
    kaldi_once = set(re.findall(r"^KALDI\s+([A-Z]{1,2}-\d+[a-z]?)", 
                                open(once, encoding="utf-8").read(), re.M))
# [otuz ikinci tur] Ölçüt eskiden HER ağır maddenin atfının sadık koşumda
# KALDI olmasını istiyordu. Sadık koşum yamalardan ÖNCEKİ ham çıktıdır ve o
# sırada var olmayan bir takımın vakası orada hiç görünemez — yani sonraki
# turlarda bulunan bir kusuru DOĞRU kimliğiyle anmak imkânsızlaşıyor, madde
# yanlış bir vakaya bağlanmaya itiliyordu. Ölçüt ikiye ayrıldı; her iki dalda
# da gerçek bir şart var, hiçbir madde şartsız kalmıyor:
#   * takım sadık koşumda VARSA  -> atıf orada KALDI olmalı (eski güç aynen)
#   * takım sonradan yazıldıysa  -> atıf, gerçekten TANIMLI bir vaka olmalı
# Geçerli vaka öneki = diskteki takımların harfi (ks_<harf>_...) + tabanda
# görülenler. Uydurma bir önek ("ZZ") hiçbirinde yoktur ve ölçüte GİRER.
_ONEKLER = {a.split("_")[1].upper()
            for a in os.listdir(os.path.join(_KOK_COZ, "sinama"))
            if a.startswith("ks_") and "_" in a[3:]}
_taban_onekleri = {k.split("-")[0] for k in kaldi_once}
_ONEKLER |= _taban_onekleri
# [otuz dokuzuncu tur] İlk sürüm yalnızca `.py` takımlarında tek bir
# `vaka("XX-nn")` imzasını arıyordu. Ama vakaların bir kısmı MARKDOWN
# takımlarında tanımlı (G, H, I) ve bazı python takımları başka bir imza
# kullanıyor (F, V, J). Sonuç: on meşru errata atfı "böyle bir vaka tanımlı
# değil" diye işaretlendi — onda sekizi yanlış işaretleyen bir ölçüt,
# kırmızıyı görmezden gelmeyi öğretir (AF-04'ün dersi). Ölçüt bütün takım
# dosyalarını (py, sh, md) tarayıp kimlik BİÇİMİNDEKİ her jetonu toplar;
# uydurma bir kimlik (ZZ-99) hiçbirinde geçmez ve yakalanır.
_tanimli = set()
_sin = os.path.join(_KOK_COZ, "sinama")
# D MUTASYON HARNESSİDİR: içinde bilerek BOZUK fixture'lar taşır — uydurma
# bir kimlik de dâhil. Onu "tanımlı vaka" kaynağı saymak, mutasyonun kendi
# fixture'ının mutasyonu görünmez kılması demektir. Otuzuncu turda AL-03'te
# düştüğüm tuzağın aynısı: KANIT, ÖLÇÜME KARIŞMAMALI.
# ANMAK, TANIMLAMAK DEĞİLDİR. Uydurma kimlik `ZZ-99` üç ayrı yerde geçiyordu:
# D'nin mutasyon fixture'ında, AU'nun sentetik beyanında, ve bu dosyada onu
# ANLATAN yorumda. Hepsi ölçütü tatmin ediyor ve uydurma kimlik "tanımlı"
# sayılıyordu — yorum/prosedür, açıklama/kural, belge dizgesi/kod ayrımının
# beşinci hâli.
#
# Ölçüt aparatın gerçek düzenine bağlandı: BİR TAKIM YALNIZCA KENDİ VAKALARINI
# TANIMLAR. `ks_au_epilog.py` AU-nn tanımlar; içinde geçen ZZ-99 bir anmadır.
# Uydurma bir önek için `ks_zz_*` dosyası hiç yoktur, dolayısıyla hiçbir yerde
# tanımlı olamaz.
for _ad in sorted(os.listdir(_sin)):
    if not _ad.startswith("ks_") or "_" not in _ad[3:]:
        continue
    _harf = _ad.split("_")[1].upper()
    try:
        _m = open(os.path.join(_sin, _ad), encoding="utf-8",
                  errors="replace").read()
    except OSError:
        continue
    _tanimli |= {k for k in re.findall(r"\b([A-Z]{1,2}-\d+[a-z]?)\b", _m)
                 if k.split("-")[0] == _harf}

agir = [(b, k) for b, a, k in maddeler if a in ("A", "B") and k]
sinanmamis = []
for b, kimlikler in agir:
    # [otuz dokuzuncu tur] Önek listesi "ABCE" diye SABİTLENMİŞTİ — takımlar
    # yalnızca A..E iken doğruydu. Bugün takımlar AU'ya kadar gidiyor ve
    # `ZZ-99` gibi uydurma bir kimlik ölçütün DIŞINDA kalıyordu: D'nin
    # "errata'ya uydurma vaka kimliği ekle" mutasyonu bu yüzden kaçtı.
    # Elle yazılmış liste, ölçtüğü şeyden ayrışır — bu oturumun üçüncü kez
    # gördüğü sınıf. Önekler artık diskteki takımlardan türetiliyor.
    # Ölçüt ÖNEK LİSTESİNDEN BİÇİME çevrildi. Önek listesi ("ABCE" idi, sonra
    # diskteki takımlardan türetildi) uydurma bir kimliği ölçütün DIŞINDA
    # bırakıyordu: `ZZ-99` bilinen bir önek taşımadığı için "vaka bile değil"
    # sayılıp atlanıyordu — yani en çok yakalanması gereken şey muaftı.
    # `*(...)*` içinden gelen her jeton zaten bir vaka atfı olmak üzere
    # yazılmıştır; ölçüt kimlik BİÇİMİNİ arar ve gerisini iki dala bırakır.
    somut = [k for k in kimlikler
             if re.match(r"^[A-Z]{1,2}-\d+[a-z]?$", k)]
    if not somut:
        continue
    tabanda = [k for k in somut if k.split("-")[0] in _taban_onekleri]
    if tabanda:
        if not any(k in kaldi_once for k in tabanda):
            sinanmamis.append((b[:44], tabanda, "sadık koşumda kalmamış"))
    # J takımı kimlikleri ÇALIŞMA ANINDA kuruyor: vaka("J-07%s" % etiket).
    # Statik tarama `J-07s`'yi göremez ama `J-07`'yi görür. Bir atfın TABANI
    # (sondaki küçük harf ekleri atılmış hâli) tanımlıysa atıf gerçektir.
    # Bunu doğrulamadan errata'yı "düzeltseydim" gerçek bir atfı bozacaktım —
    # ölçüt kırmızı verdiğinde önce ÖLÇÜTÜ sınamak gerekir.
    elif not any(k in _tanimli or re.sub(r"[a-z]+$", "", k) in _tanimli
                 for k in somut):
        sinanmamis.append((b[:44], somut, "böyle bir vaka tanımlı değil"))
vaka("M-03", "[A] ve [B] maddelerinin atıfları gerçek vakalara bağlı",
     not sinanmamis,
     "sadık koşumda kalan: %d · tanımlı vaka: %d · bağsız madde: %s"
     % (len(kaldi_once), len(_tanimli), sinanmamis or "yok"))

# --- M-04 ters kapsama ---------------------------------------------------
anilan = set()
for b, a, kimlikler in maddeler:
    anilan |= set(kimlikler)
rapor_metni = open(os.path.join(_KOK_COZ, "RAPOR.md"), encoding="utf-8").read()
aciklanmamis = sorted(k for k in kaldi_once
                      if k not in anilan and k not in rapor_metni)
vaka("M-04", "sadık sistemde kalan her vaka errata'da ya da raporda açıklanmış",
     not aciklanmamis,
     "%d vaka kaldı · açıklanmamış: %s"
     % (len(kaldi_once), aciklanmamis or "yok"))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
# Bu koruma on üçüncü turda eklendi ama YALNIZCA sonrasında yazılan
# takımlara; on beş takım korumasız kaldı. Geriye doldurma.
BEKLENEN_VAKA = 4


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("M-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))

    print("=" * 96)
    print("KÖR SINAMA M — errata ↔ sınama izlenebilirliği")
    print("=" * 96)
    kaldi = 0
    for kod, baslik, gecti, ayrinti in sonuclar:
        d, sinyal = beklenen.durum(kod, gecti)
        if sinyal:
            kaldi += 1
        print("%s %-6s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    print("-" * 96)
    _sinyal, _sayim = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _sayim["GEÇTİ"], _sayim["BEKLENEN"], _sinyal))
    if _sayim["BEKLENMEDİK GEÇİŞ"]:
        print("  %d BEKLENMEDİK GEÇİŞ — beyan bayat ya da sınama çürüdü"
              % _sayim["BEKLENMEDİK GEÇİŞ"])
    return kaldi


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
