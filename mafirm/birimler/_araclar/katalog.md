# Araç kataloğu — kurulmuş, doğrulanmış, yönlendirilmiş

Doğrulama: 2026-08-27.

Kontrol edildi: PyPI ve npm kayıt uç noktaları (2026-08-27) · `git ls-remote`
ve sığ klon ile depo çözümlemesi (2026-08-27) · bu makinedeki gerçek `import`
denemesi (2026-08-27) · **GitHub deposu arama uç noktası üzerinden yıldız,
lisans ve son güncelleme (2026-08-28)** · bulunamayan: doğrudan
`api.github.com` çağrısı — hâlâ kapalı; rakamlar GitHub arama aracıyla
alınmıştır.

## Yıldız sayıları — sonradan doğrulandı

İlk kurulumda `api.github.com` kapalıydı ve yıldız sayıları bu dosyaya
**yazılmadı**; kitaptan kopyalanmaları reddedildi. Sonradan GitHub deposu
arama uç noktasının çalıştığı görüldü ve **her rakam canlı olarak çekildi**.
Aşağıdaki tablolardaki yıldızlar 2026-08-28 tarihinde ölçülmüştür.

**Kitabın yıldız sayıları esasen doğruydu** — sapma normal büyüme kadar.
Yanlış olan tarihlerdi (aşağıya bakın). Bu, kitabın hangi kısmına güvenilip
hangisine güvenilmeyeceğini gösterir: sayımı yapılmış bir olgu tutmuş,
"en son ne zaman güncellendi" iddiası tutmamıştır.

| Depo | Kitap | Ölçülen (2026-08-28) |
|---|---|---|
| docling-project/docling | 65.575 | **65.674** |
| Open-Source-Legal/OpenContracts | 1.449 | **1.455** |
| unclecode/crawl4ai | 79.445 | **79.618** |
| Panniantong/Agent-Reach | 75.400 | **76.177** |
| opensanctions/opensanctions | 789 | **789** |
| opensanctions/nomenklatura | 265 | **265** |
| google/diff-match-patch | 8.140 | **8.139** |
| LexPredict/lexpredict-lexnlp | 795 | **795** |
| ICLRandD/Blackstone | 696 | **696** |
| freelawproject/eyecite | 271 | **272** |
| freelawproject/courtlistener | 1.002 | **1.003** |
| unionai-oss/pandera | 4.442 | **4.443** |
| fivetran/great_expectations | 11.738 | **11.743** |
| python-openxml/python-docx | 5.697 | **5.698** |
| jsvine/pdfplumber | (verilmemiş) | **10.700** |

## Yıldızın ölçmediği iki şey — bu kurulumda çıktı

1. **`google/diff-match-patch` ARŞİVLENMİŞ bir depodur.** Kitap onu yalnızca
   "eski" sayıyor; gerçekte Google depoyu resmen arşivlemiştir, yani salt
   okunur ve bakımı bırakılmıştır. 8.139 yıldız bunu göstermez. Karar
   değişmiyor (kararlı algoritma, kurulu kalıyor) ama gerekçe artık
   "bakımsız" değil "arşivlenmiş"tir ve bir hata bulunursa düzeltilmeyecektir.

2. **`Panniantong/Agent-Reach` 2026-02-24'te oluşturulmuş bir depodur** ve altı
   ayda 76.177 yıldıza ulaşmıştır. Rakam gerçektir; ne anlama geldiği ayrı bir
   sorudur. Zaten kurulmadı (sır saklama kuralı), ama bu, kitabın "yıldız bir
   şey kanıtlamaz" cümlesinin en somut örneğidir: bir depoyu yaşı ve büyüme
   hızıyla birlikte okumayan biri, buradan güven çıkarır.

Yıldızın yanında **çözümlenebilirlik** ve **son commit tarihi** de doğrulandı;
ikisi de bakım sorusunu yıldızdan iyi cevaplar.

## API kapalıyken çözümleme nasıl yapıldı

`~/.claude/skills/once-arastir` bu yolu kalıcı olarak yazar:

    git ls-remote --heads https://github.com/<sahip>/<depo>     # çözülüyor mu
    git clone --depth 1 --filter=blob:none --no-checkout ...    # son commit
    curl -s https://pypi.org/pypi/<paket>/json                  # sürüm, lisans
    curl -s https://registry.npmjs.org/<paket>                  # sürüm, lisans

## Belge çıkarma — KURULU

| Depo | Paket | Lisans | Son commit | Durum |
|---|---|---|---|---|
| docling-project/docling | docling 2.123.0 | MIT | 2026-08-26 | import ok |
| jsvine/pdfplumber | pdfplumber | MIT | 2026-06-14 | import ok |
| Open-Source-Legal/OpenContracts | — | MIT | çözüldü | kurulmadı, okuma kaynağı |

docling, pdfplumber'ın yerine değil öncesine gelir: docling madde hiyerarşisini
verir, pdfplumber bir finansal cetvelde hücre koordinatına iner. Bir SPA
birincisini ister; kapanış hesapları cetveli ikincisini.

Çalıştırma: `kod/belge.py` (ikisini de sarar, hangisini neden seçtiğini yazar).

## Yaptırım ve gerçek lehtar — KURULU

| Depo | Paket | Lisans | Son commit |
|---|---|---|---|
| opensanctions/nomenklatura | nomenklatura | MIT | 2026-08-24 |
| opensanctions/opensanctions | — (veri kümesi) | MIT | 2026-08-27 |

Kitabın "son üç gün içinde güncellenmiştir" iddiası doğrulandı ve fazlasıyla:
opensanctions bugün güncellenmiş. Türkçe adların harf çevirisi farklarını
(Şükrü / Sukru / Shukru) elle tarama kaçırır; nomenklatura bunun için vardır.

Çalıştırma: `kod/tarama.py`. Sır saklama kuralı üsttedir — ad hiçbir dış
servise gitmez, eşleştirme yereldir.

## Sözleşme ve madde çözümlemesi

| Depo | Lisans | Son commit | Kitabın dediği | GERÇEK | Karar |
|---|---|---|---|---|---|
| google/diff-match-patch | Apache-2.0 | **2019-07-25** | 2024-05-22 | 7 yıl | Kullan — kurulu |
| LexPredict/lexpredict-lexnlp | AGPL-3.0 | **2023-03-06** | 2024-05-27 | 3,5 yıl | KURULMADI |
| ICLRandD/Blackstone | Apache-2.0 | **2021-01-31** | 2024-07-16 | 5,5 yıl | Kurulmadı, okuma kaynağı |

**Kitabın üç tarihi de yanlıştı ve üçü de gerçekte daha eski.** Bu, kitabın
kendi §13.4 kararlarını güçlendirir, zayıflatmaz: diff-match-patch'in kararlı
algoritma gerekçesi 2019 için de geçerlidir; Blackstone "iki yıldır bakımsız"
değil beş buçuk yıldır bakımsızdır ve bağımlılık değil okuma kaynağıdır.

lexpredict-lexnlp **AGPL-3.0** olduğu için kurulmadı. Bu bir paket kurulumu
değil, asıl sahibin lisans kararıdır (§13.4).

Çalıştırma: `kod/karsilastir.py` (diff-match-patch).

## İçtihat ve atıf — KURULU ama SINIRLI

| Depo | Paket | Lisans | Son commit |
|---|---|---|---|
| freelawproject/eyecite | eyecite | BSD-2-Clause | 2026-08-14 |
| freelawproject/courtlistener | — | açık | çözüldü |

**İkisi de yalnızca Amerika Birleşik Devletleri'dir.** Türk içtihadını, Yargıtay
kararlarını ya da Rekabet Kurulu emsallerini bilmezler ve hiçbir ayar bunu
değiştirmez. Bu sistemde Türk içtihadı YOKTUR. "İçtihat" gibi görünüp tek ülkeyi
kapsayan bir araç, sınır ötesi bir pratikte tuzaktır.

## Veri doğrulama ve belge üretimi — KURULU

| Depo | Paket | Lisans | Not |
|---|---|---|---|
| unionai-oss/pandera | pandera | MIT | import ok |
| python-openxml/python-docx | python-docx | MIT | import ok |
| fivetran/great_expectations | — | Apache-2.0 | kurulmadı, ağır; pandera yetiyor |

`fivetran/great_expectations` ile `great-expectations/great_expectations` aynı
HEAD'e çözülüyor: depo devredilmiş, eski ad yönlendiriyor. **Kitaptaki ad
geçerlidir ve tek geçerli olandır**: GitHub arama uç noktası
`great-expectations/great_expectations` adını artık çözemiyor, yalnızca
`fivetran/great_expectations` çözülüyor (11.743 yıldız, 2026-08-28). Eski adı
bir bağımlılık dosyasına yazan, bir gün çözülmeyen bir ada yazmış olur.

Çalıştırma: `kod/cetvel.py` (pandera şeması), belge üretimi için `docx`.

## Karşı taraf ve açık kaynak istihbaratı — KURULMADI

| Depo | Lisans | Karar |
|---|---|---|
| Panniantong/Agent-Reach | MIT | Çözüldü ama KURULMADI |
| unclecode/crawl4ai | Apache-2.0 | Çözüldü ama KURULMADI |

İkisi de dış servise sorgu gönderir. Sır saklama kuralı gereği bu pratikte
müvekkil, hedef ya da kod adı hiçbir dış aramaya girmez; bu araçların meşru
kullanımı yalnızca soyutlanmış hukuki sorulardır ve o iş için WebSearch zaten
yeterlidir. Agent-Reach ayrıca gerçek hesapla **yazma** fiilleri
(post/comment/follow/delete) taşır; `.claude/settings.json` içinde bu fiiller
yasaklanmıştır — araç kurulmasa bile yasak yerinde durur.

## Token verimliliği — KURULU

Kurulum kitabında yok; bu pratiğe eklendi. Uzun bir SPA'yı ya da bir veri
odasını bağlama sokmanın maliyeti gerçektir ve ölçülmeden yönetilemez.

| Depo | Paket | Lisans | Son commit | Ne yapar |
|---|---|---|---|---|
| openai/tiktoken | tiktoken 0.14.0 | MIT | — | Token sayar |
| simonw/ttok | ttok 0.3 | Apache-2.0 | — | Komut satırından token sayar/kırpar |
| simonw/strip-tags | strip-tags 0.6 | Apache-2.0 | — | HTML etiketlerini atar |
| simonw/files-to-prompt | files-to-prompt 0.6 | Apache-2.0 | — | Klasörü tek isteme çevirir |
| coderamp-labs/gitingest | gitingest 0.3.1 | MIT | 2025-08-16 | Depoyu özet metne indirger |
| yamadashy/repomix | repomix 1.18.0 (npm) | MIT | 2026-08-23 | Depoyu token sayımıyla paketler |
| AgentOps-AI/tokencost | tokencost 0.1.26 | — | — | Maliyet tahmini |
| isaacus-dev/semchunk | semchunk | MIT | — | Anlamsal parçalama |
| chonkie-inc/chonkie | chonkie 1.7.0 | MIT | yıldız ölçülemedi | Parçalama boru hattı |
| microsoft/LLMLingua | llmlingua 0.2.2 | MIT | 2025-10-28 | İstem sıkıştırma |

**Bir tuzak yakalandı ve kaydedilmesi gerekiyor.** PyPI'da `repomix` adında bir
paket vardır (0.5.0) ve GitHub bağlantısı yoktur; gerçek repomix **npm**
paketidir ve `yamadashy/repomix` deposundan gelir. Kitabın §14'te uyardığı
"kayıt adı depo adı olmayabilir" tuzağının bu kurulumdaki canlı örneğidir.
Bu yüzden repomix npm'den kuruldu, PyPI'dan değil.

**Boş bir arama yokluğun kanıtı değildir — bu kurulumda ikinci canlı örnek.**
`chonkie-inc/chonkie` GitHub **arama** uç noktasından çözülmüyor ("bu kaynaklar
mevcut değil" hatası veriyor), ama `git ls-remote` ile **çözülüyor** ve PyPI
kaydı da aynı adresi gösteriyor. Depo vardır; arama indeksinde görünmemektedir.
Kitabın §14'te uyardığı tuzak tam olarak budur: aramanın boş dönmesine bakıp
"böyle bir depo yok" demek. Bu yüzden bu depo için yıldız yazılmamıştır —
ölçülemedi, uydurulmadı.

**Sır saklama kuralı burada da üsttedir.** Bu araçların hepsi yereldir ve hiçbiri
belgeyi dışarı göndermez. llmlingua bir model indirir ve yerel çalışır; müvekkil
metni yine makineden çıkmaz.

Çalıştırma: `kod/token-butce.py`.

## Kurulmayanlar ve nedenleri

- **PyMuPDF** AGPL-3.0'dır. Kurum içinde sorun çıkarmaz; bir şey hizmet olarak
  sunulduğu anda soru gelir. pdfplumber ve docling MIT'tir, bu soruyu doğurmaz.
- **lexpredict-lexnlp** AGPL-3.0'dır. Asıl sahibin kararı olmadan kurulmaz.
- **Ücretli anahtar ya da hesap açılışı** gerektiren her şey, paket kurulumundan
  ayrı bir karardır ve asıl sahibin onayı olmadan yapılmaz.
- **Müvekkil belgesini üçüncü taraf bir uç noktadan geçiren** her araç, yıldız
  sayısı ne olursa olsun reddedilir. Bu, sır saklama kuralıdır ve kolaylık için
  esnetilmez.

## Doğrulama komutu

    python3 ~/mafirm/birimler/_araclar/kod/dogrula.py

Kontrol pip list satırı değil bir `import`tur: bir paket kurulu görünüp import
edilemeyebilir. Bu kurulumda tam olarak bu oldu — `pdfplumber` kuruluydu ama
Debian'ın `cryptography` paketi `_cffi_backend` olmadan geldiği için import
edilemiyordu. Fark yalnızca ona ihtiyaç duyulduğunda ortaya çıkardı.

## Şimdi ne yapılmalı

Bir araç kullanılmadan önce `dogrula.py` çalıştırılır. Kırmızı bir satır varsa o
araca dayanan iş durur.

## Yetkili avukat görüşü gereken konular

AGPL lisanslı bir bileşenin kurulup kurulmayacağı; müvekkil belgesinin herhangi
bir dış uç noktadan geçirilip geçirilemeyeceği; ve bir tarama sonucunun
yorumlanması.
