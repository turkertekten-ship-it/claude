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
r=subprocess.run([sys.executable,os.path.expanduser('~/mafirm/.claude/hooks/kapi.py')],input=json.dumps(o),capture_output=True,text=True)
assert r.returncode==2, 'beyansız koltuk bloklanmadı'
print('bloklanıyor')\""

echo "=== kapsanmayan kurallar sesli bildirilir ==="
adet=$(grep -cve '^[[:space:]]*#' -e '^[[:space:]]*$' "$M/hafiza/muvekkil-adlari.txt" 2>/dev/null | head -1)
adet=${adet:-0}
if [ "$adet" -eq 0 ]; then
  echo "  UYARI müvekkil ad kaydı BOŞ — kural 6'nın gerçek kişi ayağı kapsanmıyor"
else
  printf "  ok    %-38s %s\n" "müvekkil ad kaydı" "$adet ad"
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
