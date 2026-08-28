---
name: dosya-ac
description: Yeni bir dosya (iş) açılırken, bir işe klasör, çıkar çatışması kontrolü ve kapsam notu gerektiğinde kullan. Çatışma kontrolünü açılışın önkoşulu yapar ve bir eşleşmede durur. Var olan bir dosyada çalışmak için KULLANMA; yalnızca yeni dosya açılışında.
---

# Dosya açma

## Sıra kesindir
1. **Çıkar çatışması kontrolü.** `hafiza/cikar-catismasi.md` karşı taraflar için
   okunur. Dosya bu adımdan önce açılmaz. Bir eşleşme uyarı değil DURMA
   sebebidir (işletim sözleşmesi §8).
   Dosya yoksa: bu bir "temiz" sonucu değildir. "Çatışma listesi yok, kontrol
   yapılamadı" yazılır ve insana sorulur.
2. **Klasör.** `dosyalar/<ad>/` altında `veri/`, `cikti/`, `KAPSAM.md`.
3. **Kapsam notu.** Kim müvekkil, hangi taraf, ne yapılacak, ne yapılmayacak,
   hangi birimler devrede, kim onaylar.
4. **İlk yaptırım taraması** — soyutlama kuralıyla (`yaptirim-taramasi`).
5. **Şirket türü ve halka açıklık** tespiti; hangi el kitabının geçerli olduğu.

## KAPSAM.md şablonu
    # <dosya adı> · kapsam notu
    Açılış tarihi:
    Müvekkil ve taraf:
    Karşı taraflar (çatışma kontrolü yapılan):
    Çatışma kontrolü sonucu ve tarihi:
    İşin tanımı:
    Kapsam dışı:
    Devredeki birimler:
    İnsan onayı verecek kişi:

## Çıktı
Açılan klasör, kapsam notu ve çatışma kontrolünün sonucu.
Şununla bitir: Şimdi ne yapılmalı / Yetkili avukat görüşü gereken konular /
Kontrol edildi:
