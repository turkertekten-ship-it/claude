---
description: Yeni bir dosya açar: çıkar çatışması kontrolü, klasör, kapsam notu ve sorumluluk kayıtları. Çatışma kontrolü açılışın önkoşuludur.
---

`$ARGUMENTS` adıyla yeni bir dosya aç.

<!-- [AO-02/AO-03 · otuz üçüncü tur] Kitaba sadık sürüm
     yamalar/kitaba-sadik/dosya-ac-komut.md. İki bağ eklendi.
     YÖN: kitabın adımı yalnızca "verilen KARŞI TARAF adlarını ara" diyordu.
     Çatışma simetrik bir ilişkidir ve en ağır hâli tersidir: yeni dosyanın
     MÜVEKKİLİ, açık bir dosyanın KARŞI TARAFI olabilir — yani şu anda
     aleyhine çalıştığımız kişi için çalışmaya başlarız. Kayıt biçimi
     `<taraf adı> · <dosya> · <hangi tarafta> · <tarih>` bu soruyu
     cevaplayacak veriyi zaten taşıyordu; sorulmuyordu.
     ZAMAN: kontrol açılış anına bağlıydı. Kayda sonradan bir ad girdiğinde
     çatışma o an doğar ve hiçbir şey geriye bakmıyordu.
     SINIR: bu yama neyin çatışma SAYILDIĞINA karar vermez — o bir meslek
     kuralları meselesidir ve §9 uyarınca insana aittir. Yalnızca mekanik
     kontrolün iki yönü de kapsamasını sağlar. -->

1. **Önce çıkar çatışması — İKİ YÖNLÜ.** `hafiza/cikar-catismasi.md` dosyasını
   oku ve **iki aramayı da** yap:
   - verilen **karşı taraf** adlarını kayıtta ara;
   - verilen **müvekkil** adını da kayıtta ara — kayıtta *karşı taraf* olarak
     geçiyorsa bu, aleyhine çalıştığımız kişi için çalışmaya başlamak demektir
     ve en ağır çatışma hâlidir.

   Dosya yoksa bu bir "temiz" sonucu DEĞİLDİR: "çatışma listesi yok, kontrol
   yapılamadı" yaz ve insana sor. Eşleşme varsa —hangi yönde olursa olsun— DUR.
2. `dosyalar/$ARGUMENTS/{veri,cikti}` klasörlerini oluştur.
3. `dosyalar/$ARGUMENTS/KAPSAM.md` yaz: açılış tarihi, müvekkil ve taraf, karşı
   taraflar, çatışma kontrolü sonucu ve tarihi, işin tanımı, kapsam dışı,
   devredeki birimler, insan onayı verecek kişi.
4. Şirket türü ve halka açıklık tespitini kapsam notuna yaz; hangi el kitabının
   geçerli olduğunu belirt.

5. **Kayda yazdıktan sonra geriye bak.** Yeni tarafları kayda işledikten
   sonra, `dosyalar/*/KAPSAM.md` altındaki **açık dosyaların** müvekkil ve
   karşı taraf satırlarını bu yeni adlara karşı —yine iki yönlü— tara. Bir
   çatışma açılış anında doğmayabilir; kayda sonradan giren bir ad onu o an
   doğurur. **Hiçbir dosyayı düzenleme**; bulduğunu bildir ve insana sor —
   bir dosyayı kapatmak §9 uyarınca insan kararıdır.

   **Bu tarama makinede kalır.** Satırları müvekkil dosyalarının adlarını
   taşır; kural 6 uyarınca dışarı giden hiçbir çağrıya konmaz.

Şununla bitir: Şimdi ne yapılmalı / Yetkili avukat görüşü gereken konular /
Kontrol edildi:
