# sinir-otesi · SPA mimarisi ve işlemin kurulduğu katman

## Buraya ne yönlenir
Yapı kararları: pay mı varlık mı, uygulanacak hukuk, uyuşmazlık merci, bedelin
yapısı, başvuru paketi (emanet / W&I / satıcı taahhüdü). İşlem el kitapları da
burada.

## Yöntem dosyaları
- `yontem/mimari.md` — geri kalan her şeyi belirleyen beş karar, W&I, açıklama
  mektubu, kapanış öncesi koşul sırası.
- `yontem/elkitabi-alici.md` — yabancı alıcı, Türk hedef; aşama aşama.
- `yontem/elkitabi-satici.md` — satıcı tarafı, ters yönde.

## Buraya yönlenmeyen
- Türk emredici kurallarının içeriği → `birimler/tr-*/`
- Kapanış sonrası talep ve tahkim duruşu → `birimler/uyusmazlik/`

## Neden ayrı birim
İşlemin asıl yaşadığı yer burasıdır. Türkiye katmanı Türkiye'nin ne istediğini
söyler; bu katman işlemin nasıl kurulduğunu söyler ve ikisi aynı dosyada
karışırsa hangi kuralın bertaraf edilebilir olduğu bulanıklaşır.

## Yetkili avukat görüşü gereken konular
Uygulanacak hukuk ve merci seçimi, başvuru paketi ve SPA'nın bertaraf
edemeyeceği her Türk emredici kuralı.
