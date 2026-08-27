# İş akışları — ne oldukları ve kapı kuralı

Doğrulama: 2026-08-27.

Kontrol edildi: işletim sözleşmesi §5, §8 ve §9 · `birimler/sinir-otesi/yontem/`
altındaki alıcı ve satıcı el kitapları · `.claude/skills/`, `.claude/agents/` ve
`.claude/commands/` içindeki gerçek adlar (2026-08-27) · bulunamayan: bu
büronun geçmiş dosyalarından çıkarılmış gerçek süre verisi — aşağıdaki
sıralamalar mantıksal önceliğe dayanır, ölçülmüş takvime değil.

## Bir iş akışı nedir

Bu sistemde üç ayrı şey vardır ve birbirinin yerine geçmezler:

- **Birim** (`birimler/*/yontem/`) *kuralı* tutar: TTK m.595 ne der, eşik kaç
  liradır, kıdem yükü nasıl hesaplanır.
- **Beceri ve komut** (`.claude/skills/`, `.claude/commands/`) *işi* tutar: bir
  SPA nasıl incelenir, bir koşul listesi nasıl kurulur.
- **İş akışı** (bu klasör) *sırayı* tutar: hangi iş hangisinden önce yapılır,
  çıktısı nereye gider ve **nerede durulur**.

İş akışı yeni doktrin üretmez. Var olan birime, beceriye, alt ajana ya da
betiğe **yönlendirir**. Bir iş akışı satırında adı geçen her şey bu makinede
gerçekten kuruludur; olmayan bir araca yönlendiren satır, iş akışının kendisini
değersiz kılar.

## Kapı kuralı — bir iş akışı kapı atlamaz

Her adımın son sütunu **geçilemeyen kapı**dır: o adımı hangi olgunun
durdurduğu. Kural tek cümledir:

> **Kapı, karşılanmadan geçilmez. Aceleyle, ticari baskıyla ya da "sonra
> hallederiz" ile geçilmez.**

Bu, üslup meselesi değil bu pratiğin maliyet yapısıdır. Atlanan kapıların
tamamı aynı biçimde davranır: atlandıkları anda ucuz görünürler ve
faturalarını en pahalı anda keserler.

- Çıkar çatışması kontrolü, dosya açılmadan önce yirmi dakikadır; altı ay sonra
  dosyanın tamamının bırakılmasıdır.
- Gizlilik sözleşmesinden önceki yaptırım taraması bir betik çalıştırmadır;
  imzadan sonra öğrenilmesi, alıcının kendi rejiminde bir uyum olayıdır.
- İzinden önce kapanış, imza tarihinde bir haftalık gecikmeydi; sonrasında
  4054 sayılı Kanun madde 11 uyarınca hukuken geçerlilik kazanmamış bir
  işlemdir ve madde 16 cezası işlem değerine değil grup cirosuna bağlıdır.
- Türk şekil şartı, kapanış gününde bir noter randevusudur; karşılanmadığında
  devir hiç gerçekleşmemiştir.

**Bir kapı yalnızca iki yolla açılır:** kapının aradığı olgu belgeyle
karşılanır, ya da iş akışı **durur** ve adı belli bir insan karar verir
(işletim sözleşmesi §9). Makine kapıyı kendi başına açmaz, "muhtemelen
sorun değildir" demez ve kapıyı uyarıya çevirmez.

Kapının atlandığı hâller de yazılır. Bir kapı bilinçli bir insan kararıyla
geçildiyse, bunu kimin, hangi tarihte ve hangi gerekçeyle yaptığı dosyanın
`cikti/` klasörüne kaydedilir. Sessizce geçilen kapı, hiç olmamış kapıdır.

## Adım tablosunun beş sütunu

| Sütun | Ne yazar |
|---|---|
| **#** | Sıra. Sıra tavsiye değil, bağımlılıktır: sonraki adım öncekinin çıktısını girdi alır. |
| **Adım** | Yapılacak işin adı, tek satırda. |
| **Ne çalıştırılır** | Bu makinedeki gerçek beceri, komut, alt ajan ya da betik yolu. Uydurma ad yazılmaz. |
| **Çıktı nereye** | Sonucun yazılacağı gerçek dosya yolu. Bir yere yazılmayan çıktı yapılmamış sayılır. |
| **Geçilemeyen kapı** | Bu adımı durduran olgu. Kapı yoksa "—" yazılır — boş bırakılmaz. |

"—" ile boş hücre aynı şey değildir. "—" bu adımda kapı olmadığının **tespit
edildiğini** söyler; boş hücre bakılmadığını söyler.

## Duran noktalar

Her iş akışının ayrı bir **Duran noktalar** başlığı vardır: makinenin devam
etmeyeceği, adı belli bir insanın karar vereceği yerler. Dört tanesi bütün
akışlarda ortaktır ve hiçbirinde yumuşatılmaz:

- **Çıkar çatışması eşleşmesi** — `hafiza/cikar-catismasi.md` (§8).
- **Giderilemeyen yaptırım eşleşmesi** — kimlik doğrulaması sonrası hâlâ duran
  eşleşme.
- **Rekabet izni alınmadan kapanış** — 4054 sayılı Kanun madde 11.
- **Türk şekil şartının karşılanmaması** — TTK m.490/499 (A.Ş.), m.595
  (Ltd. Şti.).

"Adı belli insan" gerçek bir addır, bir unvan değil. Her dosyada bu adlar
`dosyalar/<dosya>/kapsam.md` içine yazılır; yazılmamışsa iş akışı orada durur,
çünkü kararı verecek kişi belli değildir.

## Klasördeki dosyalar

| Dosya | Ne zaman |
|---|---|
| `01-alici-tarafi.md` | Yabancı alıcı, Türk hedef. Aşama 0'dan kapanışa. |
| `02-satici-tarafi.md` | Türk satıcı, yabancı alıcı. Süreçten temiz ayrılmaya. |
| `03-hizli-esik.md` | Tek soru: bu işlem yapılabilir mi, izin gerekiyor mu. |
| `04-kapanis-sonrasi.md` | Kapanıştan sonra: tescil, süre, emanet, bütünleşme. |

Uzun akışlar (01 ve 02) hızlı akışı (03) **içerir**; 03 ayrı durur çünkü çoğu
soru daha ilk telefonda gelir ve tam akışı çalıştırmadan cevaplanması gerekir.
03'ün cevabı 01 ya da 02'nin altıncı adımına aynen girer, yeniden hesaplanmaz —
ama doğrulama tarihi altı aydan eskiyse yeniden çekilir (§3).

## Bu dosyaların sınırı

Bir iş akışı hukuki görüş değildir ve olmadığı yerde de öyle davranmaz
(§5). Sıra ve kapı listesidir. Türkiye'de tescil, imza, başvuru ve müvekkile
tavsiye baroya kayıtlı avukat gerektirir; bu klasördeki hiçbir dosya bunu
değiştirmez.

Ayrıca: iş akışındaki her eşik ve süre, kendi birim dosyasından gelir ve orada
bir doğrulama tarihi taşır. İş akışı rakamı **kopyalamaz**, kaynağını gösterir.
Rakamın bayat olup olmadığı `/esik-denetle` ile sorulur.

## Şimdi ne yapılmalı

Yeni bir dosyada önce hangi akışta olunduğu tespit edilir (alıcı / satıcı /
yalnız eşik sorusu), sonra o dosyanın adım tablosu baştan açılır ve satırlar
sırayla kapatılır. Tablo atlanarak değil, satır satır ilerletilir; atlanan
satır "yapılmadı" olarak işaretlenir ve gerekçesi yazılır.

## Yetkili avukat görüşü gereken konular

Bir kapının somut olayda gerçekten karşılanıp karşılanmadığı; bir kapının
insan kararıyla geçilmesinin sonuçları; iş akışının bu dosyaya uygulanabilir
olup olmadığı; ve her akışın kendi başlığında sayılan konular.
