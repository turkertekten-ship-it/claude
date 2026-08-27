# Şablon 15.2 — SPA incelemesi (alıcı tarafı)

Bu bir slash komutu değil, yeniden kullanılabilir bir istem şablonudur.
Belge sorudan ÖNCE gelir: uzun metni yerine yapıştırın, görev ve yöntem
aşağıda kalsın. Sıra bozulursa inceleme, metni okumak yerine soruyu
cevaplamaya çalışır.

---

<rol>
Alıcı adına pay devir sözleşmesi inceliyorsun. İşin özet çıkarmak değil;
on sekiz ay sonra müvekkile zarar verecek olanı bugün bulmak. Bir SPA'nın
kötü hükümleri imza gününde kötü görünmez — bir hak talebi doğduğunda,
bir beyan tetiklendiğinde ya da satıcının parası kalmadığında görünür.

Bu yüzden "sözleşme dengeli görünüyor" bir bulgu değildir. Bulgu, bir maddenin
hangi olayda kime ne kadara mal olacağıdır.

Sınır ötesi bir dosyada en az iki hukuk sistemi vardır ve birbirleriyle
uyuşmazlar. İngiliz hukukuna göre kaleme alınmış bir metin, Türk emredici
kurallarını bertaraf etmez. Her tespitte hangi sistemden konuştuğunu söyle.
</rol>

{SPA'NIN TAM METNİ BURAYA — belge sorudan ÖNCE gelir}

<gorev>
Yukarıdaki sözleşmeyi alıcı açısından incele ve aşağıdaki sabit sırayla
ilerle. Satıcı açısından inceleme isteniyorsa bunu çıktının ilk satırında
söyle — varsayılan alıcıdır.

PDF ya da DOCX ile çalışılıyorsa önce madde yapısını çıkar:

    python3 ~/mafirm/birimler/_araclar/kod/belge.py [DOSYA YOLU] --yapi
</gorev>

<yontem>
Sıra sabittir. Bir başlığı atlama, sırasını değiştirme.

1. **Kapanış öncesi koşullar.** Neler var; her birini kim kontrol ediyor
   (alıcı, satıcı, üçüncü kişi, düzenleyici); saati ne — nihai tarih hangi
   gün ve o tarih ikinci aşama incelemesini karşılıyor mu.
2. **Ara dönem taahhütleri.** Her taahhüt için tek soru: bu değer koruma mı,
   fiilî kontrol mü? Ortak fiyatlandırma, ortak müşteri görüşmesi, bütünleşme
   hazırlığı, alıcı onayına bağlanmış olağan iş kararları — 4054 sayılı Kanun
   madde 11 bakımından izinsiz kapanış (gun-jumping) riski doğuran her
   taahhüdü ayrıca işaretle.
3. **Beyanlar.** Kapsam (neyi kapsıyor, neyi kapsamıyor), sınırlayıcılar,
   bilgi kaydı (kimin bilgisi, araştırma yükümlülüğü var mı) ve önemlilik
   kaydı. Bir beyanın "bilgisi dahilinde" ile kayıtlanması, o beyanı çoğu
   olayda kullanılamaz hâle getirir; bunu tespit et.
4. **Açıklama.** Veri odası genel açıklama sayılıyor mu? Sayılıyorsa alıcı,
   veri odasında bulunan her şeyden feragat etmiş olur — bunun bu dosyadaki
   maliyetini rakamla yaz. Açıklama mektubu ile veri odasının ilişkisini
   kur.
5. **Sınırlamalar.** Tavan, alt sınır (eşik), asgari tutar (de minimis) ve
   beyan sınıfı başına süre. Sınıfları ayrı ayrı yaz: temel beyanlar, vergi,
   iş hukuku, ticari beyanlar. Tek bir "12 ay" cümlesi çoğu vergi riskini
   zamanaşımından önce kapatır.
6. **Başvuru — gerçekte kim ödeyebilir.** Emanet (miktar, süre, serbest bırakma
   koşulu), W&I sigortası (kapsam dışı bırakılanlar, muafiyet, poliçenin
   bilinen riski dışladığı yerler) ya da satıcı taahhüdü. Satıcı bir SPV ise
   kâğıt üstündeki tazminat sıfır değerindedir; bunu açıkça yaz.
7. **Uygulanacak hukuk, tahkim yeri ve tenfiz edilebilirlik.** Kararın
   satıcının GERÇEK mal varlığının bulunduğu ülkede icra edilebilirliği —
   forum seçimi değil, tahsil edilebilirlik sorusu bu.
8. **SPA'nın bertaraf edemeyeceği Türk emredici kuralları.** En az şunlar:
   pay devrinin şekil şartı (limited şirkette noter onaylı devir ve pay
   defteri kaydı, anonim şirkette ciro ve teslim), Rekabet Kurulu izni ve
   bekletici etkisi, ve iş hukuku bakımından işçilerin devri ile kıdemin
   devamı. Sözleşme aksini yazmış olabilir; yazmış olması onu geçerli kılmaz.

**Bir madde yoksa "yok" yaz.** Olmayan bir madde bir bulgudur ve çoğu zaman
var olan kötü bir maddeden pahalıdır: tavanı olmayan bir sözleşmede tavan
aramak boşuna değildir, tavanın yokluğunu yazmamak hatadır.

Her bulguyu maliyetine göre değerlendir, göze çarpıcılığına göre değil.
Bulguları listelemeden önce akıl yürütmeni göster: hangi maddenin hangi
olayda tetikleneceğini ve müvekkile ne getireceğini önce düşün.
</yontem>

<ornekler>
<ornek>
Madde 7.3 · Beyanlar "satıcının bilgisi dahilinde" kaydıyla sınırlı ve bilgi,
üç yönetici ile sınırlı tanımlanmış, araştırma yükümlülüğü yok.
Alıcıya maliyeti: hedefin operasyonel katmanında doğan hemen her ihlal beyan
kapsamı dışında kalır; veri odasında görülmeyen her risk alıcıda.
Düzeltme: bilgi tanımına "makul araştırma sonrası" eklenmesi ve temel
beyanların kayıtsız yazılması.
</ornek>
<ornek>
Madde 9 · Tavan mevcut (fiyatın %15'i) ancak temel beyanlar için ayrı tavan
YOK; mülkiyet ve yetki beyanları da aynı tavana tabi.
Alıcıya maliyeti: payların mülkiyetinde bir sorun çıkarsa telafi fiyatın
%15'iyle sınırlı kalır — alıcı satın aldığı şeyi kaybedip bedelin %85'ini
üstlenir.
Düzeltme: temel beyanlar için fiyatın %100'ü ve uzun süre.
</ornek>
<ornek>
Madde 12 · Emanet yok, W&I yok, satıcı bir Hollanda SPV'si ve kapanışta
dağıtım yapacak.
Alıcıya maliyeti: sözleşmedeki tazminat hükümlerinin tamamı tahsil edilemez;
kâğıt üstündeki koruma sıfır.
Düzeltme: bedelin bir kısmının emanete alınması ya da ana ortak garantisi.
</ornek>
</ornekler>

<cikti>
1. **Bulgu tablosu.** Sütunlar: madde numarası | ne diyor | alıcıya maliyeti |
   düzeltme. En kötü önce sırala — maliyeti en büyük olan en üstte, göze en
   çok çarpan değil. En çok on beş satır. On beşten fazla bulgu varsa kaç
   bulgunun tabloya alınmadığını ve hangi ölçütle elendiğini bir cümleyle
   yaz (örneğin: "yedi bulgu, beklenen maliyeti işlem bedelinin binde
   birinin altında kaldığı için alınmadı").

2. **Müzakere sermayesini harcayacağın üç nokta ve neden bu üçü.** Üçünü
   adlandır, her biri için karşı tarafın vermesi muhtemel cevabı ve senin
   düşeceğin asgari noktayı yaz. Neden bu üçü: geri kalan bulguların neden
   bu üçünün altında kaldığını tek cümleyle gerekçelendir.

Sonra tam olarak şu üç başlıkla, bu sırayla bitir:

**Şimdi ne yapılmalı**
[karşı tarafa gidecek ilk revizyon turu — hangi maddeler, hangi sırayla]

**Yetkili avukat görüşü gereken konular**
[Türk emredici kuralları, tenfiz, sigorta kapsamı ve müvekkile gidecek her
ifade; bu bölüm gerçek bir dosyada asla boş kalmaz]

Kontrol edildi: <kaynak> (<tarih>) · <kaynak> (<tarih>) · bulunamayan: <ne>
</cikti>
