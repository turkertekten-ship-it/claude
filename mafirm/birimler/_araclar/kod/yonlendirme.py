#!/usr/bin/env python3
"""İç yönlendirme denetimi: sistemin gönderdiği her yol gerçekten var mı.

Neden var. Bu sistem sürekli yönlendirir: "beceri: rekabet-esigi",
"`birimler/tr-sirketler/yontem/pay-devri.md` dosyasına bak", "/spa-incele
çalıştır". Bir dosya yeniden adlandırıldığında bu yönlendirmeler sessizce
kırılır ve kırık bir yönlendirme, baskı altındaki bir hukukçuyu çıkmaza
gönderir. Sessiz olduğu için de fark edilmez.

Doğrulama: 2026-08-27.
"""
import glob
import os
import re
import sys

KOK = os.path.expanduser("~/mafirm")

YOL = re.compile(
    r"(?:~/mafirm/)?((?:birimler|isakislari|komutlar|hafiza|emsal|dosyalar)"
    r"/[A-Za-z0-9_./*-]+)")


def topla():
    os.chdir(KOK)
    dosyalar = [p for p in glob.glob("**/*", recursive=True)
                if os.path.isfile(p) and p.endswith((".md", ".py", ".sh"))]
    beceriler = {os.path.basename(os.path.dirname(p))
                 for p in glob.glob(".claude/skills/*/SKILL.md")}
    ajanlar = {os.path.splitext(os.path.basename(p))[0]
               for p in glob.glob(".claude/agents/*.md")}
    komutlar = {os.path.splitext(os.path.basename(p))[0]
                for p in glob.glob(".claude/commands/*.md")}
    return dosyalar, beceriler, ajanlar, komutlar


def denetle():
    dosyalar, beceriler, ajanlar, komutlar = topla()
    kirik = []
    for f in dosyalar:
        metin = open(f, encoding="utf-8", errors="replace").read()
        for m in YOL.finditer(metin):
            y = m.group(1).rstrip(".,;:)`")
            # Yer tutucu, glob ve canlı dosya klasörü denetlenmez.
            if "<" in y or "*" in y or y.endswith("/"):
                continue
            if y.startswith("dosyalar/"):
                continue
            if not os.path.exists(y):
                kirik.append(("yol", f, y))
        for m in re.finditer(r"[Bb]eceri:?\s*`([a-z0-9-]+)`", metin):
            if m.group(1) not in beceriler:
                kirik.append(("beceri", f, m.group(1)))
        for m in re.finditer(r"[Aa]lt ajan:?\s*`([a-z-]+)`", metin):
            if m.group(1) not in ajanlar:
                kirik.append(("ajan", f, m.group(1)))
        for m in re.finditer(r"`/([a-z][a-z0-9-]{2,})[\s`<]", metin):
            if m.group(1) not in komutlar:
                kirik.append(("komut", f, "/" + m.group(1)))
    return sorted(set(kirik))


def main():
    kirik = denetle()
    for tur, f, x in kirik:
        print("  KIRIK [%-6s] %-44s -> %s" % (tur, f, x))
    print("YÖNLENDİRME %s" % ("OK" if not kirik else "KIRIK %d" % len(kirik)))
    return len(kirik)


if __name__ == "__main__":
    sys.exit(main())
