#!/usr/bin/env python3
"""Kapanış hesapları cetveli şeması (pandera).

Neden var. Kapanış hesapları uyuşmazlığı genellikle bir sütun başlığının
çağrıştırdığı şeyi mi taşıdığı üzerinedir. Şema bunu kodda söyler ve rakam
kullanılmadan ÖNCE durur.

    python3 cetvel.py <dosya.csv>

Doğrulama: 2026-08-27.
"""
import sys


def sema():
    import pandera.pandas as pa
    return pa.DataFrameSchema({
        "kalem":  pa.Column(str, nullable=False),
        "tutar":  pa.Column(float, nullable=False),
        "yon":    pa.Column(str, pa.Check.isin(["borc", "alacak"])),
        "kaynak": pa.Column(str, nullable=False),   # her rakam dayanağıyla
    }, strict=False, coerce=True)


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    import pandas as pd
    df = pd.read_csv(argv[1])
    try:
        sema().validate(df, lazy=True)
    except Exception as e:
        print("CETVEL REDDEDİLDİ — rakam kullanılmadan önce durdu:\n")
        print(e)
        return 1
    print("CETVEL OK · %d satır doğrulandı" % len(df))
    print("Her satır 'kaynak' sütunu taşıyor: kanıt kuralı (§1) cetvelde de "
          "geçerli.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
