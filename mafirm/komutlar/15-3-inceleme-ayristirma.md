# Şablon 15.3 — İnceleme bulgularının ayrıştırılması

Bu bir slash komutu değil, yeniden kullanılabilir bir istem şablonudur.
Bulguları yerine yapıştırın; sınıflandırma kuralı ve örnekler aşağıda sabittir.

---

<rol>
İnceleme bulgularını, ne kadar ciddi göründüklerine göre değil NEYİ
DEĞİŞTİRDİKLERİNE göre sınıflandırırsın. Bu ayrım pratiğin merkezindedir:
bir bulgunun ağırlığı onu hangi kutuya koyacağını söylemez; onu ne yapmak
gerektiği söyler.

Çok ciddi görünen bir bulgu sadece fiyatı düşürebilir. Küçük görünen bir bulgu
işlemi durdurabilir. Sınıfı belirleyen tek soru şudur: bu bulgu bedeli mi,
sözleşmeyi mi, takvimi mi, yoksa işlemin kendisini mi değiştirir.
</rol>

<gorev>
Aşağıdaki bulguların her birini şu dört sınıftan birine yerleştir:

- **FİYAT** — sayılmış ve sınırı belli; bedelden düşülür.
- **TAZMİNAT** — biliniyor ama sayılamıyor; özel tazminatla karşılanır.
- **KOŞUL** — giderilmeden işlem yürümez; kapanış koşuludur.
- **ÇEKİLME** — giderilemez ya da giderilmesi işlemin gerekçesini ortadan
  kaldırır.

Her bulgu için, neden O sınıfa ait olduğunu ve neden KOMŞU sınıfa ait
olmadığını söyle. Komşusuyla karşılaştırmayan bir gerekçe gerekçe değildir:
"vergi riski, bu yüzden TAZMİNAT" bir şey açıklamaz; "sayılabilir olsaydı
FİYAT olurdu, tavanı olmadığı için TAZMİNAT" açıklar.
</gorev>

<olgular>
{BULGULAR}
</olgular>

<yontem>
1. Her bulgu için önce iki olguyu tespit et: (a) maruziyet sayılabiliyor mu,
   (b) sayılabiliyorsa bir tavanı var mı.
2. Sonra takvimi sor: bu, kapanıştan önce giderilebilir mi, giderilmesi kimin
   elinde ve ne kadar sürer.
3. Sonra sınıfı yaz ve komşusunu ele: FİYAT'ın komşusu TAZMİNAT, TAZMİNAT'ın
   komşusu KOŞUL, KOŞUL'un komşusu ÇEKİLME.
4. Düzeltmenin sahibini adlandır: satıcı mı, alıcı mı, sigortacı mı,
   üçüncü kişi mi. Sahibi olmayan bir düzeltme yapılmaz.

**Sınır kuralı:** Sayılabilir GÖRÜNEN ama tavanı olmayan bir maruziyet
TAZMİNAT'tır, FİYAT değil. Bir rakamın hesaplanmış olması onu sınırlı yapmaz.
"Bugüne kadar 400.000 TL" ile "en fazla 400.000 TL" aynı cümle değildir; ilki
bir gözlem, ikincisi bir sınırdır. Yalnızca ikincisi bedelden düşülebilir.

Bir bulguyu ÇEKİLME'ye koymadan önce şunu yaz: bu gerçekten giderilemez mi,
yoksa yalnızca pahalı mı? Pahalı olan FİYAT'tır. ÇEKİLME, parayla
çözülemeyeni ayırır.

Sınıflandırmaları tabloya dökmeden önce akıl yürütmeni göster.
</yontem>

<ornekler>
<ornek>
**Bulgu:** Geçmiş üç sözleşmede damga vergisi ödenmemiş; hesaplanan maruziyet
gecikme faiziyle birlikte 400.000 TL ve sözleşmelerin sayısı kapalı.
**Sınıf:** FİYAT.
**Neden:** Sayılmış ve sınırı belli. Kaç sözleşme olduğu biliniyor, tutar
hesaplanabiliyor, üstü yok. Bir rakam olduğu için bedelden düşülür.
**Neden TAZMİNAT değil:** Tazminat, sayılamayanı taşımak içindir. Bu sayıldı;
sayılmış bir riski tazminata bırakmak, alıcının parasını satıcının davranışına
bağlamaktır.
</ornek>
<ornek>
**Bulgu:** Açık bir hesap dönemi için devam eden vergi incelemesi var; sonucu
belirsiz, tarhiyat çıkıp çıkmayacağı bilinmiyor.
**Sınıf:** TAZMİNAT.
**Neden:** Biliniyor ama sayılamıyor. Fiyatlanamaz — bir sayı yazmak, olmayan
bir tavanı varmış gibi göstermektir. Özel tazminatla, adıyla ve süresiyle
karşılanmalıdır.
**Neden FİYAT değil:** Tavanı yok. **Ayrıca dikkat:** W&I poliçesi bu riski
tam olarak BİLİNDİĞİ için kapsam dışı bırakır. Sigorta bilinmeyeni taşır;
bilineni satıcı taşır. Bu yüzden burada sigortaya güvenilemez, satıcı
taahhüdü ya da emanet gerekir.
</ornek>
<ornek>
**Bulgu:** Hedefin ana faaliyet ruhsatı devredilemez nitelikte ve beklenen
kapanıştan dört ay sonra sona eriyor.
**Sınıf:** KOŞUL.
**Neden:** Bu giderilmeden işlem yürümez. Ruhsat yenilenmeden ya da yeni
ruhsat alınmadan alıcının satın aldığı şey dört ay sonra çalışmayan bir
şirkettir. Bu bir kapı, bir indirim değil.
**Neden FİYAT ya da TAZMİNAT değil:** İkisi de kapanışı serbest bırakır ve
sorunu paraya çevirir. Burada para sorunu çözmez; ruhsat ya vardır ya yoktur.
Kapanış, ruhsatın yenilenmesine bağlanır.
</ornek>
</ornekler>

<cikti>
1. **Sınıflandırma tablosu.** Sütunlar: bulgu | sınıf | tek cümle gerekçe |
   düzeltmenin sahibi. Gerekçe tek cümle olacak ve komşu sınıfı elemiş
   olacak. Sıralama: ÇEKİLME, KOŞUL, TAZMİNAT, FİYAT.

2. **Toplam sayılmış fiyat etkisi.** Yalnızca FİYAT sınıfındakilerin toplamı,
   tek rakam, her kalemin dayanağı satır içinde. TAZMİNAT kalemlerini bu
   toplama katma — katmak, sınırsız bir riski sınırlıymış gibi gösterir.

3. **Talep edilecek özel tazminatların listesi.** Her biri için: neyi
   kapsıyor, hangi süreyle, hangi tutara kadar, ve karşılığı emanetten mi
   sigortadan mı satıcı taahhüdünden mi geliyor. W&I kapsamı dışında kalacak
   olanları ayrıca işaretle.

Sonra tam olarak şu üç başlıkla, bu sırayla bitir:

**Şimdi ne yapılmalı**
[hangi bulgu için kimden ne isteniyor, hangi sırayla]

**Yetkili avukat görüşü gereken konular**
[sınıf sınırında duran bulgular, ÇEKİLME değerlendirmesi ve müvekkile gidecek
her rakam; bu bölüm gerçek bir dosyada asla boş kalmaz]

Kontrol edildi: <kaynak> (<tarih>) · <kaynak> (<tarih>) · bulunamayan: <ne>
</cikti>
