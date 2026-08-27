#!/usr/bin/env bash
# KÖR SINAMA E — kitabın kendi doğrulama komutları, kendi beklenen değerlerine karşı.
# Kitap on dokuz bölümde doğrulama komutu veriyor ve bir kısmında BEKLENEN bir
# değer yazıyor. Bu takım her komutu çalıştırır ve yazılı beklenen değerle
# karşılaştırır. Kurulum kitaba SADIK yapıldı; sapma varsa kaynağı kitaptadır.
set -u
M="${MAFIRM:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
gecti=0; kaldi=0

kontrol() {   # kontrol "<bölüm>" "<beklenen>" "<gerçek>" "<not>"
  if [ "$2" = "$3" ]; then
    printf "  GEÇTİ  %-8s beklenen=%-14s gerçek=%-14s\n" "$1" "$2" "$3"; gecti=$((gecti+1))
  else
    printf "  KALDI  %-8s beklenen=%-14s gerçek=%-14s  %s\n" "$1" "$2" "$3" "$4"; kaldi=$((kaldi+1))
  fi
}

echo "======================================================================="
echo "KÖR SINAMA E — kitabın doğrulama komutları vs kitabın beklenen değerleri"
echo "======================================================================="
echo

kontrol "§3" "11" "$(grep -c '^## ' "$M/CLAUDE.md")" \
  "§14 kural 11'i yeniden yazdırıyor; eklenirse 12 olur, hiçbir kontrol bakmaz"

kontrol "§4" "8" "$(ls "$M/birimler/" | wc -l | tr -d ' ')" \
  "§7 _koltuklar/ ekliyor; §4'ün beklenen değeri bayatlıyor"

kontrol "§5.1" "SELFTEST OK" \
  "$(python3 "$M/birimler/rekabet/kod/esik.py" --self-test | grep -o 'SELFTEST OK' || echo 'SELFTEST HATA')" ""

kontrol "§7" "2" "$(grep -l 'KOLTUK BOŞ' "$M"/birimler/_koltuklar/*.md | wc -l | tr -d ' ')" ""

kontrol "§8" "2" "$(ls "$M"/birimler/sinir-otesi/yontem/elkitabi-*.md | wc -l | tr -d ' ')" ""

kontrol "§9" "10" "$(ls "$M"/.claude/skills/*/SKILL.md | wc -l | tr -d ' ')" \
  "§14 once-arastir becerisini ekliyor; §9'un beklenen değeri bayatlıyor"

kontrol "§10" "1" "$(grep -c '^tools:' "$M/.claude/agents/inceleme-okuyucu.md")" ""

kontrol "§11" "9" "$(ls "$M"/.claude/commands/*.md | wc -l | tr -d ' ')" ""

kontrol "§12/§14" "SELFTEST OK" \
  "$(python3 "$M/.claude/hooks/kapi.py" --self-test 2>&1 | grep -o 'SELFTEST OK' || echo 'SELFTEST HATA')" \
  "§14 beşinci kapıyı ekliyor ama §12'nin dokuz beklenen kümesini güncellemiyor"

kontrol "§14b" "1" "$(grep -c 'Kontrol edildi:' "$M/.claude/skills/once-arastir/SKILL.md")" ""

kontrol "§15" "boş" "$(grep -L 'Yetkili avukat görüşü gereken konular' "$M"/komutlar/*.md | wc -l | sed 's/^0$/boş/' | tr -d ' ')" ""

kontrol "§16" "DENETİM OK" \
  "$("$M/denetim.sh" 2>&1 | tail -1 | grep -o 'DENETİM OK' || echo 'BAŞARISIZ')" \
  "kitaba sadık, eksiksiz kurulum yeşile dönmüyor"

echo
echo "--- §13 katalog import kontrolü (kitabın kendi komutu) ---"
python3 - <<'PY'
import importlib
for m in ("docling", "pdfplumber", "pandera", "nomenklatura", "docx"):
    try:
        importlib.import_module(m); print("  %-14s ok" % m)
    except ImportError:
        print("  %-14s KURULU DEĞİL" % m)
PY

echo
echo "-----------------------------------------------------------------------"
echo "$((gecti+kaldi)) doğrulama · $gecti geçti · $kaldi KALDI"
exit "$kaldi"
