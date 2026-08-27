#!/usr/bin/env python3
"""Token bütçesi: bir belgeyi bağlama sokmanın maliyetini ölçer.

Neden var. Bir SPA ya da bir veri odası klasörü bağlama girdiğinde maliyeti
gerçektir ve ölçülmeden yönetilemez. Bu betik ölçer, kırpmaz: neyin
bırakılacağı hukuki bir karardır, bir sıkıştırma kararı değil.

TAM SAYIM ile TAHMİN arasındaki farkı gizlemez. tiktoken sözlüğü ağdan
indirilir; bu makinede o uç nokta kapalıysa betik çalışmayı bırakmaz, TAHMİNE
düşer ve çıktının başına bunu yazar. Doğrulanmamış bir rakamı doğrulanmış gibi
sunmak, bu sistemin önlemek için var olduğu kusurdur.

    python3 token-butce.py <dosya|klasör> [--parcala]

Doğrulama: 2026-08-27.
"""
import os
import sys

KODLAMA = "o200k_base"
# Türkçe hukuk metninde karakter/token oranı. Sözlük indirilemediğinde
# kullanılır ve çıktıda TAHMİN olarak işaretlenir.
TR_KARAKTER_BASINA_TOKEN = 1 / 3.2
UZANTILAR = (".txt", ".md", ".json", ".csv", ".py", ".html", ".xml")


def sayac():
    """(fonksiyon, kip) döner. kip: 'tam' ya da 'tahmin'."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding(KODLAMA)
        return (lambda t: len(enc.encode(t))), "tam"
    except Exception:
        pass
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return (lambda t: len(enc.encode(t))), "tam"
    except Exception:
        pass
    return (lambda t: int(len(t) * TR_KARAKTER_BASINA_TOKEN)), "tahmin"


def dosyalar(yol):
    if os.path.isfile(yol):
        return [yol]
    cikti = []
    for kok, _, adlar in os.walk(yol):
        if "__pycache__" in kok:
            continue
        for a in adlar:
            if a.lower().endswith(UZANTILAR):
                cikti.append(os.path.join(kok, a))
    return sorted(cikti)


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    say, kip = sayac()
    if kip == "tahmin":
        print("!! TAHMİN KİPİ — tiktoken sözlüğü bu makineden indirilemedi.")
        print("!! Rakamlar büyüklük mertebesidir, tam sayım DEĞİLDİR.")
        print("!! bulunamayan: openaipublic.blob.core.windows.net (ağ çıkışı "
              "kapalı)\n")
    toplam = 0
    satirlar = []
    for f in dosyalar(argv[1]):
        try:
            m = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        n = say(m)
        toplam += n
        satirlar.append((n, f))
    for n, f in sorted(satirlar, reverse=True)[:25]:
        print("  %9d  %s" % (n, f))
    if len(satirlar) > 25:
        print("  ... %d dosya daha" % (len(satirlar) - 25))
    etiket = "TOPLAM" if kip == "tam" else "TOPLAM (TAHMİN)"
    print("\n%s %d token · %d dosya · kip=%s" % (etiket, toplam,
                                                 len(satirlar), kip))
    if "--parcala" in argv and satirlar:
        import semchunk
        chunker = semchunk.chunkerify(say, 2000)
        metin = open(satirlar[0][1], encoding="utf-8",
                     errors="replace").read()
        parcalar = chunker(metin)
        print("en büyük dosya %d parçaya bölündü (parça başı <=2000 token)"
              % len(parcalar))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
