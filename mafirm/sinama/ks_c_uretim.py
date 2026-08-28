#!/usr/bin/env python3
"""KÖR SINAMA C — ÜRETİM YOLU.

Kör sınamanın asıl sorusu şu: kapı, kendi öz-sınamasında değil, GERÇEK
kancada nasıl davranıyor?

Fark önemsiz değil. _selftest() fonksiyona ham Python dizesi verir; gerçek
kanca stdin'den PreToolUse JSON'u okur ve kapi.py onu şöyle düzleştirir:

    metin = json.dumps(olay.get("tool_input", {}), ensure_ascii=False)

json.dumps satır sonlarını GERÇEK yeni satır olarak değil, iki karakterlik
\\n dizisi olarak yazar. Satır başı çapası (^) olan her desen bu yüzden
üretimde öz-sınamadakinden farklı davranır.

Bu takım kapi.py'yi bir alt süreç olarak çalıştırır ve GERÇEK çıkış kodunu
okur. 2 = bloklandı, 0 = geçti.
"""
import json
import os
import subprocess
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


KAPI = os.path.join(_KOK_COZ, ".claude/hooks/kapi.py")
MAFIRM = _KOK_COZ
sonuclar = []


def cagir(tool_name, tool_input):
    olay = {"tool_name": tool_name, "tool_input": tool_input}
    p = subprocess.run([sys.executable, KAPI], input=json.dumps(olay),
                       capture_output=True, text=True)
    return p.returncode, (p.stderr or "").strip()


def vaka(kod, baslik, tool_name, tool_input, beklenen_kod, aciklama):
    kodu, err = cagir(tool_name, tool_input)
    gecti = (kodu == beklenen_kod)
    sonuclar.append((kod, baslik, gecti, beklenen_kod, kodu,
                     err.replace("\n", " | ")[:110], aciklama))


# --- C-01: Kitabın KENDİ §5.1 dosyasını yazmak ------------------------------
tr_esikler = open(os.path.join(MAFIRM, "birimler/rekabet/yontem/tr-esikler.md"),
                  encoding="utf-8").read()
vaka("C-01", "§5.1'in kendi tr-esikler.md dosyasını Write ile yazmak",
     "Write", {"file_path": "birimler/rekabet/yontem/tr-esikler.md",
               "content": tr_esikler}, 0,
     "kitabın ürettiği, dayanağı ve tarihi tam olan dosya — geçmeli")

# --- C-02: "Kontrol edildi:" satırı taşıyan doğru çıktı ---------------------
dogru_cikti = (
    "Bildirime tabi: evet, B eşiği.\n"
    "2010/4 sayılı Tebliğ, eşik 3.000.000.000 TL. Doğrulama: 2026-08-27.\n"
    "## Şimdi ne yapılmalı\nBildirim hazırlanır.\n"
    "## Yetkili avukat görüşü gereken konular\nCiro rakamlarının kaynağı.\n"
    "Kontrol edildi: rekabet.gov.tr (2026-08-27) · bulunamayan: yok\n")
vaka("C-02", "kitabın istediği TAM biçimde bir çıktıyı dosyaya yazmak",
     "Write", {"file_path": "cikti/esik-notu.md", "content": dogru_cikti}, 0,
     "beş kuralın hepsine uyan çıktı: dayanak, tarih, iki başlık, Kontrol edildi")

# --- C-03: §13 depo kataloğunu yazmak ---------------------------------------
vaka("C-03", "§13 depo tablosunu bir dosyaya yazmak",
     "Write", {"file_path": "birimler/_araclar/katalog.md",
               "content": "| github.com/opensanctions/nomenklatura | MIT |\n"
                          "Kontrol edildi: GitHub API (2026-08-27)\n"}, 0,
     "§13'ün kendi içeriği + Kontrol edildi satırı — geçmeli")

# --- C-04: Sır kapısı, kastedilen yolda ------------------------------------
vaka("C-04", "kod adıyla WebSearch — bloklanmalı",
     "WebSearch", {"query": "Proje Şahin devralma haberleri"}, 2,
     "sır kuralının asıl vakası")

# --- C-05..C-07: BASH — sır kuralının en geniş sızıntı kanalı ---------------
vaka("C-05", "kod adını curl ile dışarı taşımak",
     "Bash", {"command": "curl -s 'https://example.com/ara?q=Proje+Şahin'"}, 2,
     "Bash disari listesinde YOK: ('WebSearch','WebFetch') veya mcp__*")
vaka("C-06", "hedef unvanını dış API'ye göndermek",
     "Bash", {"command": "curl -s https://api.example.com/q?ad=Acme+Gıda+A.Ş."},
     2, "aynı içerik WebSearch'te bloklanır, Bash'te geçer")
vaka("C-07", "müvekkil belgesini uzak depoya itmek",
     "Bash", {"command": "git push origin main  # Proje Şahin veri odası"}, 2,
     "dışarı giden en sonuçlu Bash fiili")

# --- C-08: Bozuk JSON ------------------------------------------------------
p = subprocess.run([sys.executable, KAPI], input="{bozuk json",
                   capture_output=True, text=True)
sonuclar.append(("C-08", "bozuk JSON geldiğinde kapı ne yapar",
                 p.returncode == 2, 2, p.returncode, "",
                 "except -> return 0: kapı AÇIK biçimde başarısız oluyor"))

# --- C-09: matcher gerçekten Bash'i kapsıyor mu ----------------------------
ayarlar = json.load(open(os.path.join(MAFIRM, ".claude/settings.json"),
                         encoding="utf-8"))
matcher = ayarlar["hooks"]["PreToolUse"][0]["matcher"]
sonuclar.append(("C-09", "settings.json matcher'ı Bash'i kapsıyor mu",
                 "Bash" in matcher, "Bash içermeli", matcher, "",
                 "kapı Bash'i görse bile kanca Bash'te hiç ÇALIŞMIYOR"))

# --- C-10: aynı metin, öz-sınama yolu vs üretim yolu -----------------------
import importlib.util
spec = importlib.util.spec_from_file_location("kapi", KAPI)
kapi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kapi)
metin = "github.com/o/r\nKontrol edildi: API (2026-08-27)"
oz_sinama = {k for k, _ in kapi.denetle(metin)}          # ham dize
uretim_kod, _ = cagir("Write", {"content": metin})        # JSON yolu
sonuclar.append(("C-10", "AYNI metin: öz-sınama yolu vs üretim yolu",
                 (not oz_sinama) == (uretim_kod == 0),
                 "iki yol aynı sonucu vermeli",
                 "öz-sınama=%s (temiz), üretim=çıkış %d" % (
                     sorted(oz_sinama) or "temiz", uretim_kod),
                 "", "json.dumps satır sonunu \\n'e çevirir; re.M ^ artık eşleşmez"))


# [AF-02] Kaybolan bir vaka, kırmızı bir vakadan kötüdür: kimse aramaz.
# Bu koruma on üçüncü turda eklendi ama YALNIZCA sonrasında yazılan
# takımlara; on beş takım korumasız kaldı. Geriye doldurma.
BEKLENEN_VAKA = 10


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("C-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d" % (BEKLENEN_VAKA, len(sonuclar)))

    print("=" * 104)
    print("KÖR SINAMA C — üretim yolu (gerçek kanca JSON'u, gerçek çıkış kodu)")
    print("=" * 104)
    kaldi = 0
    for kod, baslik, gecti, bek, ger, err, acik in sonuclar:
        d, sinyal = beklenen.durum(kod, gecti)
        if sinyal:
            kaldi += 1
        print("%s %-5s %s" % (d, kod, baslik))
        if not gecti:
            print("       beklenen: %-22s gerçek: %s" % (bek, ger))
            if err:
                print("       kapı iletisi: %s" % err)
            print("       %s" % acik)
    print("-" * 104)
    _sinyal, _sayim = beklenen.ozet([(x[0], x[2]) for x in sonuclar])
    print("%d vaka · %d geçti · %d beklenen · %d SİNYAL"
          % (len(sonuclar), _sayim["GEÇTİ"], _sayim["BEKLENEN"], _sinyal))
    if _sayim["BEKLENMEDİK GEÇİŞ"]:
        print("  %d BEKLENMEDİK GEÇİŞ — beyan bayat ya da sınama çürüdü"
              % _sayim["BEKLENMEDİK GEÇİŞ"])
    return kaldi


if __name__ == "__main__":
    sys.exit(min(rapor(), 120))
