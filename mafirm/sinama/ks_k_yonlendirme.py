#!/usr/bin/env python3
"""KÖR SINAMA K — yönlendirme, üst bilgi ve koltuk sağlaması.

Hiçbir kapı bu katmana bakmıyor. §9 şunu söylüyor:

    "Yönlendirme yalnızca açıklama alanını okur; dolayısıyla açıklama neyle
    ilgili olduğunu değil, NE ZAMAN devreye gireceğini yazmalıdır."

Bu ölçülebilir bir iddiadır. Ve §7'nin koltuk kuralı — "bir koltuk, o hukukçunun
gerçekten yazdığı, savunduğu ya da karara bağladığı şeye dayanır... Görüşü
bilinmiyorsa koltuk bunu yazar" — sistemin en yüksek itibar riskidir ve onu
uygulayan hiçbir mekanizma yok.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402  — beyan edilmiş taban (XFAIL mantığı)

# Kök dizin, betiğin KENDİ konumundan çözülür; sabit ~/mafirm değil.
# [Kör sınamanın kendi bulgusu] Betikler ~/mafirm'i sabitlediği sürece bir
# klon KENDİ ağacını değil, makinedeki kurulumu ölçer: klondaki kapi.py
# tamamen boşaltıldığında klonun denetimi hâlâ "DENETİM OK" diyordu. Bu, D
# takımının kitapta bulduğu kusurun aynısıdır — iddia ettiği şeye bakmayan
# bir kontrol. MAFIRM ortam değişkeniyle geçersiz kılınabilir.
_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))


M = _KOK_COZ
sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def ust_bilgi(yol):
    s = open(yol, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", s, re.S)
    if not m:
        return None, s
    alan = {}
    for satir in m.group(1).splitlines():
        if ":" in satir and not satir.startswith(" "):
            k, v = satir.split(":", 1)
            alan[k.strip()] = v.strip()
    return alan, s[m.end():]


# ===========================================================================
# 1 · Beceri üst bilgileri
# ===========================================================================
beceriler = {}
for d in sorted(os.listdir(os.path.join(M, ".claude/skills"))):
    yol = os.path.join(M, ".claude/skills", d, "SKILL.md")
    if not os.path.isfile(yol):
        continue
    alan, govde = ust_bilgi(yol)
    beceriler[d] = (alan, govde)

eksik = [d for d, (a, _) in beceriler.items() if not a]
vaka("K-01", "her becerinin YAML üst bilgisi var", not eksik,
     "eksik: %s" % eksik if eksik else "%d beceri" % len(beceriler))

adsiz = [d for d, (a, _) in beceriler.items() if a and "name" not in a]
vaka("K-02", "her beceride name alanı var", not adsiz, "eksik: %s" % adsiz)

uyusmaz = [d for d, (a, _) in beceriler.items()
           if a and a.get("name") and a["name"] != d]
vaka("K-03", "name alanı klasör adıyla eşleşiyor", not uyusmaz,
     "uyuşmayan: %s" % uyusmaz)

acsiz = [d for d, (a, _) in beceriler.items() if a and "description" not in a]
vaka("K-04", "her beceride description alanı var", not acsiz, "eksik: %s" % acsiz)

# ===========================================================================
# 2 · §9'un kendi kuralı: açıklama NE ZAMAN devreye gireceğini yazmalı
# ===========================================================================
TETIK = re.compile(r"(kullan\b|kullanıldığında|sorulduğunda|konduğunda|"
                   r"gerektiğinde|edilirken|yazılırken|ayrılırken|"
                   r"listelenip|çalıştırılırken|açılırken|önce\b|KULLANMA)", re.I)
tetiksiz = [d for d, (a, _) in beceriler.items()
            if a and not TETIK.search(a.get("description", ""))]
vaka("K-05", "her açıklama NE ZAMAN tetikleneceğini yazıyor", not tetiksiz,
     "tetik ifadesi yok: %s" % tetiksiz if tetiksiz
     else "%d/%d beceri" % (len(beceriler) - len(tetiksiz), len(beceriler)))

# Negatif sınır ("... için KULLANMA") kaç beceride var? Kitap yalnızca
# rekabet-esigi örneğinde gösteriyor; yanlış yönlendirmeyi asıl önleyen budur.
negatif = [d for d, (a, _) in beceriler.items()
           if a and re.search(r"KULLANMA|kullanma\b", a.get("description", ""))]
vaka("K-06", "açıklamalar negatif sınır taşıyor (>= yarısı)",
     len(negatif) * 2 >= len(beceriler),
     "%d/%d beceride negatif sınır var: %s"
     % (len(negatif), len(beceriler), negatif))


# ===========================================================================
# 3 · Yönlendirme ayırt ediciliği — açıklamalar birbirine karışıyor mu
# ===========================================================================
DURAK = set("""bir bu ve ya da ile için gibi olan olup ne zaman kullan
sorulduğunda gerektiğinde her hangi mi mı de den dan nin nın ın in
kapsar kullanılır olarak daha çok en var yok""".split())


def belirtec(s):
    return {w for w in re.findall(r"[a-zçğıöşüA-ZÇĞİÖŞÜ]{4,}", s.lower())
            if w not in DURAK}


ciftler = []
adlar = sorted(beceriler)
for i in range(len(adlar)):
    for j in range(i + 1, len(adlar)):
        a = belirtec(beceriler[adlar[i]][0].get("description", ""))
        b = belirtec(beceriler[adlar[j]][0].get("description", ""))
        if not a or not b:
            continue
        jac = len(a & b) / len(a | b)
        ciftler.append((jac, adlar[i], adlar[j], sorted(a & b)[:6]))
ciftler.sort(reverse=True)
en_yuksek = ciftler[0] if ciftler else (0, "", "", [])
vaka("K-07", "hiçbir beceri çifti yönlendirmede çakışmıyor (Jaccard < 0,25)",
     en_yuksek[0] < 0.25,
     "en yüksek çakışma %.2f — %s ↔ %s (ortak: %s)"
     % (en_yuksek[0], en_yuksek[1], en_yuksek[2], ", ".join(en_yuksek[3])))


# ===========================================================================
# 4 · Ajan ve komut üst bilgileri
# ===========================================================================
ajanlar = {}
for f in sorted(os.listdir(os.path.join(M, ".claude/agents"))):
    if f.endswith(".md"):
        ajanlar[f] = ust_bilgi(os.path.join(M, ".claude/agents", f))[0]
eksik_a = [f for f, a in ajanlar.items()
           if not a or not {"name", "description", "tools"} <= set(a)]
vaka("K-08", "her ajanda name + description + tools var", not eksik_a,
     "eksik: %s" % eksik_a if eksik_a else "%d ajan" % len(ajanlar))

komutlar = {}
for f in sorted(os.listdir(os.path.join(M, ".claude/commands"))):
    if f.endswith(".md"):
        komutlar[f] = ust_bilgi(os.path.join(M, ".claude/commands", f))[0]
eksik_k = [f for f, a in komutlar.items() if not a or "description" not in a]
vaka("K-09", "her komutta description var", not eksik_k,
     "eksik: %s" % eksik_k if eksik_k else "%d komut" % len(komutlar))


# ===========================================================================
# 5 · §7 koltuk sağlaması — sistemin en yüksek itibar riski
# ===========================================================================
koltuk_dizin = os.path.join(M, "birimler/_koltuklar")
koltuklar = {}
for f in sorted(os.listdir(koltuk_dizin)):
    if f.endswith(".md"):
        koltuklar[f] = open(os.path.join(koltuk_dizin, f), encoding="utf-8").read()

kaynaksiz = [f for f, s in koltuklar.items()
             if "Kaynak durumu" not in s and "KOLTUK BOŞ" not in s]
vaka("K-10", "her koltuk bir kaynak durumu beyanı taşıyor", not kaynaksiz,
     "beyansız: %s" % kaynaksiz if kaynaksiz else "%d koltuk" % len(koltuklar))

# §7: "Görüşü bilinmiyorsa koltuk bunu yazar."
kismi = [f for f, s in koltuklar.items() if "KISMEN BELGELENMİŞ" in s]
vaka("K-11", "belgelenmemiş koltuklar açıkça işaretli", len(kismi) >= 1,
     "kısmen belgelenmiş olarak işaretli: %s" % kismi)

# Uydurma alıntı taraması — ÜÇÜNCÜ SÜRÜM.
# Kör sınamanın kendi kusur kaydı:
#   1. sürüm: her tırnaklı diziyi alıntı saydı -> anılan ESER ADLARINI uydurma
#      söz diye işaretledi. Bir eser adını anmak §7'nin istediği dayanağın ta
#      kendisidir, ihlali değil.
#   2. sürüm: yakında bir söyleme fiili aradı -> "'<kitap>' kitabında ... yazdı"
#      cümlesi hâlâ eşleşti. Kitap yazmak, ağza söz koymak değildir.
#   Ayrıca her iki sürüm de tırnakları EŞLEŞTİRMİYORDU: açılış ve kapanış
#   tırnakları ayırt edilmediği için bir kapanıştan bir sonraki açılışa uzanan
#   hayalet aralıklar üretiliyordu.
# Bu sürüm: eşleşmiş tırnak çiftleri, ESER işaretçisi taşıyanlar dışlanır,
# ve yalnızca söyleme fiiliyle atfedilmiş olanlar sayılır.
CIFTLER = [("\u201c", "\u201d"), ("\u00ab", "\u00bb"), ('"', '"')]
ESER = re.compile(r"^[\s,]*(kitab|adlı|başlıklı|makale|eser|çerçeve)", re.I)
ATIF = re.compile(r"(dedi|diyor|demişti|savundu|belirtti|ifade etti|şöyle|"
                  r"sözleriyle|görüşüne göre|der ki)", re.I)
alinti, incelenen = [], 0
for f, s_ in koltuklar.items():
    for ac, kap in CIFTLER:
        desen = re.escape(ac) + "([^" + re.escape(ac + kap) + "]{25,})" + re.escape(kap)
        for m in re.finditer(desen, s_):
            incelenen += 1
            sonrasi = s_[m.end():m.end() + 40]
            if ESER.match(sonrasi):          # "<X>" kitabında / adlı ...
                continue
            if ATIF.search(s_[max(0, m.start() - 120):m.end() + 120]):
                alinti.append((f, m.group(1)[:46]))
vaka("K-12", "hiçbir koltukta kişiye ATFEDİLEN uydurma söz yok", not alinti,
     "bulunan: %s" % alinti if alinti
     else "temiz — %d tırnaklı dizi incelendi; eser adları ve sistem "
          "ifadeleri dışlandı, hiçbiri söyleme fiiliyle atfedilmedi" % incelenen)

# Her dolu koltuk kendi sınırını yazıyor mu (iki hukuk kuralı, CLAUDE.md §7)
sinirsiz = [f for f, s_ in koltuklar.items()
            if "KOLTUK BOŞ" not in s_ and "konuşmadığı yer" not in s_]
vaka("K-13", "her dolu koltuk kendi sınırını yazıyor", not sinirsiz,
     "sınırsız: %s" % sinirsiz if sinirsiz else "13/13 dolu koltuk")

# EN ÖNEMLİSİ: bunu uygulayan bir kapı var mı?
# Kaynak metnini grep'lemek yetmez — DAVRANIŞ sınanır. Beyansız bir koltuk
# dosyası gerçek kanca yolundan geçirilir; bloklanmalı. Beyanlı olan geçmeli.
import json
import subprocess
KAPI = os.path.join(M, ".claude/hooks/kapi.py")


def _kanca(icerik, yol):
    olay = {"tool_name": "Write",
            "tool_input": {"file_path": yol, "content": icerik}}
    r = subprocess.run([sys.executable, KAPI], input=json.dumps(olay),
                       capture_output=True, text=True)
    return r.returncode, (r.stderr or "").strip()

BEYANSIZ = ("# Leo E. Strine Jr.\n\n## Getirdiği mercek\n"
            "Hâkimin koltuğu: kayıt üç yıl sonra nasıl okunacak.\n")
BEYANLI = ("# Leo E. Strine Jr.\n\n## Kaynak durumu\nBelgelenmiş: yazdığı "
           "kararlar ve hakemli makaleler kamuya açıktır.\n\n"
           "## Getirdiği mercek\nHâkimin koltuğu.\n")

rc1, err1 = _kanca(BEYANSIZ, "birimler/_koltuklar/leo-strine.md")
rc2, _ = _kanca(BEYANLI, "birimler/_koltuklar/leo-strine.md")
vaka("K-14", "beyansız bir koltuk dosyası GERÇEKTEN bloklanıyor mu",
     rc1 == 2 and rc2 == 0,
     "beyansız -> çıkış %d (%s) · beyanlı -> çıkış %d"
     % (rc1, err1.split("]")[0][10:] if "]" in err1 else "geçti", rc2))

# Ve kapı yalnızca koltuk yollarında ateşlemeli — yöntem dosyasını bloklamamalı.
rc3, _ = _kanca("Beyansız bir yöntem dosyası. Doğrulama: 2026-08-27",
                "birimler/rekabet/yontem/x.md")
vaka("K-15", "koltuk kapısı yöntem dosyalarını bloklamıyor", rc3 == 0,
     "yöntem dosyası -> çıkış %d" % rc3)


def rapor():
    print("=" * 96)
    print("KÖR SINAMA K — yönlendirme, üst bilgi ve koltuk sağlaması")
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
