# Çıkar çatışması kaydı

Doğrulama: 2026-08-27.

Kontrol edildi: işletim sözleşmesi §8 ve `/dosya-ac` komutunun birinci adımı
(2026-08-27) · bulunamayan: bu kurulumda kayda işlenmiş gerçek bir taraf —
tablo bilerek boştur.

## Bu dosya ne kadar iyiyse tarama o kadar iyidir

Bu kayıt bir veri tabanı değil, insanların yazdığı bir listedir. **İçine
yazılmamış bir ilişkiyi tespit edemez.** Açıklanmamış bir hissedarlık, sözlü
bir yönlendirme ücreti, bir ortağın eşinin yönetim kurulu üyeliği ya da geçmiş
bir dosyada yalnızca telefonda konuşulmuş bir taraf burada görünmez; bu dosyaya
bakıp "çatışma yok" demek, yalnızca **bu dosyaya yazılanlar arasında** çatışma
olmadığını söyler. Çıktı bunu bu kelimelerle yazar.

Bundan çıkan iki iş kuralı:

1. **Boş dönen bir arama olumsuz bir iddia değildir.** İşletim sözleşmesi §2
   gereği "çatışma yok" cümlesi tek başına yazılmaz; "kayıtta eşleşme
   bulunmadı, kayıt şu tarihe kadar günceldir, şu taraflar arandı" yazılır.
2. **Her kapanan dosya buraya geri yazılır.** Kaydı besleyen tek şey budur.
   Yazılmayan taraf, bir sonraki dosyada görünmez.

## Eşleşme bir uyarı değil, durma sebebidir

Bir eşleşme bulunduğunda iş akışı **durur**: klasör açılmaz, gizlilik
sözleşmesi imzalanmaz, belge istenmez, karşı tarafla temas kurulmaz. Devam
kararını makine değil, adı `kapsam.md` içinde yazılı olan dosya sorumlusu
ortak verir ve kararını gerekçesiyle buraya işler.

Eşleşme "muhtemelen sorun değil" diye geçilmez. Bir çatışmanın maliyeti, geç
fark edildiğinde dosyanın tamamının bırakılmasıdır.

## Ne aranır

Karşı taraf adının kendisi yetmez. Aranan asgari küme: hedef şirket · ana
ortaklar ve gerçek lehtarlar · yönetim kurulu üyeleri · grup şirketleri ve
iştirakler · finansmanı verenler · karşı tarafın avukatları. Türkçe adların
harf çevirisi farkları (Şükrü / Sukru / Shukru) elle aramayı yanıltır; ad
taramasında `birimler/_araclar/kod/tarama.py` mantığı burada da geçerlidir.

## Kayıt

| Taraf | Rol | Dosya | Tarih | Not |
|---|---|---|---|---|
| ÖRNEK SATIR — SİLİNECEK · Örnek Sanayi A.Ş. | karşı taraf (satıcı) | ÖRNEK-2026-000 | 2026-08-27 | Bu satır biçimi göstermek için konmuştur, gerçek bir taraf değildir. Kayda ilk gerçek satır yazılırken silinir. |

Sütunların anlamı: **Taraf** tam hukuki unvan (kısaltma değil) · **Rol** bu
dosyadaki konumu (müvekkil / karşı taraf / hedef / gerçek lehtar / finansman /
karşı tarafın avukatı) · **Dosya** iç dosya numarası · **Tarih** kaydın
işlendiği gün · **Not** çatışmayı doğuran ya da doğurmayan olgunun kendisi.

## Şimdi ne yapılmalı

Her yeni dosyada `/dosya-ac` çalıştırılır; birinci adım bu dosyayı okur.
Kapanan her dosyanın tarafları, `04-kapanis-sonrasi.md` iş akışının son
adımında buraya yazılır. Örnek satır, ilk gerçek kayıtla birlikte silinir.

## Yetkili avukat görüşü gereken konular

Bir eşleşmenin gerçekten çatışma oluşturup oluşturmadığı; bilgi duvarının
yeterli olup olmadığı; feragat istenip istenmeyeceği ve kimden isteneceği; ve
kaydın kapsamının bu büronun tüm ilişkilerini gerçekten yansıtıp yansıtmadığı.
