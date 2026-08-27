# Türkiye'de birleşme denetimi — bildirim eşikleri

Dayanak: 2010/4 sayılı Rekabet Kurulundan İzin Alınması Gereken Birleşme ve
Devralmalar Hakkında Tebliğ'i değiştiren 2026/2 sayılı Tebliğ.
Resmî Gazete: 11 Şubat 2026, sayı 33165. Yürürlük: 11 Şubat 2026.
Doğrulama: 2026-08-27.

Kontrol edildi: 2026/2 sayılı Tebliğ üzerine yayımlanmış uygulamacı
çözümlemeleri, web araması (2026-08-27) · bulunamayan: Resmî Gazete ve
rekabet.gov.tr birincil metni — bu kurulumun ağ çıkışı bu alan adlarını
engelliyor; madde metni birincil kaynaktan TEYİT EDİLMEDİ.

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

## Bekletici etki

4054 sayılı Kanun, madde 11: bildirime tabi bir işlem, Kurul açıkça ya da
inceleme süresinin dolmasıyla zımnen karar vermeden hukuken geçerlilik
kazanmaz. İmza serbesttir; kapanış değildir.

Yabancı bir alıcı için Türk işlem pratiğindeki en sonuçlu cümle budur, çünkü
gönüllü bildirim rejimi olan ülkelerden taşınan sezgiden daha katıdır.

## İzinsiz kapanışın yaptırımı

4054 sayılı Kanun, madde 16: bildirimde bulunmama hâlinde yıllık gayrisafi
gelirin **binde biri** oranında idari para cezası. Yerinde incelemenin
engellenmesi **binde beş**.

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
