# Birincil kaynak erişimi — OLUMSUZ İDDİANIN KANITI

İşletim sözleşmesi §2: *"Olumsuz iddia, olumludan daha yüksek bir kanıt eşiği
ister; çünkü okuyucu onu tek bir aramayla doğrulayamaz. Olumsuz iddia ancak o
yükümlülüğü getirecek olan hükmü göstererek ve nereye bakıldığını söyleyerek
yazılır."*

Bu rapor şu olumsuz iddiayı taşıyor: **"Bu ortamda hiçbir birincil kaynağa
erişilemedi."** İlk dört turda bu iddia yalnızca iki araç hatasına
dayanıyordu — yani kendi kuralımı çiğniyordum. Aşağıda gereken kanıt var.

## Nereye bakıldı

| Kanal | Nasıl denendi | Sonuç |
|---|---|---|
| WebFetch aracı | `mevzuat.gov.tr` (kanun metni PDF'i) | `EGRESS_BLOCKED` |
| WebFetch aracı (alt ajan) | sagepub, ssrn, doi.org, crossref, openalex, arxiv, hbs.edu, lexpera, resmigazete, rekabet, spk | hepsi reddedildi |
| **Bash + curl** (hiç denenmemiş kanal) | dört Türk birincil kaynağı | **CONNECT tunnel failed, 403** |
| Vekil durum uç noktası | `$HTTPS_PROXY/__agentproxy/status` | dört ret makinece kaydedildi |
| WebSearch | aynı alan adları | **çalışıyor** — ama sayfa METNİNİ değil arama motoru özetini döndürür |

## Yükümlülüğü getiren hüküm

Ortamın kendi belgesi (`/root/.ccr/README.md`), bu kodun anlamını tanımlıyor:

> **403 / 407 from the proxy** — The destination host is not allowed by your
> organization's egress policy for this session. Do not retry or route around
> it — report the blocked host.

Yani bu bir geçici arıza ya da yanlış yapılandırma değil, bir **kuruluş egress
politikası reddi**dir; ve doğru davranış onu aşmak değil, bildirmektir.

## Makinece kaydedilmiş ret kaydı

Vekilin kendi kaydından (`hafiza/egress-kaniti.json`), 2026-08-28T07:43Z:

```
connect_rejected  www.mevzuat.gov.tr:443     gateway answered 403 to CONNECT
connect_rejected  www.rekabet.gov.tr:443     gateway answered 403 to CONNECT
connect_rejected  www.resmigazete.gov.tr:443 gateway answered 403 to CONNECT
connect_rejected  www.spk.gov.tr:443         gateway answered 403 to CONNECT
```

Vekil `enabled=True, selective=False, toolScoped=False` — yani ret araca özgü
değil, oturum geneli.

## İddianın kesin biçimi

Genel "erişilemedi" değil, şu:

> Bu oturumda `mevzuat.gov.tr`, `rekabet.gov.tr`, `resmigazete.gov.tr` ve
> `spk.gov.tr` alan adlarına HTTPS bağlantısı, kuruluş egress politikası
> tarafından CONNECT aşamasında 403 ile reddedilmiştir; ret hem araç
> düzeyinde hem ham curl ile, hem de vekilin kendi kaydında doğrulanmıştır.
> WebSearch bu alan adları için ÇALIŞMAKTADIR ve kullanılmıştır; döndürdüğü
> şey sayfa metni değil arama motoru özetidir — bu yüzden I-01, I-02 ve I-03
> "desteklenmiş yeniden kurgu"dur, birincil doğrulama değildir.

## Bunun kapatmadığı şey
Bu kanıt, üç mevzuat bulgusunu ÇÖZMÜYOR. Yalnızca neden çözülemediğini
doğrulanabilir hâle getiriyor. Bulgular ENGELLEYİCİ kalır.
