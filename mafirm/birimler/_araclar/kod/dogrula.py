#!/usr/bin/env python3
"""Araç kataloğunun gerçek doğrulaması: pip listesi değil, import.

Bir paket kurulu görünüp import edilemeyebilir ve bu fark yalnızca ona
ihtiyaç duyulduğunda ortaya çıkar. Bu kurulumda tam olarak bu oldu.
Doğrulama: 2026-08-27.
"""
import importlib
import shutil
import sys

# (modül, katman, ne için)
MODULLER = [
    ("docling",          "belge",   "madde hiyerarşisini koruyarak çıkarır"),
    ("pdfplumber",       "belge",   "hücre koordinatına iner"),
    ("docx",             "belge",   "koddan biçemli Word belgesi"),
    ("nomenklatura",     "tarama",  "varlık eşleştirme ve tekilleştirme"),
    ("pandera",          "cetvel",  "veri çerçevesi şeması"),
    ("diff_match_patch", "madde",   "iki sürümü gerçekten karşılaştırır"),
    ("eyecite",          "atif",    "ABD atıfları — Türk içtihadı YOK"),
    ("tiktoken",         "token",   "token sayar"),
    ("semchunk",         "token",   "anlamsal parçalama"),
    ("chonkie",          "token",   "parçalama boru hattı"),
    ("gitingest",        "token",   "depoyu özet metne indirger"),
    ("tokencost",        "token",   "maliyet tahmini"),
    ("llmlingua",        "token",   "istem sıkıştırma"),
]

KOMUTLAR = [
    ("docling",         "belge"), ("ttok", "token"), ("strip-tags", "token"),
    ("files-to-prompt", "token"), ("gitingest", "token"),
    ("repomix",         "token"),
]


def main():
    hata = 0
    print("=== modüller (import denemesi) ===")
    for mod, katman, ne in MODULLER:
        try:
            importlib.import_module(mod)
            print("  ok       [%-6s] %-17s %s" % (katman, mod, ne))
        except Exception as e:
            print("  KURULU DEĞİL [%-6s] %-17s (%s)"
                  % (katman, mod, type(e).__name__))
            hata += 1
    print("=== komut satırı araçları ===")
    for cmd, katman in KOMUTLAR:
        yol = shutil.which(cmd)
        if yol:
            print("  ok       [%-6s] %-17s %s" % (katman, cmd, yol))
        else:
            print("  YOK      [%-6s] %s" % (katman, cmd))
            hata += 1
    print()
    print("ARAÇ DOĞRULAMA %s" % ("OK" if not hata else "HATA %d" % hata))
    return hata


if __name__ == "__main__":
    sys.exit(main())
