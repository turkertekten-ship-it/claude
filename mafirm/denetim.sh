#!/usr/bin/env bash
# Pratikteki her sınamayı ve kapıyı çalıştırır. Herhangi biri başarısızsa
# sıfırdan farklı çıkış kodu döner. Kurulumun işe yaradığının tek kanıtı yeşil
# bir denetimdir; bunu çalıştırmadan "bitti" diyen bir kurulum hiçbir şey
# söylememiştir.
#
# KÖR SINAMA SONRASI SÜRÜM. Kitaba sadık sürüm yamalar/kitaba-sadik/denetim.sh.
# Mutasyon sınaması (sinama/ks_d_denetim.sh) kitaba sadık sürümde 15 bozmadan
# 11'inin FARK EDİLMEDİĞİNİ gösterdi: denetim, sıfır beceri / sıfır ajan /
# sıfır komut / kancasız settings.json / BOŞ bir esik.py taşıyan bir sistemde
# "DENETİM OK" diyordu. Sebep üç mekanizmaydı:
#   1. `... | wc -l` boru hattının çıkış kodu daima wc'nindir: 0.
#   2. Boş bir Python dosyası --self-test ile 0 döner.
#   3. `test -z "$(grep -rL ...)"` hiç dosya yokken boş döner ve GEÇER.
# Aşağıdaki her kontrol artık bir EŞİK doğrular, bir sayı yazdırmaz.
set -u
# Kök dizin betiğin KENDİ konumundan çözülür (MAFIRM ile geçersiz kılınabilir).
M="${MAFIRM:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
hata=0
export MAFIRM_KOK="$M"   # gömülü Python parçacıkları köke buradan ulaşır
YAPISAL_SADECE=0
[ "${1:-}" = "--yapisal" ] && YAPISAL_SADECE=1

kontrol() {                      # kontrol "<ad>" "<komut>"
  if out=$(eval "$2" 2>&1); then
    printf "  ok    %-38s %s\n" "$1" "$(echo "$out" | tail -1)"
  else
    printf "  HATA  %-38s %s\n" "$1" "$(echo "$out" | tail -1)"; hata=$((hata+1))
  fi
}

# En az N eşleşen dosya var mı — wc'nin çıkış kodunu YUTMADAN.
enaz() {                         # enaz <sayı> <glob...>
  local n="$1"; shift
  local c; c=$(ls -1 "$@" 2>/dev/null | wc -l)
  [ "$c" -ge "$n" ] && echo "$c dosya" && return 0
  echo "yalnızca $c dosya, en az $n bekleniyor"; return 1
}

# Bir Python dosyası GERÇEKTEN bir öz-sınama çalıştırıyor mu — boş dosya geçmez.
oz_sinama() {                    # oz_sinama <dosya> <beklenen desen>
  local f="$1" desen="$2" cikti
  [ -s "$f" ] || { echo "dosya boş ya da yok: $f"; return 1; }
  cikti=$(python3 "$f" --self-test 2>&1) || { echo "$cikti" | tail -1; return 1; }
  echo "$cikti" | grep -q "$desen" || {
    echo "öz-sınama beklenen '$desen' satırını basmadı"; return 1; }
  echo "$cikti" | tail -1
}

echo "=== yapı ==="
kontrol "işletim sözleşmesi (>=11 kural)" \
  "test -s $M/CLAUDE.md && test \$(grep -c '^## ' $M/CLAUDE.md) -ge 11 && echo \"\$(grep -c '^## ' $M/CLAUDE.md) kural\""
kontrol "uzmanlık birimleri (>=8)" \
  "test \$(ls -d $M/birimler/*/ 2>/dev/null | grep -vc _koltuklar) -ge 8 && echo '8+ birim'"
kontrol "her birimin INDEX.md'si var" \
  "test \$(ls $M/birimler/*/INDEX.md 2>/dev/null | wc -l) -ge 8 && echo 'hepsi'"
kontrol "koltuklar (>=15)"        "enaz 15 $M/birimler/_koltuklar/*.md"
kontrol "boş koltuklar işaretli (>=2)" \
  "test \$(grep -l 'KOLTUK BOŞ' $M/birimler/_koltuklar/*.md 2>/dev/null | wc -l) -ge 2 && echo '2+ işaretli'"

echo "=== kod sınamaları ==="
kontrol "rekabet eşiği" "oz_sinama $M/birimler/rekabet/kod/esik.py 'SELFTEST OK'"
kontrol "altı kapı"     "oz_sinama $M/.claude/hooks/kapi.py 'SELFTEST OK'"

echo "=== bileşenler ==="
kontrol "beceriler (>=11)"        "enaz 11 $M/.claude/skills/*/SKILL.md"
kontrol "alt ajanlar (>=5)"       "enaz 5 $M/.claude/agents/*.md"
kontrol "komutlar (>=9)"          "enaz 9 $M/.claude/commands/*.md"
kontrol "komut kütüphanesi (>=4)" "enaz 4 $M/komutlar/*.md"
kontrol "yöntem dosyaları (>=9)"  "enaz 9 $M/birimler/*/yontem/*.md"

echo "=== kanca gerçekten kayıtlı mı ==="
kontrol "settings.json kancası var" \
  "python3 -c \"import json;d=json.load(open('$M/.claude/settings.json'));h=d['hooks']['PreToolUse'];assert h and h[0]['hooks'];print('kayıtlı')\""
kontrol "matcher Bash'i kapsıyor" \
  "python3 -c \"import json;d=json.load(open('$M/.claude/settings.json'));m=d['hooks']['PreToolUse'][0]['matcher'];assert 'Bash' in m, m;print('Bash kapsanıyor')\""

echo "=== doktrin gerçekten uygulanıyor mu ==="
kontrol "her komut avukat satırını istiyor" \
  "test \$(ls $M/komutlar/*.md 2>/dev/null | wc -l) -ge 4 && test -z \"\$(grep -L 'Yetkili avukat görüşü gereken konular' $M/komutlar/*.md)\" && echo hepsi"
kontrol "her yöntem dosyası tarih taşıyor" \
  "test \$(ls $M/birimler/*/yontem/*.md 2>/dev/null | wc -l) -ge 9 && test -z \"\$(grep -rL 'Doğrulama:' $M/birimler/*/yontem/*.md)\" && echo hepsi"
kontrol "çıkar çatışması dosyası var" \
  "test -s $M/hafiza/cikar-catismasi.md && echo var"
kontrol "her koltuk kaynak beyanı taşıyor" \
  "test \$(ls $M/birimler/_koltuklar/*.md 2>/dev/null | wc -l) -ge 15 && test -z \"\$(grep -LE '^## Kaynak durumu|KOLTUK BOŞ' $M/birimler/_koltuklar/*.md)\" && echo hepsi"
kontrol "koltuk kapısı gerçekten bloklıyor" \
  "python3 -c \"import json,subprocess,sys,os
o={'tool_name':'Write','tool_input':{'file_path':'birimler/_koltuklar/x.md','content':'# X'}}
r=subprocess.run([sys.executable,os.path.join(os.environ['MAFIRM_KOK'],'.claude/hooks/kapi.py')],input=json.dumps(o),capture_output=True,text=True)
assert r.returncode==2, 'beyansız koltuk bloklanmadı'
print('bloklanıyor')\""

kontrol "engelleyici bulgular yerinde işaretli" \
  "python3 - <<'PYX'
import os,re,sys
kok=os.environ['MAFIRM_KOK']
kayit=os.path.join(kok,'hafiza','dogrulama-bulgulari.md')
eksik=[]
for satir in open(kayit,encoding='utf-8'):
    if '| ENGELLEYICI |' not in satir: continue
    alan=[a.strip() for a in satir.split('|')]
    for yol in alan[2].split(' · '):
        t=os.path.join(kok,yol)
        if not os.path.exists(t): eksik.append(yol+' (dosya yok)'); continue
        icerik=open(t,encoding='utf-8').read()
        # İşaret, BULGUYU ADIYLA anmalı. Yoksa aynı dosyadaki başka bir
        # bulgunun işareti hepsini aklıyor — kontrolün kendi kusuruydu.
        if 'DOĞRULANAMADI' not in icerik or alan[0] not in icerik:
            eksik.append(alan[0]+' -> '+yol)
if eksik:
    print('işaretsiz: '+', '.join(eksik)); sys.exit(1)
print('hepsi işaretli')
PYX"

kontrol "errata izlenebilir (her madde bir vakaya bağlı)" \
  "python3 $M/sinama/ks_m_izlenebilirlik.py >/dev/null 2>&1 && echo 'hepsi bağlı'"

kontrol "olumsuz iddia kanıtlı (kural 2)" \
  "python3 $M/sinama/ks_n_olumsuz.py >/dev/null 2>&1 && echo 'kanıtlı'"

# NOT — burada BİLEREK bir kontrol YOK.
# Denetime "sınama takımı beyan edilmiş tabanla eşleşiyor mu" kontrolü eklemek
# denendi ve ÖZYİNELEME ürettti: denetim -> hepsi.sh -> D takımı (mutasyon
# sınaması) -> denetim -> hepsi.sh -> ... Koşum 120 saniyede bitmedi.
# Katman ihlali: denetimi denetleyen takımı denetimin kendisi çağıramaz.
# Taban eşleşmesi hepsi.sh'in KENDİ çıkış kodudur (0 = sinyal yok) ve orada
# kalır; denetim yalnızca kendi katmanına bakar.

# Raporun EL YAZISI sayıları, ölçtükleri şeyden bağımsız bayatlıyor: rapor
# bir kez "on üç bilinen sapma" dedi, gerçek on birdi — kitabın §9'daki
# "10 beceri" beklentisiyle aynı kusur. Yalnızca DURAĞAN olarak türetilebilen
# şey burada kontrol edilir; vaka sayıları hepsi.sh'in kendi çıktısıdır ve
# oradan çağrılırsa yukarıda anlatılan özyineleme geri gelir.
kontrol "raporun beyan sayısı beklenen.json ile uyuşuyor" \
  "MAFIRM_KOK='$M' python3 - <<'PYX'
import json, os, re, sys
kok = os.environ['MAFIRM_KOK']
n = len(json.load(open(kok + '/sinama/beklenen.json', encoding='utf-8'))['vakalar'])
metin = open(kok + '/RAPOR.md', encoding='utf-8').read()
SAYI = {'on': 10, 'on bir': 11, 'on iki': 12, 'on üç': 13, 'on dört': 14,
        'on beş': 15, 'on altı': 16, 'dokuz': 9, 'sekiz': 8}
m = re.search(r'\*\*([A-Za-zÇĞİÖŞÜçğıöşü ]+?)\*\*\s*\n?bilinen sapma', metin)
if not m:
    print('raporda beyan cümlesi bulunamadı'); sys.exit(1)
yazi = m.group(1).strip().lower()
d = SAYI.get(yazi)
if d is None:
    print('sayı sözcüğü çözülemedi: ' + yazi); sys.exit(1)
if d != n:
    print('rapor %d diyor, beklenen.json %d taşıyor' % (d, n)); sys.exit(1)
print('%d = %d' % (d, n))
PYX"

# [X] Raporun VAKA SAYISI kontrolü bilerek BURADA DEĞİL.
# Denendi ve iki kez katman ihlali üretti: denetim, hepsi.sh'in yazdığı kaydı
# okuyunca (a) yönlendirme dosyası kesilirken yarım kaydı gördü, (b) ayrı bir
# kayda geçilince de bir ÖNCEKİ koşumu okudu — yani sayı değiştiğinde bir
# koşum kırmızı, ikincisi yeşil oluyordu. İki koşumda yakınsayan bir kontrol,
# okuyucuya "kırmızıysa bir daha koş" alışkanlığı öğretir; bu takımın tüm
# amacının tersi. Kontrol, gerçek toplamı ZATEN bilen tek yere taşındı:
# hepsi.sh'in kendi kapanışına.

kontrol "her sınama takımı raporun tablosunda anılıyor" \
  "MAFIRM_KOK='$M' python3 - <<'PYX'
import glob, os, re, sys
kok = os.environ['MAFIRM_KOK']
metin = open(kok + '/RAPOR.md', encoding='utf-8').read()
harfler = sorted({os.path.basename(p).split('_')[1].upper()
                  for p in glob.glob(kok + '/sinama/ks_*')
                  if re.match(r'ks_[a-z]_', os.path.basename(p))})
eksik = [h for h in harfler if not re.search(r'^\| %s \|' % h, metin, re.M)]
if eksik:
    print('tabloda yok: ' + ', '.join(eksik)); sys.exit(1)
print('%d takımın hepsi tabloda' % len(harfler))
PYX"

kontrol "teslimatlar tarih ve bozulma sınıfı taşıyor" \
  "python3 $M/sinama/ks_p_guncellik.py >/dev/null 2>&1 && echo 'hepsi tarihli'"

echo "=== kapsanmayan kurallar sesli bildirilir ==="
adet=$(grep -cve '^[[:space:]]*#' -e '^[[:space:]]*$' "$M/hafiza/muvekkil-adlari.txt" 2>/dev/null | head -1)
adet=${adet:-0}
if [ "$adet" -eq 0 ]; then
  echo "  UYARI müvekkil ad kaydı BOŞ — kural 6'nın gerçek kişi ayağı kapsanmıyor"
  # [Y-05] "Doldur" demek, korumayı söylemeden TEHLİKELİDİR: kullanıcı gerçek
  # adları §2'nin `git init` ettiği bir depoya yazar ve ilk push kural 6'yı
  # çiğner. Talimatla birlikte koruma da söylenir.
  echo "        Doldurmadan önce: bu dosya .gitignore ile DIŞLANMIŞTIR ve"
  echo "        depoya girmez (izlenen sürüm hafiza/muvekkil-adlari.ornek.txt)."
else
  printf "  ok    %-38s %s\n" "müvekkil ad kaydı" "$adet ad"
  # [Y-05] Koruma cümlesi ÖNCE yalnızca "boş" dalında yazılıyordu. Oysa dosya
  # DOLUYKEN daha da gereklidir: içinde gerçek adlar vardır. Mutasyon bunu
  # gösterdi — kayıt doldurulunca cümle ortadan kalkıyordu.
  echo "        Bu dosya .gitignore ile DIŞLANMIŞTIR ve depoya girmez."
  echo "        İzlenen sürüm: hafiza/muvekkil-adlari.ornek.txt"
fi

# [W-02] §2 `emsal/` dizinini "onaylı madde bankası" olarak açıyor, §10
# emsal-bulucu'yu yalnızca orayı aramak üzere görevlendiriyor, §14
# once-arastir'ın üçüncü adımını oraya yönlendiriyor — ve bankayı hiç
# doldurmuyor. Boş bir bankada arama yapan ajan "emsal yok" der; okuyucu bunu
# dünyaya dair bir tespit sanır. §14'ün kendi kuralı: "Boş bir arama yokluğun
# kanıtı değildir." Boş müvekkil ad kaydıyla aynı kusur, ikinci yerde.
emsal_adet=$(find "$M/emsal" "$M"/birimler/*/emsal -type f ! -name '.*' 2>/dev/null | wc -l)
if [ "$emsal_adet" -eq 0 ]; then
  echo "  UYARI emsal (onaylı madde bankası) BOŞ — emsal-bulucu'nun"
  echo "        'emsal yok' cevabı DÜNYAYA değil BOŞ DOLABA dairdir"
else
  printf "  ok    %-38s %s\n" "onaylı madde bankası" "$emsal_adet madde"
fi

echo "=== açık doğrulama bulguları ==="
if [ -f "$M/hafiza/dogrulama-bulgulari.md" ]; then
  eng=$(grep -c '| ENGELLEYICI |' "$M/hafiza/dogrulama-bulgulari.md" | head -1); eng=${eng:-0}
  tum=$(grep -cE '^[A-Z]-[0-9]+ \|' "$M/hafiza/dogrulama-bulgulari.md" | head -1); tum=${tum:-0}
  echo "  $tum açık bulgu, $eng tanesi ENGELLEYİCİ"
  grep '| ENGELLEYICI |' "$M/hafiza/dogrulama-bulgulari.md" \
    | cut -d'|' -f1,4 | sed 's/^/    /'
  if [ "$eng" -gt 0 ] && [ "$YAPISAL_SADECE" -eq 0 ]; then
    hata=$((hata + eng))
    echo "  Bunlar KOD hatası değildir; birincil kaynak açılıp teyit edilene"
    echo "  kadar açık kalır. Bir eşik değişikliği insan kararıdır (§11)."
  fi
fi

echo
if [ "$hata" -eq 0 ]; then echo "DENETİM OK"; else echo "DENETİM BAŞARISIZ: $hata"; fi
exit "$hata"
