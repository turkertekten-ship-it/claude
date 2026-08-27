# İşçi devri ve kıdem yükü

Dayanak: 4857 sayılı İş Kanunu madde 6; 1475 sayılı Kanun madde 14 (kıdem
tazminatı, yürürlükteki hükmü); 6356 sayılı Sendikalar ve Toplu İş Sözleşmesi
Kanunu.
Doğrulama: 2026-08-27.

## Neden bu birim ayrı

Yabancı alıcı kıdem tazminatı yükünü bir muhasebe karşılığı sanır. Türkiye'de
bu, işyeri devriyle birlikte geçen ve belirli bir süre devreden ile devralanı
birlikte sorumlu tutan bir yüktür. Fiyat modeline karşılık olarak değil,
devralınan bir borç olarak girer.

## Pay devri ile varlık devri arasındaki fark

- **Pay devri**: işveren tüzel kişiliği değişmez. İş sözleşmeleri aynen devam
  eder; kıdem kesintisiz işler. Görünürde hiçbir şey olmaz, bu yüzden gözden
  kaçar.
- **Varlık devri**: işyeri devri hükümleri devreye girer. İş sözleşmeleri
  devralana geçer, işçinin kıdemi devreden nezdinde geçen süreyi de kapsar ve
  devir tek başına haklı fesih sebebi değildir.

## Modellenmesi gereken kalemler

1. Kıdem tazminatı yükü — her işçi için kıdem süresi × giydirilmiş ücret, tavan
   uygulanarak. Tavan yılda iki kez güncellenir; kullanılan tavanın tarihi
   yazılır.
2. İhbar tazminatı ve yıllık izin karşılığı.
3. Toplu iş sözleşmesi varsa: TİS'in devirden nasıl etkilendiği ve süresi.
4. Kayıt dışı istihdam ve eksik SGK bildirimi maruziyeti — geçmişe dönük ve
   sınırlanması güç.
5. Kontrol değişikliği primleri ve yönetici hizmet sözleşmeleri — bunlar SPA
   tarafındadır (`birimler/sinir-otesi/`), burada yalnızca işaretlenir.

## SPA'da neyi değiştirir

- Kıdem yükü fiyattan düşülür ya da kapanış hesaplarında bir düzeltme kalemi
  olur; ikisi birden değil.
- Kayıt dışı istihdam bir özel tazminat kalemidir, beyan değil.
- Varlık devrinde işçi listesi bir kapanış belgesidir.

## Yetkili avukat görüşü gereken konular

Kıdem yükü hesabının kendisi, devrin işyeri devri sayılıp sayılmayacağı, her
toplu iş sözleşmesi analizi ve kullanılan kıdem tavanının güncelliği.
