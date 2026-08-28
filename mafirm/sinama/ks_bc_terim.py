#!/usr/bin/env python3
"""KÖR SINAMA BC — §10 terim açıklaması, beyanla değil KEŞİFLE.

Yönelim (kırk sekizinci tur). §10 açık: *"Piyasada karşılığı yerleşmiş
İngilizce terimler korunur ve İLK GEÇTİKLERİNDE AÇIKLANIR."* R-06 bunu
sınıyordu — ama üç terimden oluşan ELLE YAZILMIŞ bir listeyle: NFKC,
CONNECT, homoglif. Yani ölçüt yalnızca açıklandığını zaten bildiği
terimleri soruyordu ve kırk yedi tur boyunca "temiz" dedi.

Rapor bu üç terimi değil, düzyazısında yirmiden fazla İngilizce/teknik
terim taşıyor. Bu, "elle yazılan liste ölçtüğü şeyden sürüklenir"
sınıfının ÜÇÜNCÜ örneğidir (P takımının TESLIMATLAR listesi, M-03'ün
önek listesi, ve şimdi R-06'nın terim listesi). Yirmi yedinci turun
kuralı: üç örnek bir sınıftır ve sınıf duran bir sağlamayla kapanır.
Bu takım listeyi KEŞFE çevirir.

Türkçe vurgu ile İngilizce terimi ayırmak için tek bir ölçüt yeterli:
bir sözcüğün küçük harfli hâli belgede sıradan bir Türkçe sözcük olarak
geçiyorsa (DAYANAK/dayanak, HER/her), o büyük harf VURGUDUR, terim değil.
API, NFKC, SIGKILL gibi terimlerin küçük harfli Türkçe karşılığı yoktur.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beklenen  # noqa: E402

_KOK = os.environ.get("MAFIRM") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

sonuclar = []


def vaka(kod, baslik, gecti, kanit=""):
    sonuclar.append((kod, baslik, gecti, kanit))


def oku(*p):
    y = os.path.join(_KOK, *p)
    return io.open(y, encoding="utf-8").read() if os.path.exists(y) else ""


def tr_kucult(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def duzyazi(metin):
    """§10 DÜZYAZI hakkındadır: kod, yol ve tablo terim taşımaz."""
    metin = re.sub(r"```.*?```", " ", metin, flags=re.S)
    metin = re.sub(r"`[^`]*`", " ", metin)
    metin = re.sub(r"^\|.*$", " ", metin, flags=re.M)
    metin = re.sub(r"https?://\S+", " ", metin)
    metin = re.sub(r"\b[\w./-]+\.(py|sh|md|json|txt|html|docx|pdf)\b", " ", metin)
    # Yalnızca * soyulur: _ bir tanımlayıcının parçasıdır ve soyulunca
    # HTTPS_PROXY "HTTPSPROXY" diye YENİ bir terim uydurur.
    metin = re.sub(r"\*+", "", metin)
    return re.sub(r"\s+", " ", metin)


def duzyazi_html(metin):
    """Artifact'in düzyazısı: etiket, biçem, kod ve dosya adı terim değildir."""
    metin = re.sub(r"<style.*?</style>|<script.*?</script>|<pre.*?</pre>",
                   " ", metin, flags=re.S)
    metin = re.sub(r"<code[^>]*>.*?</code>", " ", metin, flags=re.S)
    metin = re.sub(r"<[^>]+>", " ", metin)
    metin = re.sub(r"&[a-z]+;", " ", metin)
    metin = re.sub(r"https?://\S+", " ", metin)
    metin = re.sub(r"\b[\w./-]+\.(py|sh|md|json|txt|html|docx|pdf)\b", " ", metin)
    return re.sub(r"\s+", " ", metin)


# [Kırk dokuzuncu tur] BC yalnızca RAPOR'u ölçüyordu. Okuyucunun AÇTIĞI belge
# ise artifact'tir ve orada terimlerin HİÇBİRİ açıklanmamıştı. BB sayıları iki
# belgede birden ölçüyordu; BC terimleri tek belgede ölçüyordu. Aynı sınıf,
# yarım uygulanmış.
RAPOR = duzyazi(oku("RAPOR.md"))
ARTIFACT = duzyazi_html(oku("kor-sinama-raporu.html"))
BELGELER = (("RAPOR", RAPOR), ("ARTIFACT", ARTIFACT))

# --- muafiyetler: gerekçesiyle BEYAN edilir, sessizce büyüyemez --------
# Her beyan bir şey örtmek ZORUNDA (BC-02); örtmeyen beyan bayattır.
# İki tür muafiyet vardır ve ikisi aynı kurala tabi değildir:
#
#   MUAF_KURUM   — POLİTİKA. §10 kurum, mevzuat ve para birimi adlarını
#                  çevirmemeyi emreder; bu muafiyet bugün bir terim örtmese
#                  bile geçerlidir ve yarın o terim geri geldiğinde hazırdır.
#   MUAF_KALINTI — ÇIKARICININ ARTIĞI. Aksansız yazılmış Türkçe sözcükler,
#                  dosya adı parçaları. Bunlar KANITA bağlıdır: hiçbir şeyi
#                  örtmeyen bir kalıntı beyanı, çıkarıcının değiştiğinin
#                  işaretidir ve sessizce durmamalıdır.
MUAF_KURUM = {
    "TTK": "Türk Ticaret Kanunu'nun yerleşik kısaltması; §10 kurum ve "
           "mevzuat adlarını çevirmemeyi emreder",
    "SPK": "Sermaye Piyasası Kurulu'nun yerleşik kısaltması; aynı gerekçe",
    "EUR": "ISO 4217 para birimi kodu; hukukçu okuyucu için standart",
    "USD": "ISO 4217 para birimi kodu; aynı gerekçe",
    "TRY": "ISO 4217 para birimi kodu; aynı gerekçe",
    "MIT": "yazılım lisansı adı; ilk geçtiği yerde lisans bağlamında, "
           "AGPL ile karşılaştırılarak tanımlanıyor",
}
MUAF_KALINTI = {
    "YYYY": "tarih biçimi şablonu, terim değil",
    "HOME": "ortam değişkeni adı, düzyazı terimi değil",
    "INDEX": "kitabın kendi dosya adının büyük harfli anılması",
    "ESIK": "Türkçe 'eşik' sözcüğünün aksansız yazımı",
    "BITTI": "Türkçe 'bitti' sözcüğünün aksansız yazımı",
    "FERAGAT": "Türkçe hukuk terimi, İngilizce değil",
    "ABA": "kitaptaki vaka kimliği öneki",
    "HER": "Türkçe 'her' sözcüğünün vurgulu yazımı; çekimli akrabası yok",
    "EVET": "eşik cevabının üç değerinden biri; Türkçe, çekimli akrabası yok",
    "HAYIR": "eşik cevabının üç değerinden biri; Türkçe, çekimli akrabası yok",
    "ERRATA": "Türkçe metinde yerleşik alıntı sözcük; çekimli akrabası yok",
}
MUAF = dict(MUAF_KURUM, **MUAF_KALINTI)


# --- keşif -------------------------------------------------------------
_kucuk = set(re.findall(r"\b[a-zçğıöşü][a-zçğıöşü]{2,}\b",
                        RAPOR + " " + ARTIFACT))


def _turkce_vurgu(k):
    """Küçük harfli hâli belgede sıradan sözcükse, bu bir VURGUDUR."""
    if re.search(r"[ÇĞİÖŞÜ]", k):
        return True
    kk = tr_kucult(k)
    # AYIRICI: Türkçe bir sözcük düzyazıda ÇEKİMLİ hâlleriyle de geçer
    # ("saklama/saklanabilir", "dayanaksız/dayanan"); bir kısaltma ise
    # yalnızca KENDİSİ olarak geçer ("json" → yine "json").
    #
    # Yalnızca birebir eşleşmeye bakmak JSON'u Türkçe vurgu sanıyordu;
    # yalnızca gövdeye bakmak da aynı hatayı yapar. Ölçüt bu yüzden
    # BAŞKA bir çekimli akraba arar. Bulamadığı kalanlar tahmin edilmez,
    # MUAF_KALINTI'da gerekçesiyle BEYAN edilir.
    kok = kk[:4] if len(kk) >= 5 else kk
    return len(kk) >= 3 and any(w.startswith(kok) and w != kk for w in _kucuk)


ADAYLAR = sorted({k for _a, _m in BELGELER
                  for k in re.findall(r"\b[A-Z][A-Z0-9]{2,9}\b", _m)
                  if not _turkce_vurgu(k)})
TERIMLER = [k for k in ADAYLAR if k not in MUAF]

# --- açıklama, CÜMLE ölçeğinde ----------------------------------------
# [AQ-01 / BB] Karakter penceresi komşuyu kanıt sanar. Açıklama, terimin
# İLK geçtiği CÜMLE içinde ve terimin HEMEN ardında olmalıdır: parantez,
# uzun çizgi, iki nokta ya da "yani".
# İlk yazım açıklamanın terime BİTİŞİK olmasını istedi ve NFKC'yi
# "açıklanmamış" saydı — oysa açıklaması aynı cümlede, birkaç sözcük
# sonrasındaydı ("NFKC ile birleştir (Unicode'un uyumluluk
# normalleştirmesi…)"). Sınır CÜMLEDİR; cümlenin içindeki sözcük mesafesi
# bir pencere değil, cümle içi bir incelticidir: hiçbir komşu cümleye
# uzanmaz.
# Gevşetilmiş sürüm (cümle içinde 12 sözcük) YEDİ YANLIŞ GEÇİŞ verdi: DOI
# bir virgüllü listenin iki noktasıyla, HTTPS yanındaki CONNECT parantezinin
# içinden, UTC ilgisiz bir "(1 gün)" ile "açıklanmış" sayıldı. Noktalama,
# anlamın vekili değildir — bu incelemenin baştan beri gördüğü şey.
#
# Bu yüzden ölçüt GEVŞETİLMEDİ, BELGE SIKILAŞTIRILDI: açıklama terimin
# hemen ardında durur (Türkçe eki alabilir), parantez / uzun çizgi / iki
# nokta / "yani" ile başlar. Ölçütün tahmin etmesi gereken hiçbir şey
# kalmaz; §10'un istediği de tam olarak budur.
ACIKLAMA = re.compile(
    r"^['’]?[a-zçğıöşü]{0,4}[-\d.]*\s*(?:\(|—|–|:|,?\s*yani\b)")


def ilk_cumle(terim, metin=None):
    # [BC, dedektörün kendi kusuru] İlk yazım düz alt dizi araması yapıyordu:
    # "PDF"in ilk geçişi "PyMuPDF" içinde bulunuyordu. Keşif sözcük sınırı
    # kullanırken ölçüm kullanmıyordu; iki farklı şeyi ölçüyorlardı.
    metin = RAPOR if metin is None else metin
    m = re.search(r"\b%s\b" % re.escape(terim), metin)
    if not m:
        return None, None
    i = m.start()
    bas = max(metin.rfind(".", 0, i), metin.rfind("!", 0, i),
              metin.rfind("?", 0, i)) + 1
    ucu = [x for x in (metin.find(".", i), metin.find("!", i),
                       metin.find("?", i)) if x > 0]
    son = min(ucu) if ucu else len(metin)
    return metin[bas:son + 1].strip(), metin[i + len(terim):son + 1]


def cipllaklar(metin):
    kotu = []
    for t in TERIMLER:
        _c, _ard = ilk_cumle(t, metin)
        if _c is None:
            continue
        if not ACIKLAMA.match(_ard or ""):
            kotu.append(t)
    return kotu


_aciklanmamis = cipllaklar(RAPOR)
_aciklanmamis_html = cipllaklar(ARTIFACT)

# --- BC-01 · her keşfedilen terim ilk geçişte açıklanmış ---------------
vaka("BC-01", "düzyazıdaki her İngilizce/teknik terim ilk geçişte açıklanmış",
     not _aciklanmamis,
     "%d terim keşfedildi · açıklanmamış (%d): %s"
     % (len(TERIMLER), len(_aciklanmamis), _aciklanmamis[:12] or "yok"))

# --- BC-02 · muafiyet beyanlı ve tamamı kullanılıyor -------------------
_bayat = sorted(k for k in MUAF_KALINTI if k not in ADAYLAR)
vaka("BC-02", "her muafiyet gerekçeli; hiçbir kalıntı beyanı bayat değil",
     not _bayat and all(len(v) > 20 for v in MUAF.values()),
     "%d politika + %d kalıntı muafiyeti · bayat kalıntı: %s"
     % (len(MUAF_KURUM), len(MUAF_KALINTI), _bayat or "yok"))

# --- BC-03 · keşif vakum değil ----------------------------------------
# Elle yazılmış üç terimlik listenin yerine geçen şey, gerçekten KEŞİF
# olmalı: hem yeterince aday bulmalı, hem Türkçe vurguyu ayıklamalı.
_vurgu_ayikladi = _turkce_vurgu("DAYANAK") and not _turkce_vurgu("NFKC")
vaka("BC-03", "keşif yeterince aday buluyor ve Türkçe vurguyu ayıklıyor",
     len(ADAYLAR) >= 15 and _vurgu_ayikladi,
     "%d aday · %d terim · vurgu ayıklaması: %s"
     % (len(ADAYLAR), len(TERIMLER), _vurgu_ayikladi))

# --- BC-04 · ölçüt cümle ölçeğinde, pencerede değil --------------------
_kaynak = io.open(os.path.abspath(__file__), encoding="utf-8").read()
_kod = "\n".join(r for r in _kaynak.splitlines()
                 if not r.lstrip().startswith("#"))
_pencere = re.search(r"\[max\(0,|\.\{0,\d{3,}\}|\[\s*ilk\s*:\s*ilk\s*\+", _kod)
vaka("BC-04", "ölçüt cümle ölçeğinde ölçüyor, karakter penceresinde değil",
     _pencere is None, "pencere kullanımı: %s" % bool(_pencere))

# --- BC-05 · kurum adları çevrilmemiş (§10'un ikinci yarısı) -----------
CEVIRI = {
    "Competition Authority": "Rekabet Kurumu",
    "Capital Markets Board": "Sermaye Piyasası Kurulu",
    "Trade Registry Directorate": "Ticaret Sicili Müdürlüğü",
    "Turkish Commercial Code": "Türk Ticaret Kanunu",
}
_cevrilmis = [e for e in CEVIRI if re.search(r"\b%s\b" % re.escape(e), RAPOR)]
vaka("BC-05", "kurum ve mevzuat adları çevrilmemiş",
     not _cevrilmis, "çevrilmiş: %s" % (_cevrilmis or "yok"))


# --- BC-06 · artifact de aynı kurala tabi ------------------------------
vaka("BC-06", "artifact düzyazısındaki her terim de ilk geçişte açıklanmış",
     not _aciklanmamis_html,
     "açıklanmamış (%d): %s"
     % (len(_aciklanmamis_html), _aciklanmamis_html[:12] or "yok"))


BEKLENEN_VAKA = 6


def rapor():
    if len(sonuclar) != BEKLENEN_VAKA:
        vaka("BC-00", "takım beyan ettiği vaka sayısını taşıyor", False,
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
