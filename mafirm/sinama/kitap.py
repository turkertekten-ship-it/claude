#!/usr/bin/env python3
"""Kitabın metnini .docx'ten çıkarmanın TEK yeri.

Neden ortak: elli birinci turda AW-01, kitaba atfettiğim bir alıntıyı
"bulunamadı" diye işaretledi. Alıntı doğruydu; ÇIKARICI yanlıştı.

Word'de yumuşak satır sonu `<w:br/>` etiketiyle yazılır ve paragraf sonundan
(`</w:p>`) ayrıdır. Beş takım da yalnızca paragraf sonunu satır sonuna
çeviriyor, `<w:br/>` etiketini ise diğer etiketlerle birlikte SİLİYORDU.
Sonuç: satır sonunun iki yanındaki sözcükler birbirine YAPIŞIYORDU —
"işletim" + "sözleşmesi" = "işletimsözleşmesi". Kitapta 1022 yumuşak satır
sonu var; çıkarılan metin 1038 karakterlik ayırıcıyı kaybediyordu.

Bu, ölçüm ALETİNİN kusuruydu ve on bir tur boyunca beş takımın hepsini
etkiledi: kitaba yapılan her birebir arama, bir satır sonunu geçtiği anda
sessizce başarısız oluyordu. Yeni bir ölçüm eski aleti bozuk buldu.

Tek yerde durmasının sebebi de bu: aynı kusurun beş kopyası, beş kez
düzeltilmeyi bekler ve dördü unutulur.
"""
import html
import os
import re
import zipfile

DOCX = ("/root/.claude/uploads/a0f718bf-fd01-52d5-a508-48d77db2834c/"
        "0ca2aeab-RePieArelMAAvukatClaudeKurulumKitabi.docx")

# Metinde AYIRICI üreten her etiket. Paragraf sonu, yumuşak satır sonu ve
# sekme; üçü de metinde boşluk demektir ve üçü de silinirse sözcük yapışır.
AYIRICI = re.compile(r"</w:p>|<w:br\s*/>|<w:tab\s*/>")


def metin(yol=None):
    """Kitabın düz metni. Dosya yoksa boş dize döner."""
    yol = yol or DOCX
    if not os.path.exists(yol):
        return ""
    with zipfile.ZipFile(yol) as z:
        x = z.read("word/document.xml").decode("utf-8")
    return html.unescape(re.sub(r"<[^>]+>", "", AYIRICI.sub("\n", x)))


# --- YAPI: metin desenlerinden değil, Word'ün KENDİ biçem bilgisinden ----
# Yumuşak satır sonları geri gelince "N. Başlık" deseni artık bölüm başlığı
# ile numaralı liste maddesini ayırt edemiyor: ikisi de satır başında "N."
# ile başlıyor. Desen, bozuk metin üzerinde yalnızca RASTLANTIYLA çalışıyordu.
# Word bunu zaten biliyor: bölümler Heading2, alt bölümler Heading3.
_PARA = re.compile(r"<w:p[ >].*?</w:p>", re.S)
_STIL = re.compile(r'<w:pStyle w:val="([^"]+)"')


def _paragraflar(yol=None):
    yol = yol or DOCX
    if not os.path.exists(yol):
        return []
    with zipfile.ZipFile(yol) as z:
        x = z.read("word/document.xml").decode("utf-8")
    cikti = []
    for m in _PARA.finditer(x):
        p = m.group(0)
        st = _STIL.search(p)
        t = html.unescape(re.sub(r"<[^>]+>", "", AYIRICI.sub(" ", p))).strip()
        cikti.append((st.group(1) if st else "", t))
    return cikti


def bolumler(yol=None):
    """{numara: başlık} — Word'ün Heading2 paragrafları."""
    d = {}
    for st, t in _paragraflar(yol):
        if st == "Heading2":
            m = re.match(r"(\d{1,2})\.\s+(.+)$", t)
            if m:
                d[int(m.group(1))] = m.group(2).strip()
    return d


def altbolumler(yol=None):
    """{'N.M'} — Word'ün Heading3 paragrafları."""
    k = set()
    for st, t in _paragraflar(yol):
        if st == "Heading3":
            m = re.match(r"(\d{1,2}\.\d{1,2})\b", t)
            if m:
                k.add(m.group(1))
    return k


def maddeler(n, yol=None):
    """§n içindeki numaralı liste maddelerinin numaraları.

    Maddeler AYRI PARAGRAF değildir: numara ile gövde aynı paragrafın içinde,
    yumuşak satır sonuyla ayrılmıştır. Bu yüzden yapı değil METİN görünümü
    kullanılır — ama sınırlar yine Word'ün başlıklarından alınır, desenden
    değil."""
    b = bolumler(yol)
    if n not in b:
        return set()
    t = metin(yol)
    bas = t.find("%d. %s" % (n, b[n]))
    if bas < 0:
        return set()
    sonrakiler = [t.find("%d. %s" % (m, b[m])) for m in b if m > n]
    sonrakiler = [x for x in sonrakiler if x > bas]
    son = min(sonrakiler) if sonrakiler else len(t)
    return {int(m.group(1))
            for m in re.finditer(r"^\s*(\d{1,2})\.\s*$", t[bas:son], re.M)}


def govdeler(yol=None):
    """{numara: (başlık, gövde)} — sınırlar Heading2'den, gövde metinden.

    AY takımı bölümün İÇİNDEKİ iddiaları sınadığı için gövdeye ihtiyaç
    duyar; sınırların desenden değil biçemden gelmesi şart, yoksa numaralı
    liste maddeleri bölüm sanılır ve gövdeler birbirine karışır."""
    b = bolumler(yol)
    t = metin(yol)
    yer = []
    for n in sorted(b):
        i = t.find("%d. %s" % (n, b[n]))
        if i >= 0:
            yer.append((n, i))
    yer.sort(key=lambda x: x[1])
    d = {}
    for k, (n, i) in enumerate(yer):
        son = yer[k + 1][1] if k + 1 < len(yer) else len(t)
        d[n] = (b[n], t[i:son])
    return d
