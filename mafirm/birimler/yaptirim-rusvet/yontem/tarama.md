# Yaptırım, ihracat kontrolü ve rüşvet taraması

Doğrulama: 2026-08-27.

Kontrol edildi: kurulum kitabı §6 (2026-08-27) · OpenSanctions ve nomenklatura
paket kaydı, PyPI (2026-08-27) · bulunamayan: OFAC, AB, OFSI ve BM liste
uç noktalarının bu makineden erişilebilirliği — ağ çıkışı kısıtlı, tarama
çevrimdışı veri kümesiyle yapılır.

Türkiye'nin coğrafi konumu, karşı taraf taramasını bir formalite olmaktan
çıkarır. Bir Türk hedefinin Rusya, İran ya da Suriye ticaret geçmişi Türk
hukukuna göre hukuka uygun, bir ABD ya da AB alıcısı için diskalifiye edici
olabilir.

## Ne taranır, ne zaman

Üç noktada taranır: gizlilik sözleşmesinden önce, münhasırlıktan önce ve
imzadan önce. İlk tarama ucuzdur ve sonraki pahalı keşfi önler.

| Nesne | Listeler ve kontroller |
|---|---|
| Hedef ve ana ortaklar | OFAC SDN, AB konsolide listesi, Birleşik Krallık OFSI, BM |
| Gerçek lehtarlar ve yöneticiler | Aynı listeler artı siyasi nüfuz sahibi kişi taraması |
| Müşteriler ve tedarikçiler | Yaptırım uygulanan ülkelerdeki yoğunlaşma |
| Ürünler | Çift kullanımlı sınıflandırma ve ihracat lisansı |
| Ödemeler | Muhabir bankacılık maruziyeti, para birimi yönlendirmesi |

## Türkçe ad çevirisi ayrı bir kusur kaynağıdır

Türkçe adlar birden çok biçimde çevrilir: Şükrü / Sukru / Shukru, Öztürk /
Ozturk / Oztuerk. Elle tarama bu farkları kaçırır. `nomenklatura` tam olarak
bunu çözmek için vardır ve bu katalogda bir Türk pratiği için en kullanışlı
araçtır. Çalıştırma yolu: `birimler/_araclar/kod/tarama.py`.

## Eşleşme sonrası

Bir ad eşleşmesi bir ipucudur, bir sonuç değildir. Sırayla:
1. Kimlik doğrulaması — aynı ad mı, aynı kişi mi? Doğum tarihi, uyruk, adres.
2. Maruziyetin niteliği — doğrudan mı, dolaylı mı, geçmişte mi?
3. Alıcının kendi rejimi ne diyor — ABD, AB ve Birleşik Krallık aynı olguya
   farklı sonuç bağlayabilir.
4. Devam kararı. Bu karar hiçbir koşulda bu sistem tarafından verilmez.

## Rüşvetle mücadele

FCPA (ABD) ve Bribery Act 2010 (Birleşik Krallık) alıcıya bağlanır ve halefiyet
sorumluluğu nedeniyle temiz bir alıcı, temiz olmayan bir hedefin maruziyetini
devralabilir. Bribery Act'in 7. maddesindeki "önlememe" suçu, hedefin yalnızca
davranışını değil prosedürlerinin yeterliliğini de bir inceleme kalemi yapar.

Tekrar eden risk noktaları: kamu müşterisi yoğunlaşması, acenteler ve aracılar,
gümrük müşavirleri ve lisansa bağlı faaliyetler.

## Sır saklama kuralı burada en katıdır

Bir hedefin ya da gerçek lehtarın adı hiçbir dış arama servisine girmez.
Tarama yerel veri kümesiyle yapılır. Dışarıdan bir hukuki soru gerekiyorsa
sorgu soyutlanır: "Türk hedefli bir işlemde çift kullanımlı ürün sınıflandırması
nasıl yapılır" sorulur, hedefin adı sorulmaz.

## Şimdi ne yapılmalı

Gizlilik sözleşmesi imzalanmadan önce ilk tarama çalıştırılır ve sonucu
`dosyalar/<dosya>/tarama/` altına tarihiyle yazılır.

## Yetkili avukat görüşü gereken konular

Her olumlu eşleşme, her çift kullanım sınıflandırması ve olumsuz bir bulguya
rağmen devam etme kararı.
