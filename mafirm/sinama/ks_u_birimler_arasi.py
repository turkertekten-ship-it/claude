#!/usr/bin/env python3
"""KÖR SINAMA U — birimler birbiriyle çelişiyor mu.

§4 birim yapısının gerekçesini kendisi yazar: birimler AYNI YAPIYI paylaşır,
böylece biri okunduğunda hepsi okunabilir. Kitabın denetimi bu yapıyı sayar:
INDEX var mı, yontem/ dolu mu, üst bilgi yerinde mi. Hepsi YAPISAL.

Hiçbir yerde bir birimin SÖYLEDİĞİ ile başka bir birimin söylediği
karşılaştırılmaz. İki birim aynı hukuki işlemi farklı sıraya koyabilir ve
kitabın denetimi yeşil kalır. On iki tur boyunca ben de bunu sınamadım:
§6 ve §8 içeriği yalnızca referans bütünlüğü için okundu.

Bu takım içeriği okur. Kaynağı kitabın DÜZYAZISIdır, kodu değil.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

import importlib.util as _ilu  # noqa: E402
_sp_k = _ilu.spec_from_file_location(
    "kapi_u09", os.path.join(KOK, ".claude/hooks/kapi.py"))
_kapi_u09 = _ilu.module_from_spec(_sp_k)
_sp_k.loader.exec_module(_kapi_u09)
_tr = _kapi_u09.tr_kucult

sonuclar = []


def vaka(kod, baslik, gecti, ayrinti=""):
    sonuclar.append((kod, baslik, gecti, ayrinti))


def oku(rel):
    p = os.path.join(KOK, rel)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def bolum(metin, basligin_parcasi):
    """'## ...parça...' başlığından bir sonraki '##'ye kadar olan gövde."""
    d = re.split(r"^## ", metin, flags=re.M)
    for b in d[1:]:
        if basligin_parcasi.lower() in b.split("\n", 1)[0].lower():
            return b
    return ""


def numarali(gövde):
    """Gerçek numaralı LİSTE — 1'den başlayıp artan en uzun bitişik dizi.

    İlk sürüm her '^\\d+\\.' satırını madde saydı. Düzyazıda geçen
    "1. adımda hiçbir zaman doğrulanamaz" cümlesi de satır başına düştüğü
    için madde sanıldı ve listenin indisleri kaydı — yani metin
    DÜZELTİLDİKTEN sonra sınama bozuldu. Metni sınamaya uydurmak yanlış
    olurdu; okuduğunu iddia ettiği şeyi okuyan ayrıştırıcı budur.
    """
    satirlar = gövde.split("\n")
    diziler, simdiki, bekle = [], [], 1
    for i, sat in enumerate(satirlar):
        m = re.match(r"\s*(\d+)\.\s+(.*)", sat)
        if m and int(m.group(1)) == bekle:
            simdiki.append([i, m.group(2)])
            bekle += 1
        elif m and int(m.group(1)) == 1:
            if len(simdiki) > 1:
                diziler.append(simdiki)
            simdiki, bekle = [[i, m.group(2)]], 2
        elif simdiki and sat.strip() and sat.startswith((" ", "\t")):
            simdiki[-1][1] += " " + sat.strip()       # sarkan satır
        elif not sat.strip():
            continue
        else:
            if len(simdiki) > 1:
                diziler.append(simdiki)
            simdiki, bekle = [], 1
    if len(simdiki) > 1:
        diziler.append(simdiki)
    if not diziler:
        return []
    en_uzun = max(diziler, key=len)
    return [re.sub(r"\s+", " ", t).strip() for _, t in en_uzun]


def bas(oge):
    """Maddenin ADLANDIRDIĞI işlem — açıklamasından önceki kısım.

    "Kapanış öncesi koşulların karşılandığının teyidi — izin yazısı elde,
    yetkilendirici organ kararları alınmış" maddesi bir TEYİTTİR; içindeki
    "organ kararları" o adımda YAPILAN iş değil, teyit edilen koşuldur.
    Kıyas işlem adı üzerinden yapılır."""
    return re.split(r"\s+[—–]\s+|\s+-\s+|\s*\(", oge)[0].strip()


TUM = {}
for kok, _d, dosyalar in os.walk(KOK):
    if "/.git" in kok or "/sinama" in kok or "/yamalar" in kok:
        continue
    for ad in dosyalar:
        if ad.endswith(".md"):
            yol = os.path.relpath(os.path.join(kok, ad), KOK)
            if yol.split("/")[0] in ("birimler", ".claude", "komutlar"):
                TUM[yol] = open(os.path.join(kok, ad), encoding="utf-8").read()


# --- U-01 · kapanış öncesi koşul sırası iki yerde aynı mı --------------
mimari = numarali(bolum(oku("birimler/sinir-otesi/yontem/mimari.md"),
                        "Kapanış öncesi koşullar"))
takip = numarali(bolum(oku(".claude/skills/kosul-takibi/SKILL.md"), "Sıra"))
ANAHTAR = [("rekabet",), ("sektör", "düzenleyici"), ("yabancı", "millî"),
           ("üçüncü", "kontrol değişikliği"), ("organ", "genel kurul")]


def sirali_ortusme(a, b):
    if len(a) != len(b):
        return False, "madde sayısı %d vs %d" % (len(a), len(b))
    for i, kelimeler in enumerate(ANAHTAR[:len(a)]):
        ax, bx = a[i].lower(), b[i].lower()
        if not any(k in ax for k in kelimeler) or not any(k in bx for k in kelimeler):
            return False, "%d. madde ayrışıyor" % (i + 1)
    return True, "%d madde, aynı sırada" % len(a)


ok, not_ = sirali_ortusme(mimari, takip)
vaka("U-01", "kapanış öncesi koşul sırası mimari.md ≡ kosul-takibi", ok, not_)

# --- U-02 · bir koşul öncesi, aynı anda kapanış GÜNÜ adımı olamaz ------
gun = numarali(bolum(oku(".claude/skills/kapanis-listesi/SKILL.md"),
                     "Kapanış günü sırası"))
onkosul_metni = " ".join(bas(x) for x in mimari + takip).lower()
gun_metni = " ".join(bas(x) for x in gun).lower()
cakisan = []
for etiket, kelimeler in (("organ kararları", ("organ karar",)),
                          ("genel kurul onayı", ("genel kurul",))):
    if any(k in onkosul_metni for k in kelimeler) and \
       any(k in gun_metni for k in kelimeler):
        cakisan.append(etiket)
vaka("U-02", "kapanış öncesi koşul listesi ile kapanış günü sırası ayrık", not cakisan,
     ("İKİ LİSTEDE BİRDEN: %s. Kapanış günü 1. adımı 'koşulların "
      "karşılandığının teyidi'dir; koşul sayılan bir işlem 2. adımda "
      "YAPILAMAZ — 1. adım hiçbir zaman doğrulanamaz." % ", ".join(cakisan))
     if cakisan else "çakışma yok")

# --- U-03 · TTK 595 sırası: noter mi önce, organ kararı mı -------------
pd = oku("birimler/tr-sirketler/yontem/pay-devri.md")
noter_kurucu = ("595/1" in pd and "noter" in pd.lower()
                and "595/2" in pd.lower() and "kurucu" in pd.lower()
                and pd.lower().index("595/1") < pd.lower().index("595/2"))
# BOŞA GEÇMEZ: aradığı iki adımdan biri yoksa vaka BAŞARISIZ olur, çünkü
# kapanış günü sırasının 595/1 ve 595/2'yi ADLANDIRMASI gerekir. İlk sürüm
# StopIteration'ı "çakışma yok" sayıp sessizce yeşile döndü — kitabın
# hep-yeşil denetiminin aynadaki hâli, kendi takımımda.
def _indis(liste, *kelimeler):
    for i, m in enumerate(liste):
        d = m.lower()
        if all(k in d for k in kelimeler):
            return i
    return None


i_noter = _indis(gun, "noter")
i_gk = _indis(gun, "595/2")
if not noter_kurucu:
    gecti_03, ayr = False, "pay-devri.md 595/1→595/2 sırasını kurmuyor"
elif i_noter is None or i_gk is None:
    gecti_03 = False
    ayr = ("kapanış günü sırası %s adımını adlandırmıyor — pay-devri.md "
           "şekli kurucu sayıyor, sıra onu göstermek zorunda"
           % ("noter" if i_noter is None else "TTK m.595/2 genel kurul onayı"))
else:
    gecti_03 = i_noter < i_gk
    ayr = ("pay-devri.md: 595/1 noter → 595/2 genel kurul (kurucu). "
           "kapanis-listesi: %d. noter → %d. genel kurul onayı.%s"
           % (i_noter + 1, i_gk + 1, "" if gecti_03 else " TERS."))
vaka("U-03", "TTK m.595 sırası pay-devri.md ≡ kapanis-listesi",
     gecti_03, ayr)

# --- U-04 · aynı mevzuat atfı iki dosyada aynı önermeye bağlı mı ------
ATIF = re.compile(r"TTK m\.(\d{3}(?:/\d)?)")
DURAK = set("""bir bu şu ve ile için olan olarak ancak ise da de ki mi mı
              gibi göre kadar sonra önce her hiç en çok az var yok""".split())


def anlamli(c):
    """Türkçe eklemeli bir dildir: 'defterine', 'Defterin' ve 'defteri' aynı
    önermeyi taşır ama tam kelime olarak eşleşmez. İlk beş harf kaba bir
    gövdedir ve bu kıyas için yeterlidir. (Bu satır, ilk sürümün dört yanlış
    pozitif üretmesinden sonra yazıldı.)"""
    return {k[:5] for k in re.findall(r"[a-zçğıöşüA-ZÇĞİÖŞÜ]{4,}", c.lower())
            if k not in DURAK}


def pencereler(m):
    """Bir ÖNERMENİN doğal birimi cümledir.

    İki yanlış granülden sonra: (1) satır — sarılmış markdown'da atıf satır
    başına düşünce önermesi bir önceki satırda kalıyordu; (2) paragraf —
    yoğun numaralı bloklarda (çeviri kuralları gibi) atıfın çevresine iki
    yüz karakter ilgisiz metin topluyordu. Cümle ikisinin arasıdır ve
    kıyaslanan şeyin kendisidir."""
    duz = re.sub(r"\s+", " ", m)
    for c in re.split(r"(?<=[.;:])\s+(?=[A-ZÇĞİÖŞÜ0-9*`\-])|\s+\|\s+", duz):
        c = c.strip()
        if c:
            yield c


yerler = {}
for yol, m in TUM.items():
    for pen in pencereler(m):
        for a in set(ATIF.findall(pen)):
            yerler.setdefault(a, []).append((yol, pen))
# Ölçüt: bir hükmün, AYNI hükmün başka HİÇBİR anımıyla tek bir içerik
# kelimesi paylaşmayan anımı. Kesişimi "hepsinde ortak" diye aramak yanlıştı:
# listedeki çıplak bir işaretçi ("pay defterine kayıt (TTK m.499)") bir önerme
# taşımaz, dolayısıyla hiçbir şeyle çelişemez ama kesişimi sıfıra düşürür.
# Sıfır örtüşme ayrık bir önermedir ve bir insan tarafından okunmalıdır.
ayrisan = []
for a, kayitlar in sorted(yerler.items()):
    if len({y for y, _ in kayitlar}) < 2:
        continue
    kumeler = [(y, anlamli(c)) for y, c in kayitlar]
    for i, (yol, kume) in enumerate(kumeler):
        digerleri = set().union(*[k for j, (_, k) in enumerate(kumeler)
                                  if j != i]) if len(kumeler) > 1 else set()
        if kume and not (kume & digerleri):
            ayrisan.append("m.%s · %s ile ayrık" % (a, yol))

vaka("U-05", "aynı hükmün her anımı aynı önermeyi taşıyor",
     not ayrisan,
     "; ".join(sorted(set(ayrisan))) if ayrisan
     else "%d hüküm birden çok dosyada anılıyor, hiçbir anım ayrık değil"
          % sum(1 for a in yerler if len({y for y, _ in yerler[a]}) > 1))

# --- U-06 · aynı rakam iki dosyada farklı anlamda kullanılıyor mu -----
RAKAM = re.compile(r"(?<![\d.,])(\d{1,3}(?:\.\d{3}){2,})(?![\d.,])")
rakam_yerleri = {}
for yol, m in TUM.items():
    for satir in m.split("\n"):
        for r in RAKAM.findall(satir):
            rakam_yerleri.setdefault(r, []).append((yol, satir))
coklu = {r: k for r, k in rakam_yerleri.items()
         if len({y for y, _ in k}) > 1}
catisan = []
for r, kayitlar in sorted(coklu.items()):
    kumeler = [anlamli(s) for _, s in kayitlar]
    if len(set.intersection(*kumeler)) < 2:
        catisan.append("%s (%d dosya)" % (r, len({y for y, _ in kayitlar})))
vaka("U-06", "eşik rakamları tek kaynaklı ya da anlamı örtüşüyor",
     not catisan,
     "; ".join(catisan) if catisan
     else "%d büyük rakam; birden çok dosyada geçen: %d"
          % (len(rakam_yerleri), len(coklu)))

# --- U-07 · KULLANMA yönlendirmesi var olan bir beceriyi gösteriyor mu -
beceriler = {os.path.basename(os.path.dirname(p)): p for p in
             [os.path.join(KOK, y) for y in TUM
              if y.startswith(".claude/skills/") and y.endswith("SKILL.md")]}
kirik = []
for yol, m in sorted(TUM.items()):
    if not (yol.startswith(".claude/skills/") and yol.endswith("SKILL.md")):
        continue
    for hedef in re.findall(r"KULLANMA[;,] +o(?:nlar)? +([a-z-]+)", m):
        if hedef not in beceriler:
            kirik.append("%s -> %s" % (yol.split("/")[2], hedef))
vaka("U-07", "KULLANMA yönlendirmeleri var olan beceriyi gösteriyor",
     not kirik, "; ".join(kirik) if kirik
     else "%d beceri tarandı" % len(beceriler))

# --- U-08 · bir birimin yontem/ dosyasına yapılan atıf çözülüyor mu ----
ATIF_YOL = re.compile(r"`(birimler/[^`]+\.md)`")
cozulmez = []
for yol, m in sorted(TUM.items()):
    for hedef in set(ATIF_YOL.findall(m)):
        if not os.path.exists(os.path.join(KOK, hedef)):
            cozulmez.append("%s -> %s" % (yol, hedef))
vaka("U-08", "birimler/ atıfları çözülüyor", not cozulmez,
     "; ".join(cozulmez) if cozulmez else "tüm atıflar var olan dosyayı gösteriyor")

# --- U-09 · bekletici etki her yerde aynı mı --------------------------
# İLK SÜRÜM SABİT True YAZIYORDU: tarama bir ihlal bulsa bile vaka yeşil
# kalıyordu. Kitabın §16'da bulduğum `topla "F" 0` kusurunun aynısı, kendi
# takımımda. Vaka artık tarama sonucuna bağlı.
FERAGAT = re.compile(r"feragat edilebilir|vazgeçilebilir|feragat edilebileceği")
bekletici, ihlal = {}, []
for yol, m in sorted(TUM.items()):
    for satir in re.sub(r"\n(?=\s+\S)", " ", m).split("\n"):
        # [AE-03] Çıplak .lower() burada SESSİZ bir körlüktü: 'BEKLETİCİ'
        # küçültülünce 'bekleti̇ci̇' olur (İ -> i + U+0307) ve "bekletici"
        # eşleşmez. Büyük harfle yazılmış bir "BEKLETİCİ ... FERAGAT
        # EDİLEBİLİR" ihlali satır hiç İNCELENMEDEN atlanıyordu — §12'nin
        # B-10 kusurunun kendi takımımdaki hâli.
        d = _tr(satir)
        if "bekletici" not in d:
            continue
        bekletici[yol] = bekletici.get(yol, 0) + 1
        if FERAGAT.search(d) and "edilemez" not in d and "edilmez" not in d:
            ihlal.append("%s: %s" % (yol, satir.strip()[:90]))
vaka("U-09", "bekletici etki hiçbir birimde feragat edilebilir sayılmıyor",
     not ihlal, "; ".join(ihlal) if ihlal
     else "%d dosyada geçiyor, hiçbirinde feragat edilebilir denmiyor"
          % len(bekletici))

# --- U-10 · müvekkile giden her beceri §0 sözleşmesini adlandırıyor mu -
# DÖRDÜNCÜ SÜRÜM. Üçüncüsü "her beceri" dedi ve once-arastir'ı bıraktı.
# Kitabın kuralı (§0) "her ESASLI ÇIKTI"dır ve §12'nin kapsam kapısı bunu
# yalnızca TAVSİYE ya da OLUMSUZ İDDİA biçimindeki metinde arar. once-arastir
# bir araştırma notu üretir, müvekkile giden bir teslim değil. Muafiyet
# BEYAN EDİLİR; beyanın doğruluğu U-11'de kapının kendisiyle sınanır.
SON = ("Şimdi ne yapılmalı", "Yetkili avukat görüşü gereken konular")
MUAF = {"once-arastir": "araştırma notu üretir, müvekkile giden teslim değil"}
eksik = []
beceriler_l = [y for y in sorted(TUM)
               if y.startswith(".claude/skills/") and y.endswith("SKILL.md")]
for yol in beceriler_l:
    ad = yol.split("/")[2]
    if ad in MUAF:
        continue
    duz = re.sub(r"\s+", " ", TUM[yol])
    yok = [b for b in SON if b not in duz]
    if yok:
        eksik.append("%s (%s)" % (ad, " + ".join(yok)))
vaka("U-10", "müvekkile giden her beceri §0 çıktı sözleşmesini adlandırıyor",
     not eksik, "; ".join(eksik) if eksik
     else "%d beceri (%d muaf: %s)"
          % (len(beceriler_l) - len(MUAF), len(MUAF),
             ", ".join("%s — %s" % kv for kv in sorted(MUAF.items()))))

# --- U-11 · muafiyet iddiası kapının kendisiyle sınanıyor mu ----------
# Muaf bir beceri TAVSİYE biçiminde çıktı ÜRETMEMELİDİR. Bu bir kanaat
# değil, çalıştırılabilir bir sınamadır: becerinin BELGELEDİĞİ çıktı biçimi
# kapsam kapısına verilir. Kapı susarsa muafiyet doğrudur; ateşlerse
# muafiyet yanlıştır ve sözleşme o beceride de gereklidir.
try:
    import importlib.util
    _sp = importlib.util.spec_from_file_location(
        "kapi_u", os.path.join(KOK, ".claude/hooks/kapi.py"))
    _kapi = importlib.util.module_from_spec(_sp)
    _sp.loader.exec_module(_kapi)
    ornek = "Kontrol edildi: Resmî Gazete (2026-08-27) · bulunamayan: yok"
    ates = _kapi.kapi_kapsam(ornek)
    vaka("U-11", "muaf becerinin belgelediği çıktı biçimi kapsam kapısını "
         "ateşlemiyor", ates is None,
         "kapı sustu — muafiyet doğrulandı" if ates is None
         else "KAPI ATEŞLEDİ: %s — muafiyet YANLIŞ" % (ates,))
except Exception as e:                                    # noqa: BLE001
    vaka("U-11", "muaf becerinin çıktı biçimi kapıyla sınanabildi", False,
         "kapı yüklenemedi: %s" % e)

BEKLENEN_VAKA = 10  # bir vaka SESSİZCE kaybolursa bu satır onu yakalar


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("U-00", "takım beyan ettiği vaka sayısını taşıyor", False,
             "beyan %d, bulunan %d — bir vaka kayboldu ya da eklendi"
             % (BEKLENEN_VAKA, len(sonuclar)))
    print("=" * 96)
    print("KÖR SINAMA U — birimler birbiriyle çelişiyor mu")
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
