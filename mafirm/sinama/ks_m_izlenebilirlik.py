#!/usr/bin/env python3
"""KÖR SINAMA M — errata ↔ sınama izlenebilirliği.

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
                ar = re.match(r"^([A-Z])-(\d+)\s*(?:…|\.\.\.|\.\.)\s*(?:[A-Z]-)?(\d+)$", p)
                if ar:
                    h, b1, b2 = ar.group(1), int(ar.group(2)), int(ar.group(3))
                    kimlikler += ["%s-%02d" % (h, n) for n in range(b1, b2 + 1)]
                elif re.match(r"^[A-Z](-\d+[a-z]?)?$", p):
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
    for k in re.findall(r'"([A-Z]-\d+[a-z]?)"', icerik):
        tanimli.add(k); takimlar.add(k[0])
    for kok_id, sonek in re.findall(r'"([A-Z]-\d+)%s"\s*%\s*(\w+)', icerik):
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
    kaldi_once = set(re.findall(r"^KALDI\s+([A-Z]-\d+[a-z]?)", 
                                open(once, encoding="utf-8").read(), re.M))
agir = [(b, k) for b, a, k in maddeler if a in ("A", "B") and k]
sinanmamis = []
for b, kimlikler in agir:
    somut = [k for k in kimlikler if len(k) > 1 and k[0] in "ABCE"]
    if somut and not any(k in kaldi_once for k in somut):
        sinanmamis.append((b[:44], somut))
vaka("M-03", "[A] ve [B] maddelerinin atıfları sadık sistemde gerçekten kaldı",
     not sinanmamis,
     "sadık koşumda kalan vaka: %d · sınanmamış ağır madde: %s"
     % (len(kaldi_once), sinanmamis or "yok"))

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


def rapor():
    print("=" * 96)
    print("KÖR SINAMA M — errata ↔ sınama izlenebilirliği")
    print("=" * 96)
    kaldi = 0
    for kod, baslik, gecti, ayrinti in sonuclar:
        d = "GEÇTİ" if gecti else "KALDI"
        if not gecti:
            kaldi += 1
        print("%s %-6s %s" % (d, kod, baslik))
        if ayrinti:
            print("        %s" % ayrinti)
    print("-" * 96)
    print("%d vaka, %d geçti, %d KALDI" % (len(sonuclar),
                                           len(sonuclar) - kaldi, kaldi))
    return kaldi


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
