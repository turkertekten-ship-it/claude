#!/usr/bin/env bash
# Pratikteki her sınamayı ve kapıyı çalıştırır. Herhangi biri başarısızsa
# sıfırdan farklı çıkış kodu döner. Kurulumun işe yaradığının tek kanıtı yeşil
# bir denetimdir; bunu çalıştırmadan "bitti" diyen bir kurulum hiçbir şey
# söylememiştir.
set -u
hata=0

kontrol() {                      # kontrol "<ad>" "<komut>"
  if out=$(eval "$2" 2>&1); then
    printf "  ok    %-36s %s\n" "$1" "$(echo "$out" | tail -1)"
  else
    printf "  HATA  %-36s %s\n" "$1" "$(echo "$out" | tail -1)"; hata=$((hata+1))
  fi
}

echo "=== yapı ==="
kontrol "işletim sözleşmesi" "test -f ~/mafirm/CLAUDE.md && grep -c '^## ' ~/mafirm/CLAUDE.md"
kontrol "uzmanlık birimleri" "test \$(ls -d ~/mafirm/birimler/*/ | wc -l) -ge 8 && echo 8+"
kontrol "boş koltuklar işaretli" "grep -l 'KOLTUK BOŞ' ~/mafirm/birimler/_koltuklar/*.md | wc -l"

echo "=== kod sınamaları ==="
kontrol "rekabet eşiği" "python3 ~/mafirm/birimler/rekabet/kod/esik.py --self-test"
kontrol "beş kapı"      "python3 ~/mafirm/.claude/hooks/kapi.py --self-test"
kontrol "araç katmanı"  "python3 ~/mafirm/birimler/_araclar/kod/dogrula.py | tail -1"
kontrol "iç yönlendirme" "python3 ~/mafirm/birimler/_araclar/kod/yonlendirme.py"

echo "=== bileşenler ==="
kontrol "beceriler" "ls ~/mafirm/.claude/skills/*/SKILL.md | wc -l"
kontrol "alt ajanlar" "ls ~/mafirm/.claude/agents/*.md | wc -l"
kontrol "komutlar" "ls ~/mafirm/.claude/commands/*.md | wc -l"
kontrol "komut kütüphanesi" "ls ~/mafirm/komutlar/*.md | wc -l"
kontrol "iş akışları" "ls ~/mafirm/isakislari/*.md | wc -l"

echo "=== doktrin gerçekten uygulanıyor mu ==="
kontrol "her komut avukat satırını istiyor" \
  "test -z \"\$(grep -L 'Yetkili avukat görüşü gereken konular' ~/mafirm/komutlar/*.md)\" && echo hepsi"
kontrol "her iş akışı avukat satırını istiyor" \
  "test -z \"\$(grep -L 'Yetkili avukat görüşü gereken konular' ~/mafirm/isakislari/0*.md)\" && echo hepsi"
kontrol "her eşik dosyası tarih taşıyor" \
  "test -z \"\$(grep -rL 'Doğrulama:' ~/mafirm/birimler/*/yontem/*.md)\" && echo hepsi"
kontrol "her yöntem dosyası araştırma satırı taşıyor" \
  "test -z \"\$(grep -rL 'Kontrol edildi:' ~/mafirm/birimler/*/yontem/*.md)\" && echo hepsi"
kontrol "sınır beyanı var" "test -f ~/mafirm/SINIRLAR.md && grep -c '^## ' ~/mafirm/SINIRLAR.md"
kontrol "çıkar çatışması kaydı var" "test -f ~/mafirm/hafiza/cikar-catismasi.md && echo var"
kontrol "boş koltuk sayısı tam iki" \
  "test \$(grep -l 'KOLTUK BOŞ' ~/mafirm/birimler/_koltuklar/*.md | wc -l) -eq 2 && echo 2"

echo
if [ "$hata" -eq 0 ]; then echo "DENETİM OK"; else echo "DENETİM BAŞARISIZ: $hata"; fi
exit "$hata"
