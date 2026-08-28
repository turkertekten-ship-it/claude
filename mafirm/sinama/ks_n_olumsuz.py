#!/usr/bin/env python3
"""KÖR SINAMA N — raporun OLUMSUZ İDDİALARININ kanıtı.

İşletim sözleşmesi §2, bu sistemdeki en sert kuraldır:

    "Böyle bir yükümlülük yok", "bildirim gerekmez", "bu düzenlemeye tabi
    değil" cümleleri kariyer bitirir. Olumsuz bir iddia, olumludan daha yüksek
    bir kanıt eşiği ister; çünkü okuyucu onu tek bir aramayla doğrulayamaz.
    Olumsuz iddia ancak o yükümlülüğü getirecek olan hükmü göstererek ve
    nereye bakıldığını söyleyerek yazılır.

Kural kitabın çıktısı için yazıldı. Ama bu RAPOR da bir çıktıdır ve o da
olumsuz iddialar taşıyor — en önemlisi: "hiçbir birincil kaynağa erişilemedi."

İlk dört tur boyunca bu iddia yalnızca İKİ ARAÇ HATASINA dayanıyordu. Yani
raporun kendisi, kitapta bulduğu kusurun aynısını yapıyordu: kanıtlanmamış bir
olumsuz iddiayı kanıtlanmış gibi sunmak. Bu takım o boşluğu ölçer ve kapatır.
"""
import json
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


kanit_md = os.path.join(_KOK_COZ, "hafiza", "egress-kaniti.md")
kanit_json = os.path.join(_KOK_COZ, "hafiza", "egress-kaniti.json")
rapor = open(os.path.join(_KOK_COZ, "RAPOR.md"), encoding="utf-8").read()

# --- N-01: rapor gerçekten bir olumsuz iddia taşıyor mu -------------------
OLUMSUZ = re.compile(r"(hiçbir birincil kaynağa erişilemedi|erişilemedi|"
                     r"ulaşamamıştı)", re.I)
vaka("N-01", "rapor bir olumsuz iddia taşıyor (kural 2 devreye girer)",
     bool(OLUMSUZ.search(rapor)),
     "bulunan: %s" % (OLUMSUZ.search(rapor).group(0) if OLUMSUZ.search(rapor)
                      else "yok"))

# --- N-02: iddianın MAKİNECE KAYDEDİLMİŞ kanıtı var mı -------------------
var = os.path.exists(kanit_json)
kayit = json.load(open(kanit_json, encoding="utf-8")) if var else {}
retler = kayit.get("reddedilen", [])
vaka("N-02", "olumsuz iddia makinece kaydedilmiş kanıta dayanıyor",
     var and len(retler) >= 4,
     "vekilin kendi kaydında %d ret; araç hatası değil, bağımsız kayıt"
     % len(retler))

# --- N-03: kanıt HANGİ HOST'ları ve HANGİ MEKANİZMAYI adlandırıyor -------
hostlar = {r.get("host", "").split(":")[0] for r in retler}
gerekli = {"www.mevzuat.gov.tr", "www.rekabet.gov.tr",
           "www.resmigazete.gov.tr", "www.spk.gov.tr"}
mekanizma = all("403" in r.get("detail", "") for r in retler) if retler else False
vaka("N-03", "kanıt host'ları ve ret mekanizmasını adlandırıyor",
     gerekli <= hostlar and mekanizma,
     "host: %d/%d · hepsi CONNECT 403: %s" % (len(gerekli & hostlar),
                                              len(gerekli), mekanizma))

# --- N-04: "nereye bakıldığı" yazılmış mı (kural 2'nin ikinci şartı) -----
kmd = open(kanit_md, encoding="utf-8").read() if os.path.exists(kanit_md) else ""
kanallar = ["WebFetch", "curl", "WebSearch", "__agentproxy/status"]
eksik_kanal = [k for k in kanallar if k not in kmd]
vaka("N-04", "kanıt hangi kanalların denendiğini tek tek yazıyor",
     not eksik_kanal, "eksik kanal: %s" % (eksik_kanal or "yok"))

# --- N-05: yükümlülüğü getiren HÜKÜM gösterilmiş mi ---------------------
vaka("N-05", "reddin anlamını tanımlayan hüküm alıntılanmış",
     "egress policy" in kmd and "README" in kmd,
     "ortamın kendi belgesi alıntılanıyor: 403 = kuruluş politikası reddi")

# --- N-06: ÇALIŞAN kanal da dürüstçe yazılmış mı ------------------------
# En kolay kaçamak: "hiçbir şey çalışmadı" demek. WebSearch ÇALIŞIYOR.
vaka("N-06", "çalışan kanal da yazılmış (kaçamak yok)",
     "WebSearch" in kmd and ("çalışıyor" in kmd or "ÇALIŞMAKTADIR" in kmd),
     "WebSearch çalışıyor ve kullanıldı; döndürdüğü şey sayfa metni değil")

# --- N-07: iddia FAZLA GENİŞ yazılmamış mı ------------------------------
# "Hiçbir kaynağa erişilemedi" yanlış olurdu: GitHub MCP çalıştı, 16 depo
# çözüldü. İddia belirli alan adlarıyla sınırlanmalı.
vaka("N-07", "iddia belirli alan adlarıyla sınırlı, genel değil",
     "alan adlarına" in kmd or "alan adları" in kmd,
     "GitHub MCP ile 16 depo çözüldü — 'hiçbir şeye erişilemedi' YANLIŞ olurdu")

# --- N-08: kanıt, bulguları ÇÖZDÜĞÜNÜ iddia etmiyor ---------------------
vaka("N-08", "kanıt, üç mevzuat bulgusunu çözdüğünü İDDİA ETMİYOR",
     "ÇÖZMÜYOR" in kmd or "çözmüyor" in kmd,
     "erişimin neden yok olduğunu kanıtlamak, bulguyu kapatmaz")


def rapor_yaz():
    print("=" * 96)
    print("KÖR SINAMA N — raporun olumsuz iddialarının kanıtı (CLAUDE.md §2)")
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
    sys.exit(min(rapor_yaz(), 120))
