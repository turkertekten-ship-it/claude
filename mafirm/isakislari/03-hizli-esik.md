# Hızlı eşik iş akışı — bu işlem yapılabilir mi, izin gerekiyor mu

Doğrulama: 2026-08-27.

Kontrol edildi: `birimler/rekabet/yontem/tr-esikler.md` (2010/4 sayılı Tebliğ'in
2026/2 ile değişik hâli, RG 11.02.2026 sayı 33165) · `birimler/rekabet/kod/esik.py`
başlığındaki rakamlar ve `--self-test` vakaları · `.claude/skills/rekabet-esigi/SKILL.md` ·
`hafiza/cikar-catismasi.md` (2026-08-27) · bulunamayan: rekabet.gov.tr ve Resmî
Gazete birincil metni — bu kurulumun ağ çıkışı bu alan adlarını engelliyor;
eşik rakamları BİRİNCİL KAYNAKTAN TEYİT EDİLMEDİ. Ayrıca bulunamayan: Rekabet
Kurulu'nun bugünkü fiilî birinci ve ikinci aşama süreleri.

## Ne zaman bu iş akışı

Soru henüz bir dosya değilken çalıştırılır: telefonda, ilk toplantıda ya da bir
teklif mektubu hazırlanırken sorulan "bu işlem Türkiye'de izne tabi mi, kapanışı
ne kadar geciktirir" sorusu. Altı adımdır ve tek bir çıktısı vardır: **git /
gitme** kararıyla birlikte, dayanılan eşiklerin doğrulama tarihi. Bu akış tam
inceleme yapmaz, yapı kurmaz, sözleşme okumaz; yalnızca işlemin bildirime tabi
olup olmadığını ve bekletici etkinin takvimi nasıl kırdığını söyler. Cevabı
`01-alici-tarafi.md` adım 6'ya ya da `02-satici-tarafi.md` adım 7'ye **aynen**
girer; oradan yeniden hesaplanmaz — ama doğrulama tarihi altı aydan eskiyse
yeniden çekilir (§3).

## Adımlar

| # | Adım | Ne çalıştırılır | Çıktı nereye | Geçilemeyen kapı |
|---|---|---|---|---|
| 1 | Çıkar çatışması ön kontrolü — soru cevaplanmadan önce | `hafiza/cikar-catismasi.md` taraflar için okunur (dosya açılacaksa `/dosya-ac <dosya adı>`, beceri: `dosya-ac`) | `dosyalar/<dosya>/kapsam.md`, dosya yoksa `cikti/hizli-esik-<tarih>.md` başına not | Eşleşme varsa **DUR**: soru cevaplanmaz, rakam istenmez. Hızlı olması bu kapıyı kaldırmaz (§8) |
| 2 | Eşiğin gerektirdiği altı olgunun toplanması | Beceri: `rekabet-esigi`; toplanan olgular: (a) işlem **devralma** mı **birleşme** mi, (b) tarafların ayrı ayrı Türkiye ciroları, (c) devre konu varlık ya da faaliyetin Türkiye cirosu, (d) diğer taraflardan birinin dünya cirosu, (e) devralınan taraf Türkiye'de **yerleşik** bir teknoloji teşebbüsü mü, (f) öyleyse yalnızca teknoloji **alanındaki** cirosu | `cikti/hizli-esik-<tarih>.md` | Tahmin edilen her ciro rakamı **tahmin olduğu yazılarak** girilir. Hangi rakamın cevabı çevireceği yazılmadan hesaba geçilmez |
| 3 | Kodun sınanması ve gerçek rakamlarla hesap | `python3 ~/mafirm/birimler/rekabet/kod/esik.py --self-test`, ardından gerçek rakamlarla `bildirilmeli(tr_cirolar, hedef_tr, diger_dunya_cirolari, teknoloji, islem_turu, yerlesik, teknoloji_alan_cirosu)` | `cikti/hizli-esik-<tarih>.md` | `--self-test` HATA dönerse hesap yapılmaz. **Eşik hafızadan cevaplanmaz** — A eşiği (yurt içi) ve B eşiği (devre konu) düzyazıda akıl yürütülerek çözülmez |
| 4 | Teknoloji istisnasının gerçekten uygulanıp uygulanmadığı | `birimler/rekabet/yontem/tr-esikler.md` "Teknoloji teşebbüsü istisnası"; üç olgu ayrı ayrı doğrulanır: Türkiye'de **yerleşiklik** (faaliyet göstermek yetmez) · devralmada devralınan taraf / birleşmede taraflardan herhangi biri · 250.000.000 TL testinin **alan cirosuyla** yapılması | `cikti/hizli-esik-<tarih>.md` | Yerleşiklik olgusu yoksa istisna yoktur ve 1.000.000.000 TL eşiği geri gelir. Toplam ciroyla yapılan 250.000.000 TL testi yanlıştır ve gereksiz bildirim üretir |
| 5 | Bekletici etkinin ve cezanın takvime çevrilmesi | `birimler/rekabet/yontem/tr-esikler.md` "Bekletici etki" ve "İzinsiz kapanışın yaptırımı"; nihai tarih birinci **ve** ikinci aşamaya karşı sınanır | `cikti/hizli-esik-<tarih>.md` | Bildirime tabi bir işlemde **imza serbest, kapanış değildir** (4054 m.10, Tebliğ m.10). Ceza (m.16) işlem değeri üzerinden değil yıllık gayrisafi gelir üzerinden hesaplanır; küçük bir eklenti alımı için ölçeklenmez ve bu, cevaba yazılmadan geçilmez |
| 6 | Git / gitme kararının yazılması | Beceri: `rekabet-esigi` cevap biçimi (bildirime tabi mi · dayanılan rakamlar · eşiklerin doğrulama tarihi · her iki yönde yanılmanın sonucu); karara götürülecekse `/kurul-notu` | `cikti/hizli-esik-<tarih>.md`, dosya açıldıysa `dosyalar/<dosya>/cikti/esik-<tarih>.md` | Cevap, kullanılan eşiklerin **doğrulama tarihini** taşımadan verilmez. "Bildirim gerekmez" sonucu, hangi hükmün arandığı ve neden bulunamadığı gösterilmeden yazılmaz (olumsuz iddia kuralı, §2) |

## Çıktının taşıması gereken beş satır

1. **Bildirime tabi mi:** evet / hayır / belirlenemiyor — ve hangi ayak (A eşiği,
   B eşiği, her ikisi, hiçbiri).
2. **Dayanılan rakamlar**, her biri nereden geldiğiyle ve tahminse tahmin olduğu
   yazılarak.
3. **Kullanılan eşiklerin doğrulama tarihi** ve dayanağı (2026/2 sayılı Tebliğ,
   RG 11.02.2026 sayı 33165 — bu kurulumda birincil metinden teyit edilmedi).
4. **Her iki yönde yanılmanın sonucu:** gereksiz bildirim haftalara mal olur;
   gereken bildirimin yapılmaması kapanışı hukuken geçersiz kılar.
5. **Git / gitme** ve bunun bir eşik cevabı olduğu, işlemin tamamına ilişkin bir
   görüş olmadığı.

## Duran noktalar

Karar, adı `dosyalar/<dosya>/kapsam.md` içinde gerçek adıyla yazılı olan kişiye
gider; dosya henüz açılmamışsa soruyu alan sorumlu ortak.

| Duran nokta | Adım | Ne olur | Kim karar verir |
|---|---|---|---|
| **Çıkar çatışması eşleşmesi** | 1 | Soru cevaplanmaz, ciro rakamı istenmez, tarafla temas kurulmaz. Sorunun kısa olması kapıyı kaldırmaz | Dosya sorumlusu ortak |
| **Giderilemeyen yaptırım eşleşmesi** | 1-2 | Eşik sorusu çalışılırken bir taraf hakkında yaptırım şüphesi doğarsa akış `/tara` ile `01`/`02` akışının 2. adımına devredilir ve orada durur | Uyum sorumlusu ile dosya sorumlusu ortak |
| **`--self-test` HATA dönmesi** | 3 | Hesap yapılmaz, rakam verilmez. Kod bozuksa cevap kodun verdiği güveni taşıyamaz | Sistemi kuran sorumlu; `/denetim` çalıştırılır |
| **Eşiklerin doğrulama tarihinin altı aydan eski olması** | 3, 6 | Rakam kullanılmadan önce yeniden çekilir. Eskimiş bir eşik, hiç olmamasından kötüdür: kontrol edilmiş gibi durur (§3) | `/esik-denetle` çalıştırılır; eşik değişikliğini dosyaya işleyecek olan insan karar verir |
| **Rekabet izni alınmadan kapanış** | 5 | Bildirime tabi çıkan bir işlemde kapanış izne bağlanır; bu koşuldan feragat edilemez (4054 m.10, Tebliğ m.10) | Hiç kimse "evet" diyemez. Karar Rekabet Kurulu'nundur |
| **Ciro rakamlarının tahmin olması** | 2, 6 | Sonuç "belirlenemiyor" olarak verilir ve hangi rakamın cevabı çevireceği yazılır. Tahmine dayalı sonuç kesin gibi sunulmaz | Dosya sorumlusu ortak; gerçek rakam gelene kadar karar ertelenir |
| **Türk şekil şartının karşılanmaması** | — | Bu akışın kapsamı dışındadır ve öyle olduğu yazılır. Eşik cevabı, devrin hukuken gerçekleşeceğini söylemez; onu `01`/`02` akışlarının kapanış adımı söyler | Kapanışı yürüten Türk hukukçusu |

## Şimdi ne yapılmalı

Adım 3 çalıştırılmadan hiçbir eşik cevabı verilmez; bu akışın var olma sebebi
odur. Cevap verildikten sonra, işlem ilerleyecekse `/dosya-ac` ile dosya açılır
ve çıktı `01-alici-tarafi.md` adım 6'ya (ya da satıcı tarafındaysa
`02-satici-tarafi.md` adım 7'ye) taşınır. Eşik sonucu "belirlenemiyor" ise
eksik rakam adıyla listelenir ve kimden isteneceği yazılır.

## Yetkili avukat görüşü gereken konular

Bu dosyada kullanılan her eşik rakamının birincil mevzuat metninden teyidi ·
"Türkiye'de yerleşik" niteliğinin somut olayda karşılanıp karşılanmadığı ·
teknoloji faaliyeti cirosunun toplam cirodan ayrıştırılması · ciro hesabında
hangi grup şirketlerinin taraf sayılacağı · bildirime tabi **olmadığı** sonucuna
varılan her işlem (olumsuz iddia kuralı, §2) · ve bekletici etkinin somut
takvime ve nihai tarihe uygulanması.
