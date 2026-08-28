# Araç kataloğu — §13'ün kararları, kurulumda

> **Doğrulama: 2026-08-28 · Bozulma sınıfı: ALTI AY**
>
> §3'ün kuralı. Ama dikkat: bu dosyadaki alanlar altı ayda BİR BOZULMAZ —
> arşiv durumu bir günde değişebilir, lisans bir sürümde. Altı ay, ötesinde
> dayanılmaması gereken ÜST SINIRDIR, tazeliğin garantisi değil.

[AP-01 · otuz dördüncü tur] Kitabın §13'ü altı deposu için lisans, yıldız,
son güncelleme ve bir **Karar** yazıyor — ama bu tablo kurulumda hiçbir dosya
bırakmıyordu. §2 klasörleri kuruyor (`birimler`, `emsal`, `hafiza`,
`dosyalar`, `cikti`) ve hiçbiri araç kataloğu için değil. Sonuç: kurulumu
yapan hukukçunun elinde hangi aracın incelendiğine dair yerel bir kayıt,
eskiyecek bir doğrulama tarihi ve §16'nın bakabileceği bir şey yoktu.
Karar yalnızca kitapta yaşıyordu; kararın dayandığı olgular ise bozuluyor.

**İki sütun kitapta hiç yok ve ikisi de karar değiştiriyor:** deponun
ARŞİVLENMİŞ olup olmadığı, ve VERİ lisansının kod lisansından farklı olup
olmadığı.

## Katalog

| Depo | Kod lisansı | Veri lisansı | Arşiv | Bizim doğrulamamız | Karar |
|---|---|---|---|---|---|
| `google/diff-match-patch` | Apache-2.0 | — | **ARŞİVLENDİ 2024-08-05** | 2026-08-28 · depo sayfası | Kullan — ama kitabın "eskime bozulma değildir" gerekçesi arşiv olgusunu bilmeden yazıldı; salt okunur bir depo hata düzeltmesi almaz |
| `LexPredict/lexpredict-lexnlp` | AGPL-3.0 | — | doğrulanmadı | **doğrulanmadı** (kitap beyanı: 2024-05-27) | Lisans kararı verilmeden kurulmaz — copyleft, ticari yığın |
| `ICLRandD/Blackstone` | Apache-2.0 | — | doğrulanmadı | **doğrulanmadı** (kitap beyanı: 2024-07-16) | Yöntemi için okunur; bağımlılık değil |
| `freelawproject/courtlistener` | AGPL-3.0 | — | arşivlenmemiş | 2026-08-28 · deponun README'si | AGPL: ticari pratikte lisans kararı gerekir. Kitap "açık (depoya bakın)" diyordu; bakıldı |
| `opensanctions/opensanctions` | MIT | **CC BY-NC 4.0 — ticari kullanım YASAK** | arşivlenmemiş | 2026-08-28 · depo | **Çelişki:** kitap bu aracı ticari bir hukuk pratiği için öneriyor; verisi ticari kullanıma kapalı. İnsan kararı gerekir (§9) |
| `opensanctions/nomenklatura` | — | — | doğrulanmadı | **doğrulanmadı** | Kitap §13.3'te öneriyor; lisans ve veri durumu ayrıca doğrulanmalı |

## Bu kataloğun kuralı

1. Her satır **bizim** doğrulama tarihimizi taşır. Kitabın beyan ettiği tarih
   bizim doğrulamamız değildir ve öyle yazılmaz.
2. Doğrulanmamış bir satır "temiz" değildir — **kontrol edilmedi** demektir.
   §14'ün ikinci tuzağı: boş arama yokluğun kanıtı değildir.
3. Altı aydan eski bir doğrulama bayattır (§3). Tazelemek için
   `once-arastir` becerisini kullan; **beş** alanı da oku: lisans, yıldız,
   son güncelleme, **arşiv durumu** ve **veri lisansı**.
4. Bir satırı değiştirmek bir araç kararını değiştirebilir. Kararı değiştiren
   her değişiklik §9 uyarınca insana sorulur; bu dosya kendiliğinden
   düzenlenmez.
