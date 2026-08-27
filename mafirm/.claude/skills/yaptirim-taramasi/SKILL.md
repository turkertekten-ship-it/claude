---
name: yaptirim-taramasi
description: Bir karşı taraf, hedef şirket, ortak, yönetici, gerçek lehtar (beneficial owner), müşteri ya da ülke maruziyeti kontrol edilirken kullan. Yaptırım listeleri, siyasi nüfuz sahibi kişi taraması, ihracat kontrolü, çift kullanımlı ürün sınıflandırması ve rüşvet maruziyeti sorularında devreye girer.
---

# Yaptırım ve nüfuz taraması

## Sır saklama kuralı burada en katıdır

**Hedefin, müvekkilin ya da gerçek lehtarın adı hiçbir dış arama servisine
girmez.** Tarama yerel çalışır. Dışarıdan bir hukuki soru gerekiyorsa sorgu
soyutlanır: "çift kullanımlı ürün sınıflandırması nasıl yapılır" sorulur,
hedefin adı sorulmaz. Bu kural §12'deki sır kapısıyla uygulanır.

## Araç

    python3 ~/mafirm/birimler/_araclar/kod/tarama.py "<ad>" --liste <liste.txt>

Türkçe adlar birden çok biçimde çevrilir (Şükrü / Sukru / Shukru) ve elle tarama
bunu kaçırır. Betik normalleştirerek eşleştirir.

## Ne taranır, ne zaman

Üç noktada: gizlilik sözleşmesinden önce, münhasırlıktan önce, imzadan önce.

| Nesne | Kontroller |
|---|---|
| Hedef ve ana ortaklar | OFAC SDN, AB konsolide, Birleşik Krallık OFSI, BM |
| Gerçek lehtarlar, yöneticiler | Aynı listeler + siyasi nüfuz sahibi kişi |
| Müşteri ve tedarikçiler | Yaptırım uygulanan ülkelerde yoğunlaşma |
| Ürünler | Çift kullanım sınıflandırması, ihracat lisansı |
| Ödemeler | Muhabir bankacılık, para birimi yönlendirmesi |

## Eşleşme sonrası — dört adım

1. Kimlik doğrulaması: aynı ad mı, aynı kişi mi?
2. Maruziyetin niteliği: doğrudan mı, dolaylı mı, geçmişte mi?
3. Alıcının kendi rejimi ne diyor (ABD / AB / Birleşik Krallık ayrı sonuç
   verebilir)?
4. Devam kararı — **bu sistem tarafından asla verilmez.**

## Rüşvet

FCPA ve Bribery Act 2010 alıcıya bağlanır; halefiyet sorumluluğu nedeniyle temiz
bir alıcı temiz olmayan bir hedefin maruziyetini devralır. Bribery Act m.7
"önlememe" suçu, prosedürlerin yeterliliğini de bir inceleme kalemi yapar.

## Çıktı

Tablo: nesne | liste | sonuç | güven | sonraki adım.
Şununla bitir: Şimdi ne yapılmalı / Yetkili avukat görüşü gereken konular /
Kontrol edildi:
