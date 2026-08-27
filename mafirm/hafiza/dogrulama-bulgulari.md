# Açık doğrulama bulguları

Kör sınama, mevzuat ve kaynak katmanında çözülmemiş bulgular bıraktı. Bunlar
KOD hatası değildir ve bu yüzden yamalanmadılar: bir eşik değişikliği insan
kararıdır (§11, `/esik-denetle`: "Hiçbir dosyayı düzenleme"). Ayrıca kanıt
katmanı zayıftır — bu ortamda hiçbir birincil kaynağa erişilemedi.

Biçim: `<kimlik> | <engelleyici mi> | <dosya> | <bulgu>`

I-01 | ENGELLEYICI | birimler/rekabet/yontem/tr-esikler.md | Teknoloji istisnası 2026/2 m.7(2) uyarınca (a) VE (b) bentlerine uygulanıyor olabilir; kitap yalnızca B ayağına uyguluyor. AZ bildirim riski = izinsiz kapanış.
I-02 | ENGELLEYICI | birimler/rekabet/yontem/tr-esikler.md | Teknoloji bağlantı ölçütü "Türkiye'de yerleşik" olabilir; kitaptaki "faaliyet gösteren ya da Ar-Ge yapan" 2022/2'nin kalkmış ölçütü. FAZLA bildirim riski.
I-03 | ENGELLEYICI | birimler/rekabet/yontem/tr-esikler.md · birimler/rekabet/kod/esik.py · .claude/skills/spa-inceleme/SKILL.md · komutlar/15-2-spa-incelemesi.md | Bekletici etki 4054 m.10 (+m.7/2) olabilir; dört dosya m.11'e atıf yapıyor. M.11 "bildirilmemenin sonuçları"dır. KANIT KATMANI YÜKSELTİLDİ 2026-08-27: rekabet.gov.tr ve mevzuat.gov.tr üzerinde iki bağımsız arama, m.10'un ön inceleme + askıya alma + 30 günde zımni geçerlilik mekanizmasını taşıdığını, m.11'in ise bildirilmeme hâlini düzenlediğini doğruladı. Statü hâlâ ENGELLEYİCİ: birincil metin (mevzuat.gov.tr/MevzuatMetin/1.5.4054.pdf) egress ile engelli, birebir madde başlığı okunamadı. Dört dosyaya yerinde DOĞRULANAMADI işareti kondu (CLAUDE.md §1).
I-04 | hayır | birimler/rekabet/yontem/tr-esikler.md | M.16 cezasının kanuni alt sınırı (2026: 302.484,86 TL) yazılmamış.
I-05 | hayır | birimler/tr-sirketler/yontem/pay-devri.md | TTK 499 kaydı açıklayıcıdır, kurucu değil; 595/1 imza onayıdır, düzenleme şeklinde senet değil.
H-03 | hayır | (kitap §17.1) | Süre düşüşü aralıkları (%20–28 / %20–34) hiçbir kaynakla uyuşmuyor; kaynaklar %14–37 / %12–28 diyor.
H-04 | hayır | (kitap §17.1) | +0,26 puan, iki AI kolu ARASINDAKİ farktır; kontrol grubuna karşı etki değildir.
H-06 | hayır | (kitap §17.3) | "%19 daha düşük" -> "19 YÜZDE PUANI daha düşük". Mevcut ifade riski küçültüyor.
G-01 | hayır | (kitap §13.5) | courtlistener lisansı AGPL-3.0-or-later; kitap "açık (depoya bakın)" diyor.
G-02 | hayır | (kitap §13.4) | google/diff-match-patch 2024-08-05'te ARŞİVLENDİ; kitap yazmıyor.
G-03 | hayır | (kitap §13.3) | opensanctions kodu MIT ama VERİSİ CC BY-NC 4.0; ticari pratikte lisans sorusu doğurur.

## Çözüm yolu
Her ENGELLEYICI satır, birincil kaynak açılıp teyit edilene kadar açık kalır.
Teyit edildiğinde satır silinir ve ilgili dosya güncellenip yeni bir doğrulama
tarihi yazılır.
