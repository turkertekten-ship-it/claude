---
name: madde-karsilastirma
description: Bir maddenin ya da belgenin iki sürümü karşılaştırılırken, müzakere turları arasında neyin değiştiği sorulduğunda, karşı taraftan gelen değişiklik seti (markup) incelenirken kullan. Emsal madde bankasındaki bir biçimle önüne konan madde kıyaslanırken de devreye girer.
---

# Madde karşılaştırma

## Göz değil kod

Müzakere turları arasında değişen bir "ve", ya da "makul çaba"nın "azami çaba"
olması, tazminat tavanından daha çok para taşıyabilir ve göz bunu kaçırır.

    python3 ~/mafirm/birimler/_araclar/kod/karsilastir.py <eski.txt> <yeni.txt>

Belge PDF ya da DOCX ise önce düz metne indir:

    python3 ~/mafirm/birimler/_araclar/kod/belge.py <dosya> --yapi

## Farkı raporlamanın biçimi

Karakter farkı bir bulgu değildir. Her fark için üç şey yazılır:

1. **Ne değişti** (eski → yeni, tam sözcükle).
2. **Kime yarıyor** — alıcıya mı satıcıya mı, ve neden.
3. **Sessiz mi** — değişiklik özet yazıda ya da kapak mektubunda belirtilmiş mi?
   Belirtilmemiş bir esaslı değişiklik ayrıca raporlanır.

## Sessiz değişiklik

Bir tur değişikliğinde en sonuçlu bulgu, karşı tarafın söylemediği
değişikliktir. Bunları ayrı bir başlık altında topla.

## Çıktı

Tablo: madde | eski | yeni | kime yarıyor | sessiz mi.
Sonra: kabul edilebilir / müzakere / reddedilecek diye üç liste.
Şununla bitir: Şimdi ne yapılmalı / Yetkili avukat görüşü gereken konular /
Kontrol edildi:
