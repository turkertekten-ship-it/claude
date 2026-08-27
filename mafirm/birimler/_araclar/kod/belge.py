#!/usr/bin/env python3
"""Belge çıkarma: docling madde yapısını, pdfplumber hücre koordinatını verir.

Hangisi ne zaman. Bir SPA'nın madde hiyerarşisi lazımsa docling; bir kapanış
hesapları cetvelinde bir hücrenin nereye düştüğü lazımsa pdfplumber. İkisi
birbirinin yerine geçmez ve bu betik hangisini neden seçtiğini yazar.

Müvekkil belgesi makinede kalır: hiçbir uç noktaya gönderilmez (işletim
sözleşmesi §6).

    python3 belge.py <dosya> --yapi     # docling, madde yapısı korunarak
    python3 belge.py <dosya> --cetvel   # pdfplumber, tablo + koordinat

Doğrulama: 2026-08-27.
"""
import os
import sys


def yapi(yol):
    from docling.document_converter import DocumentConverter
    sonuc = DocumentConverter().convert(yol)
    return sonuc.document.export_to_markdown()


def cetvel(yol):
    import pdfplumber
    parcalar = []
    with pdfplumber.open(yol) as pdf:
        for i, sayfa in enumerate(pdf.pages, 1):
            for j, tablo in enumerate(sayfa.extract_tables(), 1):
                parcalar.append("## sayfa %d · tablo %d" % (i, j))
                for satir in tablo:
                    parcalar.append(" | ".join(
                        "" if h is None else str(h).replace("\n", " ")
                        for h in satir))
    return "\n".join(parcalar) if parcalar else "(tablo bulunamadı)"


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    yol = argv[1]
    if not os.path.exists(yol):
        print("dosya yok: %s" % yol, file=sys.stderr)
        return 2
    kip = "--cetvel" if "--cetvel" in argv else "--yapi"
    if kip == "--cetvel":
        print("# pdfplumber · tablo ve koordinat (docling değil: cetvel "
              "istendi)\n")
        print(cetvel(yol))
    else:
        print("# docling · madde hiyerarşisi korunarak\n")
        print(yapi(yol))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
