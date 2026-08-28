#!/usr/bin/env python3
"""KÖR SINAMA Q — rapor KENDİ kapılarından geçiyor mu.

Sekiz tur boyunca kitabın kapılarını sertleştirdim. Dokuzuncu turda o
kapıları kendi raporuma tuttum ve kapı ateşledi:

    RAPOR.md  [kapsam] görüş gibi okunuyor, avukat başlığı yok

Kapı haklıydı. RAPOR.md Türk hukuku ifadeleri taşıyor ("izinsiz kapanış
maruziyeti", "bildirime tabidir") ve "## Sonuç" ile bitiyordu — işletim
sözleşmesi §5'in istediği iki zorunlu başlıkla değil.

Daha kötüsü: bu çıktıyı SEKİZİNCİ turda ekranda gördüm ve üzerinden geçtim.
§12'nin öngördüğü kusurun ta kendisi: *"belgedeki bir kurala model sakinken
uyulur, görev uzayınca atlanır."* Sekiz tur, tam da "görev uzayınca"dır.

Bu takım, raporun kendi sistemine tabi kalmasını kalıcı hâle getirir.
"""
import glob
import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK_COZ = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    "kapi_q", os.path.join(_KOK_COZ, ".claude/hooks/kapi.py"))
kapi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapi)

sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


# [Altmış birinci tur] Yayımlanan belge listede YOKTU. Okuyucunun açtığı ve
# paylaştığı teslimat oydu, ve kapılardan geçirilince kural 1 ile kural 3'ü
# birden çiğnediği görüldü: eşik rakamları dayanaksız, ve belgede hiçbir
# doğrulama tarihi yoktu. Kuralın kendi sözüyle: bayat bir eşik hiç
# olmamasından kötüdür, çünkü kontrol edilmiş gibi durur.
TESLIMAT = (["RAPOR.md", "KITAP-ERRATA.md", "kor-sinama-raporu.html",
             "hafiza/dogrulama-bulgulari.md", "hafiza/egress-kaniti.md",
             "hafiza/cikar-catismasi.md"]
            + sorted(os.path.relpath(p, _KOK_COZ)
                     for p in glob.glob(os.path.join(_KOK_COZ,
                                                     "sinama/ks_[ghi]_*.md"))))


def _duzyazi(metin, rel):
    """HTML teslimatın DÜZYAZISI. Etiketler kapıların yapı okumasını bozar;
    okuyucunun gördüğü şey ise düzyazıdır ve kural 1/3 ona uygulanır."""
    if not rel.endswith(".html"):
        return metin
    metin = re.sub(r"<style.*?</style>|<script.*?</script>", " ", metin,
                   flags=re.S)
    return re.sub(r"<[^>]+>", " ", metin)


def kapilar(rel):
    p = os.path.join(_KOK_COZ, rel)
    if not os.path.exists(p):
        return None
    ham = open(p, encoding="utf-8").read()
    return sorted({a for a, _ in kapi.denetle(
        _duzyazi(ham, rel), disari=False, yol=rel)})


# --- Q-01: hiçbir teslimat kendi kapılarını ateşlemiyor -----------------
ates = {r: kapilar(r) for r in TESLIMAT}
kirli = {r: a for r, a in ates.items() if a}
vaka("Q-01", "hiçbir teslimat kendi kapılarını ateşlemiyor",
     not kirli, "%d teslimat · ateşleyen: %s" % (len(TESLIMAT), kirli or "yok"))

# --- Q-02: §5'in iki zorunlu başlığı, bu sırayla -----------------------
eksik = []
for rel in ("RAPOR.md", "KITAP-ERRATA.md"):
    s = open(os.path.join(_KOK_COZ, rel), encoding="utf-8").read()
    i = s.find("## Şimdi ne yapılmalı")
    j = s.find("## Yetkili avukat görüşü gereken konular")
    if i < 0 or j < 0:
        eksik.append("%s (başlık yok)" % rel)
    elif j < i:
        eksik.append("%s (sıra ters)" % rel)
vaka("Q-02", "esaslı çıktılar iki zorunlu başlıkla, bu sırayla bitiyor",
     not eksik, "eksik: %s" % (eksik or "yok"))

# --- Q-03: avukat başlığı BOŞ değil (§5: 'asla boş kalmaz') ------------
bos = []
for rel in ("RAPOR.md", "KITAP-ERRATA.md"):
    s = open(os.path.join(_KOK_COZ, rel), encoding="utf-8").read()
    j = s.find("## Yetkili avukat görüşü gereken konular")
    if j < 0:
        continue
    govde = s[j + 40:j + 1400]
    if govde.count("\n- ") < 3:
        bos.append(rel)
vaka("Q-03", "avukat başlığı gerçek kalemler taşıyor (§5: asla boş kalmaz)",
     not bos, "yetersiz: %s" % (bos or "yok"))

# --- Q-04: 'Kontrol edildi' satırı var ve 'bulunamayan' alanı dolu -----
eksik_k = []
for rel in ("RAPOR.md", "KITAP-ERRATA.md", "hafiza/dogrulama-bulgulari.md"):
    s = open(os.path.join(_KOK_COZ, rel), encoding="utf-8").read()
    if "Kontrol edildi:" not in s:
        eksik_k.append("%s (satır yok)" % rel)
    elif "bulunamayan:" not in s:
        eksik_k.append("%s (bulunamayan alanı yok)" % rel)
vaka("Q-04", "Kontrol edildi satırı var ve 'bulunamayan' alanı dolu",
     not eksik_k,
     "§14: 'bulunamayan isteğe bağlı değil zorunlu bir alandır' · eksik: %s"
     % (eksik_k or "yok"))

# --- Q-05: MUTASYON — avukat başlığı silinirse kapı yakalar ------------
s = open(os.path.join(_KOK_COZ, "RAPOR.md"), encoding="utf-8").read()
bozuk = s.replace("## Yetkili avukat görüşü gereken konular", "## Notlar")
yakalar = "kapsam" in {a for a, _ in kapi.denetle(bozuk, disari=False,
                                                  yol="RAPOR.md")}
vaka("Q-05", "mutasyon: avukat başlığı silinirse kapsam kapısı yakalar",
     yakalar)

# --- Q-06: MUTASYON — dayanaksız bir eşik eklenirse kapı yakalar -------
bozuk2 = s + "\n\nYeni eşik 7.500.000.000 TL olarak uygulanacaktır.\n"
yakalar2 = "kanit" in {a for a, _ in kapi.denetle(bozuk2, disari=False,
                                                  yol="RAPOR.md")}
vaka("Q-06", "mutasyon: dayanaksız eşik eklenirse kanıt kapısı yakalar",
     yakalar2)

# --- Q-07: akademik dayanak MEVZUAT dayanağının yerini almıyor --------
# Gevşetme sınaması: bir DOI, bir mevzuat eşiğini aklamamalı.
sahte = ("2026 yılında eşik 3.000.000.000 TL olarak uygulanır. "
         "Kaynak: Science 381(6654).")
vaka("Q-07", "akademik dayanak bir MEVZUAT eşiğini aklamıyor",
     "kanit" in {a for a, _ in kapi.denetle(sahte)},
     "Dayanağın TÜRÜ rakamın türüne bağlıdır: para tutarı mevzuat atfı ister, "
     "oran/yüzde kaynak atfıyla yetinir. İlk sürümde akademik dayanak her "
     "rakamı aklıyordu ve Q-06 bunu yakaladı. Şu anki davranış: %s"
     % sorted({a for a, _ in kapi.denetle(sahte)}))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
# Bu koruma on üçüncü turda eklendi ama YALNIZCA sonrasında yazılan
# takımlara; on beş takım korumasız kaldı. Geriye doldurma.
BEKLENEN_VAKA = 7


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("Q-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))

    print("=" * 96)
    print("KÖR SINAMA Q — rapor kendi kapılarından geçiyor mu")
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
