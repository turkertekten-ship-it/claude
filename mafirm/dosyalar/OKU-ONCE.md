# Dosyalar — canlı işler

Doğrulama: 2026-08-27.

Kontrol edildi: kurulum kitabı §2 ve §11 (2026-08-27) · bulunamayan: —

Bu klasör canlı işleri tutar. Kurulumda boştur.

## Bir dosya nasıl açılır

Elle değil, komutla:

    /dosya-ac <dosya adı>

Komut sırayla şunları yapar ve **birinci adım atlanamaz**:

1. `hafiza/cikar-catismasi.md` karşı taraflar için okunur. **Eşleşme varsa
   DUR** — klasör açılmaz, temas kurulmaz. Çatışma bir uyarı değil, durma
   sebebidir (işletim sözleşmesi §8).
2. Klasör kurulur.
3. Kapsam notu yazılır: kapsam içinde · kapsam DIŞINDA · varsayımlar.
4. Sorumluluk kayıtları eklenir.
5. İlk yaptırım taraması çalıştırılır ve tarihiyle kaydedilir.

## Klasör düzeni

    dosyalar/<dosya-adi>/
      kapsam.md      ne yapılacak, ne yapılmayacak, varsayımlar
      taraflar.md    kim kimdir, gerçek lehtarlar dahil
      tarama/        yaptırım ve nüfuz taraması çıktıları, tarihli
      belgeler/      alınan belgeler
      veri/          ham veri odası kopyası — .gitignore'da
      cikti/         üretilen çıktılar

`veri/` bilerek sürüm kontrolü dışındadır: müvekkil belgesinin ham kopyası
depoya girmez (işletim sözleşmesi §6).

## Hangi iş akışı

| Durum | Akış |
|---|---|
| Yabancı alıcı, Türk hedef | `isakislari/01-alici-tarafi.md` |
| Türk satıcı | `isakislari/02-satici-tarafi.md` |
| Yalnızca "izin gerekir mi" | `isakislari/03-hizli-esik.md` |
| Kapanmış işlem | `isakislari/04-kapanis-sonrasi.md` |

## Dosya kapandığında

İki şey yapılır ve ikisi de unutulur:

1. Onaylanmış maddeler `emsal/` bankasına taşınır (biçim, pozisyon, bağlam
   ayrı ayrı).
2. Taraflar `hafiza/cikar-catismasi.md` kaydına yazılır. Kayıt yalnızca içine
   yazılan kadar iyidir; beslenmeyen bir çatışma kaydı, gelecekteki bir dosyayı
   sessizce riske atar.

## Şimdi ne yapılmalı

İlk dosyayı `/dosya-ac` ile açın. Klasörü elle oluşturmak çatışma kontrolünü
atlar ve o kontrol bu sistemdeki tek geri alınamaz kapıdır.

## Yetkili avukat görüşü gereken konular

Kapsamın kendisi, kapsam dışı bırakılan her kalem ve dosyanın alınıp
alınmayacağı kararı.
