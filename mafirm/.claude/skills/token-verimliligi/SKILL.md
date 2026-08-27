---
name: token-verimliligi
description: Uzun bir belge, veri odası klasörü ya da depo bağlama sokulmadan önce maliyeti ölçülürken kullan. "Bu SPA bağlama sığar mı", "bu klasör kaç token", "bunu nasıl küçültürüz" sorularında ve bir belgeyi parçalamak, kırpmak ya da sıkıştırmak gerektiğinde devreye girer.
---

# Token bütçesi

Kurulum kitabında yok; bu pratiğe eklendi. Bir SPA'yı ya da veri odasını bağlama
sokmanın maliyeti gerçektir ve ölçülmeden yönetilemez.

## Önce ölç

    python3 ~/mafirm/birimler/_araclar/kod/token-butce.py <dosya|klasör>

Betik TAM SAYIM ile TAHMİN arasındaki farkı gizlemez: tiktoken sözlüğü
indirilemiyorsa çıktının başına TAHMİN yazar. Doğrulanmamış bir rakamı
doğrulanmış gibi sunmak, bu sistemin önlemek için var olduğu kusurdur.

## Sonra küçült — sırayla

| Araç | Ne zaman |
|---|---|
| `strip-tags` | Kaynak HTML ise, etiketleri at |
| `files-to-prompt <klasör>` | Bir klasörü tek isteme çevir |
| `repomix` | Bir kod deposunu token sayımıyla paketle |
| `gitingest <url\|yol>` | Depoyu özet metne indirge |
| `ttok -t <n>` | Sert bir üst sınıra kırp |
| `semchunk` / `chonkie` | Anlamsal parçalara böl (`--parcala`) |
| `llmlingua` | İstemi sıkıştır — **son çare** |

## Katı kural: kırpma hukuki bir karardır

Bu araçlar ölçer ve böler. **Neyin bırakılacağına model karar vermez.** Bir
SPA'dan sınırlama maddelerini düşüren bir sıkıştırma, teknik olarak başarılı
hukuki olarak felakettir. Kırpılan her şey çıktıda adıyla yazılır:

    Bağlama alınmayan: <ne> (<neden>)

## Sır saklama kuralı

Bu araçların hepsi yereldir ve hiçbiri belgeyi dışarı göndermez. Müvekkil metnini
bir sıkıştırma servisine yollamak, kolaylık için esnetilmeyecek bir yasaktır
(işletim sözleşmesi §6).

## Çıktı

Ölçüm tablosu, uygulanan indirgeme ve bağlama alınmayanların listesi.
Şununla bitir: Şimdi ne yapılmalı / Yetkili avukat görüşü gereken konular /
Kontrol edildi:
