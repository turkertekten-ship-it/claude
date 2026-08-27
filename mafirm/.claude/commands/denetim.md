---
description: Sistemdeki her sınamayı ve kapıyı çalıştırır; sesli biçimde başarısız olur.
---

Tam denetimi çalıştır ve **gerçek çıktısını** yapıştır. Özetleme.

    bash ~/mafirm/denetim.sh

Ardından araç katmanını da doğrula:

    python3 ~/mafirm/birimler/_araclar/kod/dogrula.py

Herhangi bir satır HATA dönerse:
1. Hangi kontrolün, hangi komutla, ne çıktı vererek başarısız olduğunu yaz.
2. Nedenini teşhis et.
3. Düzeltmeyi öner — ama bir eşik dosyasını kendiliğinden düzenleme.

Denetim yeşil değilse kurulum "bitti" değildir. Bunu çalıştırmadan bitti diyen
bir kurulum hiçbir şey söylememiştir.
