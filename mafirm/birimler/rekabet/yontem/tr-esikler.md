# Türkiye'de birleşme denetimi — bildirim eşikleri

Dayanak: 2010/4 sayılı Rekabet Kurulundan İzin Alınması Gereken Birleşme ve
Devralmalar Hakkında Tebliğ'i değiştiren 2026/2 sayılı Tebliğ.
Resmî Gazete: 11 Şubat 2026, sayı 33165. Yürürlük: 11 Şubat 2026.
Doğrulama: 2026-08-27.

Kontrol edildi: 2026/2 sayılı Tebliğ üzerine yayımlanmış uygulamacı
çözümlemeleri, web araması (2026-08-27) · 4054 sayılı Kanun m.10, m.11 ve m.16
ile 2010/4 sayılı Tebliğ m.10 üzerine uygulamacı çözümlemeleri ve Rekabet
Kurumu idari para cezaları sayfasına yapılan atıflar (2026-08-27) · 2026/1
sayılı Tebliğ ile belirlenen idari para cezası alt sınırı (2026-08-27) ·
bulunamayan: Resmî Gazete, mevzuat.gov.tr ve rekabet.gov.tr birincil metinleri
— bu kurulumun ağ çıkışı bu alan adlarını engelliyor; madde metni BİRİNCİL
KAYNAKTAN OKUNMADI, ikincil kaynaklardan çapraz doğrulandı.

## İki alternatif eşik

İşlem, iki eşikten HERHANGİ BİRİNİ aşıyorsa bildirime tabidir.

**A eşiği — yurt içi**
- işlem taraflarının Türkiye ciroları toplamının **3.000.000.000 TL**'yi
  aşması, VE
- işlem taraflarından **en az ikisinin** Türkiye cirolarının **ayrı ayrı
  1.000.000.000 TL**'yi aşması

**B eşiği — devre konu varlık**
- devralma işlemlerinde devre konu varlık ya da faaliyetin, birleşme
  işlemlerinde ise taraflardan en az birinin Türkiye cirosunun
  **1.000.000.000 TL**'yi aşması, VE
- diğer işlem taraflarından en az birinin dünya cirosunun
  **9.000.000.000 TL**'yi aşması

## Teknoloji teşebbüsü istisnası

Aynı dayanak: 2026/2 sayılı Tebliğ, doğrulama 2026-08-27.

**Uygulama alanı iki ayaklıdır:**
- **Devralma** işlemlerinde: **devralınan** teşebbüs Türkiye'de yerleşik bir
  teknoloji teşebbüsü ise,
- **Birleşme** işlemlerinde: işlem taraflarından **en az biri** Türkiye'de
  yerleşik bir teknoloji teşebbüsü ise,

devre konu taraf bakımından aranan **1.000.000.000 TL** Türkiye cirosu eşiği
yerine **250.000.000 TL** uygulanır.

**Teknoloji teşebbüsü** tanımı: dijital platformlar, yazılım ve oyun yazılımı,
finansal teknolojiler, biyoteknoloji, farmakoloji, tarım kimyasalları ve sağlık
teknolojileri alanlarında faaliyet gösteren teşebbüsler.

**Ciro hesabı dar tutulur.** 250.000.000 TL eşiğinin karşılanıp karşılanmadığı
değerlendirilirken, teşebbüsün yalnızca yukarıda sayılan alanlardaki
faaliyetlerinden elde ettiği ciro dikkate alınır. Birden fazla alanda faaliyeti
olan bir teşebbüsün toplam cirosu değil, yalnızca ilgili faaliyet cirosu
sayılır. Bu, uygulamada eşiği düşürmez — daraltır.

## Bu dosyanın kitaptan ayrıldığı üç nokta

Kurulum kitabı §5.1 bu istisnayı üç noktada eksik anlatıyor. Ayrım
işaretlenmiştir, çünkü kitabın kendi güncellik kuralı bunu emreder:

1. **"Türkiye'de yerleşik" ile "Türkiye'de faaliyet gösteren" aynı şey
   değildir.** 2026/2, istisnayı Türkiye'de **yerleşik** teşebbüslerle
   sınırladı. Kitaptaki "Türkiye'de faaliyet gösteren ya da araştırma
   geliştirme yürüten" ifadesi önceki rejimin daha geniş tanımıdır ve şimdi
   fazla kapsayıcıdır — yani gereksiz bildirim üretir.
2. **Birleşme ayağı kitapta yok.** Kitap istisnayı yalnızca hedefe bağlıyor.
   Birleşme işlemlerinde taraflardan herhangi birinin Türkiye'de yerleşik
   teknoloji teşebbüsü olması yeter.
3. **Ciro hesabının darlığı kitapta yok.** 250.000.000 TL, teşebbüsün toplam
   cirosuyla değil yalnızca sayılan teknoloji alanlarındaki cirosuyla ölçülür.

Bu üç ayrım `kod/esik.py` içinde uygulanmıştır ve orada da işaretlidir.

## Bekletici etki — doğru madde numarası

**2010/4 sayılı Tebliğ, madde 10**: izne tabi bir birleşme veya devralma
işlemi, açıkça veya zımnen bir karar verilmeden önce **hukuki geçerlilik
kazanamaz**. Bu hüküm bekletici şart (suspensif koşul) niteliğindedir.

**4054 sayılı Kanun, madde 10** mekaniği kurar:
- Bildirimden itibaren **on beş gün** içinde Kurul ön inceleme yapar.
- İşlemi nihai incelemeye alırsa, işlemin **nihai karara kadar askıda**
  olduğunu ve uygulamaya sokulamayacağını ilgililere tebliğ eder.
- Kurul süresi içinde cevap vermezse, anlaşma bildirim tarihinden **otuz gün**
  sonra yürürlüğe girerek hukuki geçerlilik kazanır (zımni izin).

**4054 sayılı Kanun, madde 11** ise ayrı bir hâli düzenler: bildirilmesi
zorunlu bir işlemin Kurula **hiç bildirilmemesi** ya da işlem
gerçekleştirildikten **sonra** bildirilmesi. Bu hâlde Kurul işlemi
kendiliğinden incelemeye alır.

> **Kitap ve bu dosyanın ilk sürümü bekletici etkiyi madde 11'e bağlıyordu.
> Yanlıştı.** Bekletici şart Tebliğ m.10 ve Kanun m.10'dadır; m.11 hiç
> bildirilmemiş işlemin sonucudur. Ayrım pratikte önemlidir: bildirim yapılmış
> ama izinden önce kapatılmış bir işlem m.10'u, hiç bildirilmemiş bir işlem
> m.11'i ilgilendirir.

Yabancı bir alıcı için Türk işlem pratiğindeki en sonuçlu cümle budur, çünkü
gönüllü bildirim rejimi olan ülkelerden taşınan sezgiden daha katıdır.

## İzinsiz kapanışın yaptırımı

4054 sayılı Kanun, madde 16:

| Fiil | Oran |
|---|---|
| İzne tabi işlemin **Kurul izni olmaksızın gerçekleştirilmesi** | yıllık gayrisafi gelirin **binde biri** |
| Eksik, yanlış ya da yanıltıcı bilgi verilmesi; bilginin süresinde verilmemesi | **binde biri** |
| **Yerinde incelemenin engellenmesi ya da zorlaştırılması** | **binde beşi** |

**Alt sınır — bu rakam her yıl güncellenir.** Kanun metni "on bin Türk
Lirasından az olamaz" der; tutar her yıl yeniden değerleme oranıyla artırılır.
**2026/1 sayılı Tebliğ ile 1 Ocak 2026'dan itibaren 302.484,86 TL.**
Doğrulama: 2026-08-27. Bu tutar takvim yılı başında değişir; Ocak ayında
yeniden çekilmelidir.

**Cezayı kim öder:** birleşme işlemlerinde tarafların **her birine**, devralma
işlemlerinde ise **sadece devralana** verilir. Kitapta bu ayrım yoktu ve alıcı
tarafı için doğrudan sonucu vardır.

Ceza ciro üzerinden hesaplanır, işlem değeri üzerinden değil. Yani küçük bir
devralma için ölçeklenmez: Türkiye cirosu 40 milyar TL olan bir grubun erken
kapattığı 4 milyon avroluk bir eklenti alımı, işlemin büyüklüğüyle ilgisi
olmayan bir ceza üretir.

## SPA'da neyi değiştirir

- Kapanış Kurul iznine bağlanır ve bu koşuldan feragat edilemez.
- Kapanış öncesi hiçbir bütünleşme, ortak fiyatlandırma, ortak müşteri
  görüşmesi yapılmaz.
- Ara dönem taahhütleri değer koruma olarak yazılır, kontrol olarak değil.
- Nihai tarih yalnızca birinci aşamayı değil, ikinci aşamayı da karşılamalıdır.

## Şimdi ne yapılmalı

`kod/esik.py` gerçek ciro rakamlarıyla çalıştırılır. Teknoloji ayağı
düşünülüyorsa önce iki olgu tespit edilir: teşebbüs Türkiye'de yerleşik mi ve
sayılan alanlardaki cirosu ne kadar.

## Yetkili avukat görüşü gereken konular

Bu dosyadaki her rakamın birincil metinden teyidi; "Türkiye'de yerleşik"
niteliğinin somut olayda karşılanıp karşılanmadığı; teknoloji faaliyeti
cirosunun ayrıştırılması; ve bildirime tabi olmadığı sonucuna varılan her
işlem — olumsuz iddia kuralı gereği bu, olumlu sonuçtan daha yüksek kanıt ister.
