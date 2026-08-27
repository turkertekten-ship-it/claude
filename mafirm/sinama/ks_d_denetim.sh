#!/usr/bin/env bash
# KÖR SINAMA D — denetim.sh MUTASYON SINAMASI (v2, kontrollü)
#
# v1 GEÇERSİZDİ: taban çizgisi zaten kırmızıydı (§14'ün bozduğu öz-sınama
# yüzünden), dolayısıyla her mutasyon koşusu sıfırdan farklı dönüyordu ve
# "yakalandı" ölçümü anlamsızdı. Bir mutasyon sınaması YEŞİL bir taban
# çizgisi gerektirir; yoksa ölçtüğü şey mutasyon değil, önceden var olan
# arızadır.
#
# v2: kum havuzunda önce §14 arızası onarılır (yalnızca iki bayat beklenen
# küme düzeltilir), taban çizgisinin YEŞİL olduğu doğrulanır, sonra mutasyon
# uygulanır. Ölçülen şey artık yalnızca mutasyonun etkisidir.
set -u
KAYNAK="${MAFIRM:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
KUM="${TMPDIR:-/tmp}/ks_d_kum"
gecti=0; kaldi=0

kur() {
  rm -rf "$KUM"; mkdir -p "$KUM"
  cp -a "$KAYNAK/." "$KUM/"
  # Denetim betiğini kum havuzuna yönlendir. İKİ biçim de değiştirilir:
  # kitaba sadık sürüm literal ~/mafirm kullanıyordu, yamalı sürüm M="${MAFIRM:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}".
  sed -e "s#~/mafirm#$KUM#g" \
      -e "s#^M=.*#M=\"$KUM\"#" \
      "$KAYNAK/denetim.sh" > "$KUM/denetim.sh"
  # Yönlendirmenin gerçekten tuttuğunu doğrula; tutmazsa mutasyon sınaması
  # asıl kurulumu ölçer ve her mutasyonu "kaçırmış" görünür.
  if ! grep -q "^M=\"$KUM\"" "$KUM/denetim.sh"; then
    echo "KUM HAVUZU YÖNLENDİRMESİ BAŞARISIZ — sınama geçersiz olurdu"; exit 98
  fi
  chmod +x "$KUM/denetim.sh"
  # KONTROL: §14'ün bıraktığı iki bayat beklenen kümeyi onar ki taban yeşil olsun
  python3 - "$KUM" <<'PY'
import sys, io
p = sys.argv[1] + "/.claude/hooks/kapi.py"
s = open(p, encoding="utf-8").read()
s = s.replace('''("Eşik, birleşik ciro için 3.000.000.000 TL'dir.", False, {"kanit"}),''',
              '''("Eşik, birleşik ciro için 3.000.000.000 TL'dir.", False, {"kanit", "arastirma"}),''')
s = s.replace('''("2010/4 sayılı Tebliğ eşiği 3.000.000.000 TL olarak belirler.",
         False, set()),''',
              '''("2010/4 sayılı Tebliğ eşiği 3.000.000.000 TL olarak belirler.",
         False, {"arastirma"}),''')
open(p, "w", encoding="utf-8").write(s)
PY
}

mutasyon() {
  local ad="$1" boz="$2"
  kur
  eval "$boz" >/dev/null 2>&1
  local out rc
  out=$("$KUM/denetim.sh" --yapisal 2>&1); rc=$?
  if [ "$rc" -ne 0 ]; then
    printf "  YAKALADI  %-44s\n" "$ad"; gecti=$((gecti+1))
  else
    printf "  KAÇIRDI   %-44s  << DENETİM OK — bozuk sistemde\n" "$ad"; kaldi=$((kaldi+1))
  fi
}

echo "======================================================================="
echo "KÖR SINAMA D — denetim.sh mutasyon sınaması (kontrollü taban çizgisi)"
echo "======================================================================="
echo
echo "--- taban çizgisi doğrulaması ---"
kur
base_out=$("$KUM/denetim.sh" --yapisal 2>&1); base_rc=$?
echo "$base_out" | tail -1
if [ "$base_rc" -ne 0 ]; then
  echo "  TABAN ÇİZGİSİ YEŞİL DEĞİL — mutasyon sınaması geçersiz olurdu. Durum: $base_rc"
  exit 99
fi
echo "  taban çizgisi yeşil (çıkış 0) — mutasyonlar artık ölçülebilir"
echo
echo "--- mutasyonlar: her biri denetimi KIRMIZIYA çevirmeli ---"

mutasyon "bütün becerileri sil"              "rm -rf $KUM/.claude/skills/*"
mutasyon "bütün alt ajanları sil"            "rm -f $KUM/.claude/agents/*.md"
mutasyon "bütün komutları sil"               "rm -f $KUM/.claude/commands/*.md"
mutasyon "komut kütüphanesini sil"           "rm -f $KUM/komutlar/*.md"
mutasyon "iki boş koltuğu da sil"            "rm -f $KUM/birimler/_koltuklar/turk-hukukcu.md $KUM/birimler/_koltuklar/vergi.md"
mutasyon "CLAUDE.md'yi tek kurala indir"     "printf '# x\n\n## 1. Kanit\nvar\n' > $KUM/CLAUDE.md"
mutasyon "bütün yöntem dosyalarını sil"      "rm -f $KUM/birimler/*/yontem/*.md"
mutasyon "eşik dosyasından tarihi sil"       "sed -i '/^Doğrulama:/d' $KUM/birimler/rekabet/yontem/tr-esikler.md"
mutasyon "bir komuttan avukat başlığını sil" "sed -i 's/Yetkili avukat görüşü gereken konular/Notlar/' $KUM/komutlar/15-1-esik-sorusu.md"
mutasyon "esik.py eşiğini 10 kat büyüt"      "sed -i 's/BIRLESIK_TR = 3_000_000_000/BIRLESIK_TR = 30_000_000_000/' $KUM/birimler/rekabet/kod/esik.py"
mutasyon "sır kapısını sessizce kapat"       "sed -i 's/^    if not disari:/    return None\n    if not disari:/' $KUM/.claude/hooks/kapi.py"
mutasyon "çıkar çatışması dosyasını sil"     "rm -f $KUM/hafiza/cikar-catismasi.md"
mutasyon "settings.json kancasını kaldır"    "printf '{}' > $KUM/.claude/settings.json"
mutasyon "koltuk dosyalarının 13'ünü sil"    "ls $KUM/birimler/_koltuklar/*.md | grep -v 'turk-hukukcu\|vergi' | xargs rm -f"
mutasyon "esik.py'yi tamamen boşalt"         "printf '' > $KUM/birimler/rekabet/kod/esik.py"

echo
echo "-----------------------------------------------------------------------"
echo "$((gecti+kaldi)) mutasyon · $gecti yakalandı · $kaldi KAÇIRILDI"
exit "$kaldi"
