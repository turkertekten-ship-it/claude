# mafirm — sınır ötesi birleşme ve devralma pratiği

Bu depo, *Uluslararası M&A Hukuku · Kurulum Kitabı* (Arel Barzilay, Sürüm 1.0)
uygulanarak kurulmuş çalışan bir sistemdir. Bir okuma listesi değil, çalıştırılan
bir kurulum programıdır: kitabın §0–§19'unun her bölümü ya bir dosya üretti ya
bir dosyayı doğruladı.

**Bu sistemin ürettiği hiçbir çıktı hukuki görüş değildir.** Her esaslı çıktı iki
başlıkla biter: *Şimdi ne yapılmalı* ve *Yetkili avukat görüşü gereken konular*.
Türkiye'de bir tescil, imzalanmış bir sözleşme, bir kurum başvurusu ve gerçek bir
müvekkile verilen her tavsiye baroya kayıtlı bir avukat gerektirir.

## Hızlı başlangıç

```bash
bash ~/mafirm/denetim.sh                                  # her sınama ve kapı
python3 ~/mafirm/birimler/_araclar/kod/dogrula.py         # araç katmanı
python3 ~/mafirm/birimler/rekabet/kod/esik.py --self-test # eşik kodu
python3 ~/mafirm/.claude/hooks/kapi.py --self-test        # beş kapı
```

`~/mafirm`, bu depodaki `mafirm/` klasörüne bir sembolik bağdır; kitaptaki her
doğrulama komutu birebir çalışır.

## Düzen

| Yol | Ne |
|---|---|
| `mafirm/CLAUDE.md` | İşletim sözleşmesi — 11 kural, her oturumda okunur |
| `mafirm/birimler/` | Sekiz uzmanlık birimi: yöntem, kod, emsal |
| `mafirm/birimler/_koltuklar/` | On üç ortak koltuğu + **iki bilerek boş** koltuk |
| `mafirm/birimler/_araclar/` | Araç kataloğu ve çalışan sarmalayıcılar |
| `mafirm/isakislari/` | Uçtan uca iş akışları |
| `mafirm/komutlar/` | İstem şablonları (§15) |
| `mafirm/.claude/` | Beceriler, alt ajanlar, komutlar, kapılar |
| `mafirm/denetim.sh` | Tam denetim — sesli biçimde başarısız olur |
| `mafirm/KURULUM.md` | **Kurulum kaydı ve kitaptan ayrılan yerler** |

## Katmanlar ve maliyeti

| Katman | Ne zaman okunur |
|---|---|
| İşletim sözleşmesi | Her oturumda, kendiliğinden |
| Uzmanlık birimleri | Dosya oraya yönlendiğinde |
| Ortak koltukları | Ağır bir kararda |
| Otomatik kontroller | Tetikleyen olayda |
| Beceriler, alt ajanlar, iş akışları | Talebe göre |

Yalnızca birinci katmanın bedeli her oturumda ödenir; gerisi çağrıldığında
yüklenir.

## Beş kapı

`mafirm/.claude/hooks/kapi.py` — 2 çıkış koduyla işlemi durdurur.

| Kapı | Neyi yakalar |
|---|---|
| `kapsam` | Görüş gibi okunan ama avukat başlığı taşımayan çıktı |
| `kanit` | Dayanağı yanında olmayan mevzuat eşiği |
| `sir` | Müvekkili tanıtan bilginin dışarı giden çağrıya girmesi |
| `guncellik` | Doğrulama tarihi bayatlamış bir eşiğe dayanılması |
| `arastirma` | Rakam ya da depo anıldığı hâlde "Kontrol edildi:" satırı yok |

Kip: pratiğin içinde **block**, makine genelinde Write/Edit için **warn**;
dışarı giden çağrıda sır kapısı her kipte bloklar. Kapatma: `MAFIRM_KAPI=off`.

Her kapı iki yönde sınanır — kusurlu vakada ateşlemeli, doğru vakada susmalı.
Yalnızca geçen bir kapı, kapı değildir.

## Makine geneline kurulum

```bash
bash ~/mafirm/kur-genel.sh
```

Beceriler, alt ajanlar, komutlar ve kapılar `~/.claude` altına kurulur; her
oturum ve her terminal aynı doktrini okur.

## Bilerek yapılmayanlar

1. Hukuki görüş vermez, hukuk bürosu değildir.
2. **Türk uygulamacı koltuğu yoktur** ve bu bilerek boştur.
3. **Vergi koltuğu yoktur** ve işlem yapısı vergi kaynaklıdır.
4. Türkiye rakamlarının raf ömrü vardır; altı aydan eskisi bayattır.
5. `eyecite` ve `courtlistener` yalnızca ABD'dir — Türk içtihadı YOKTUR.
6. AGPL lisanslı bileşenler kurulmadı.
7. İşlemsel belge kaleme almada ölçülmüş kazanç yoktur.
8. Doğruluğu artırdığına dair kanıt yoktur; kazanç açıklık ve düzendedir.
9. Kendisine söylenmemiş bir çıkar çatışmasını tespit edemez.

`mafirm/KURULUM.md`, bu kurulumda **doğrulanamayan** her şeyi ve kitaptan
ayrılan altı yeri açıkça listeler.
