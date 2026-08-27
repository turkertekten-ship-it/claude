---
name: dosya-ac
description: Yeni bir dosya (matter) açılırken kullan. Çıkar çatışması kontrolü, klasör yapısı, kapsam notu ve sorumluluk kayıtları gerektiğinde devreye girer. Yeni bir müvekkil, yeni bir işlem ya da mevcut bir müvekkil için yeni bir iş başlarken.
---

# Dosya açma

## Sıra katıdır — birinci adım atlanamaz

1. **Çıkar çatışması kontrolü.** `hafiza/cikar-catismasi.md` karşı taraflar
   için okunur. **Çatışma bir uyarı değil, durma sebebidir** (işletim
   sözleşmesi §8). Eşleşme varsa dosya açılmaz ve bu, insana bildirilir.

2. **Klasör.**

        dosyalar/<dosya-adi>/
          kapsam.md      ne yapılacak, ne yapılmayacak
          taraflar.md    kim kimdir, gerçek lehtarlar dahil
          tarama/        yaptırım ve nüfuz taraması çıktıları
          belgeler/      alınan belgeler
          veri/          ham veri odası kopyası (gitignore'da)
          cikti/         üretilen çıktılar

3. **Kapsam notu.** Üç başlık: kapsam içinde olan, kapsam DIŞINDA olan,
   varsayımlar. Kapsam dışı bırakılan her şey yazılır — sessizce dışarıda
   bırakılan bir kalem, yapılmış sayılır.

4. **Sorumluluk kayıtları.** Kapsam notu şu üç cümleyle biter:
   - Bu dosyada üretilen hiçbir çıktı hukuki görüş değildir.
   - Her esaslı çıktı iki zorunlu başlıkla biter.
   - Türkiye'de tescil, imza, kurum başvurusu ve müvekkile tavsiye baroya
     kayıtlı avukat gerektirir.

5. **İlk taramalar.** Hedef, ana ortaklar ve bilinen gerçek lehtarlar
   (`yaptirim-taramasi` becerisi).

## Çıktı

Açılan klasörün ağacı, kapsam notunun kendisi ve çıkar çatışması kontrolünün
sonucu (tarih ve neye bakıldığıyla).
Şununla bitir: Şimdi ne yapılmalı / Yetkili avukat görüşü gereken konular /
Kontrol edildi:
