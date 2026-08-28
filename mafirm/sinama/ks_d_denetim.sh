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

# [AT-01 · otuz sekizinci tur] Üçüncü argüman: mutasyonun HEDEF KONTROLÜ.
#
# Eski hâl yalnızca denetimin çıkış koduna bakıyordu — yani "denetim kırmızıya
# döndü mü". Ölçüldü ki bu yetmiyor: "bütün becerileri sil" mutasyonu hem
# `beceriler (>=11)` hem de ALAKASIZ bir kontrolü (`engelleyici bulgular
# yerinde işaretli`) kırmızıya çeviriyor. Yani bir mutasyon, hedeflediği
# kontrol hiç çalışmasa bile "YAKALADI" sayılabilirdi. Bu, kitabın §16
# denetiminde bulduğum kusurun ölçüm tarafındaki hâli: iddia ettiği şeye
# bakmayan bir kontrol.
#
# Artık her mutasyon HANGİ kontrolü kırmızıya çevirmesi gerektiğini beyan
# eder ve o kontrolün HATA verdiği doğrulanır.
mutasyon() {
  local ad="$1" boz="$2" hedef="$3"
  kur
  eval "$boz" >/dev/null 2>&1
  local out rc
  # [AC sınıfı · otuz sekizinci tur] MAFIRM kum havuzuna SABİTLENİR.
  # Ölçüldü: dışarıdan MAFIRM verilmişse (hepsi.sh ve AF öyle yapıyor) kum
  # havuzundaki denetim.sh onu miras alıyor ve CANLI ağacı denetliyordu.
  # Denetimin üç kontrolü Python takımlarına devrediyor; o takımlar da kökü
  # MAFIRM'den çözüyor. Sonuç: kum havuzuna uygulanan mutasyon görünmüyordu
  # ve üç mutasyon "KAÇIRDI" veriyordu — çıplak koşumda 27/27, MAFIRM'li
  # koşumda 24/27. Takımın verdiği cevap ÇAĞIRANIN ORTAMINA bağlıydı.
  out=$(MAFIRM="$KUM" "$KUM/denetim.sh" --yapisal 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then
    printf "  KAÇIRDI   %-44s  << DENETİM OK — bozuk sistemde\n" "$ad"
    kaldi=$((kaldi+1)); return
  fi
  if [ -n "$hedef" ] && ! echo "$out" | grep -qF "HATA  $hedef"; then
    printf "  YANLIŞ    %-44s  << kırmızı, ama hedef kontrol değil: %s\n" \
           "$ad" "$hedef"
    kaldi=$((kaldi+1)); return
  fi
  printf "  YAKALADI  %-44s\n" "$ad"; gecti=$((gecti+1))
}

echo "======================================================================="
echo "KÖR SINAMA D — denetim.sh mutasyon sınaması (kontrollü taban çizgisi)"
echo "======================================================================="
echo
echo "--- taban çizgisi doğrulaması ---"
kur
base_out=$(MAFIRM="$KUM" "$KUM/denetim.sh" --yapisal 2>&1); base_rc=$?
echo "$base_out" | tail -1
if [ "$base_rc" -ne 0 ]; then
  echo "  TABAN ÇİZGİSİ YEŞİL DEĞİL — mutasyon sınaması geçersiz olurdu. Durum: $base_rc"
  exit 99
fi
echo "  taban çizgisi yeşil (çıkış 0) — mutasyonlar artık ölçülebilir"
echo
echo "--- mutasyonlar: her biri denetimi KIRMIZIYA çevirmeli ---"

mutasyon "bütün becerileri sil"              "rm -rf $KUM/.claude/skills/*" "beceriler (>=11)"
mutasyon "bütün alt ajanları sil"            "rm -f $KUM/.claude/agents/*.md" "alt ajanlar (>=5)"
mutasyon "bütün komutları sil"               "rm -f $KUM/.claude/commands/*.md" "komutlar (>=9)"
mutasyon "komut kütüphanesini sil"           "rm -f $KUM/komutlar/*.md" "komut kütüphanesi (>=4)"
mutasyon "iki boş koltuğu da sil"            "rm -f $KUM/birimler/_koltuklar/turk-hukukcu.md $KUM/birimler/_koltuklar/vergi.md" "boş koltuklar işaretli (>=2)"
mutasyon "CLAUDE.md'yi tek kurala indir"     "printf '# x\n\n## 1. Kanit\nvar\n' > $KUM/CLAUDE.md" "işletim sözleşmesi (>=11 kural)"
mutasyon "bütün yöntem dosyalarını sil"      "rm -f $KUM/birimler/*/yontem/*.md" "yöntem dosyaları (>=9)"
mutasyon "eşik dosyasından tarihi sil"       "sed -i '/^Doğrulama:/d' $KUM/birimler/rekabet/yontem/tr-esikler.md" "her yöntem dosyası tarih taşıyor"
mutasyon "bir komuttan avukat başlığını sil" "sed -i 's/Yetkili avukat görüşü gereken konular/Notlar/' $KUM/komutlar/15-1-esik-sorusu.md" "her komut avukat satırını istiyor"
mutasyon "esik.py eşiğini 10 kat büyüt"      "sed -i 's/BIRLESIK_TR = 3_000_000_000/BIRLESIK_TR = 30_000_000_000/' $KUM/birimler/rekabet/kod/esik.py" "rekabet eşiği"
mutasyon "sır kapısını sessizce kapat"       "sed -i 's/^    if not disari:/    return None\n    if not disari:/' $KUM/.claude/hooks/kapi.py" "yedi kapı"
mutasyon "çıkar çatışması dosyasını sil"     "rm -f $KUM/hafiza/cikar-catismasi.md" "çıkar çatışması dosyası var"
mutasyon "settings.json kancasını kaldır"    "printf '{}' > $KUM/.claude/settings.json" "settings.json kancası var"
mutasyon "koltuk dosyalarının 13'ünü sil"    "ls $KUM/birimler/_koltuklar/*.md | grep -v 'turk-hukukcu\|vergi' | xargs rm -f" "koltuklar (>=15)"
mutasyon "esik.py'yi tamamen boşalt"         "printf '' > $KUM/birimler/rekabet/kod/esik.py" "rekabet eşiği"

# [AT-01 · otuz sekizinci tur] ÖLÇÜLDÜ: yukarıdaki on beş mutasyon
# denetimin 26 kontrolünden yalnızca 17'sini kırmızıya çeviriyordu. Dokuzu
# hiçbir mutasyonla sınanmamıştı — yani "hiçbir koşulda başarısız olamaz"
# olup olmadıkları BİLİNMİYORDU. Bu, raporun ÜÇÜNCÜ bulgusunun (kitabın on
# bir kontrolünden altısı hiçbir koşulda başarısız olamaz) ölçüm tarafındaki
# hâlidir: kitabı bu ölçütle eleştirirken kendi denetimimin dokuz kontrolünü
# aynı ölçüte tabi tutmamıştım. Aşağıdaki dokuz mutasyon o boşluğu kapatır.
mutasyon "üç uzmanlık birimini sil" \
  "ls -d $KUM/birimler/*/ | grep -v _koltuklar | head -3 | xargs rm -rf" \
  "uzmanlık birimleri (>=8)"
mutasyon "bir birimin INDEX.md'sini sil" \
  "rm -f \$(ls $KUM/birimler/*/INDEX.md | head -1)" \
  "her birimin INDEX.md'si var"
mutasyon "koltuk kapısını sessizce kapat" \
  "python3 - <<'PZ'
import io
p = '$KUM/.claude/hooks/kapi.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('def kapi_koltuk(metin, yol=None):',
              'def kapi_koltuk(metin, yol=None):\n    return None')
io.open(p, 'w', encoding='utf-8').write(s)
PZ" \
  "koltuk kapısı gerçekten bloklıyor"
mutasyon "matcher'dan Bash'i çıkar" \
  "python3 - <<'PZ'
import io, json
p = '$KUM/.claude/settings.json'
d = json.load(io.open(p, encoding='utf-8'))
t = json.dumps(d).replace('|Bash', '').replace('Bash|', '')
io.open(p, 'w', encoding='utf-8').write(t)
PZ" \
  "matcher Bash'i kapsıyor"
mutasyon "errata'ya uydurma vaka kimliği ekle" \
  "printf '\n**[A] Uydurma madde.** Bu madde hiç var olmayan bir vakaya dayanır. *(ZZ-99)*\n\n→CEVAP: YOK — sınama mutasyonu.\n' >> $KUM/KITAP-ERRATA.md" \
  "errata izlenebilir (her madde bir vakaya bağlı)"
mutasyon "raporun beyan sayısını boz" \
  "sed -i 's/\*\*On iki\*\*/**On dokuz**/' $KUM/RAPOR.md" \
  "raporun beyan sayısı beklenen.json ile uyuşuyor"
mutasyon "tabloda anılmayan bir takım ekle" \
  "printf 'x=1\n' > $KUM/sinama/ks_zz_uydurma.py" \
  "her sınama takımı raporun tablosunda anılıyor"
mutasyon "bir teslimattan doğrulama tarihini sil" \
  "sed -i '0,/Doğrulama:/s/Doğrulama:/x:/' $KUM/hafiza/arac-katalogu.md" \
  "teslimatlar tarih ve bozulma sınıfı taşıyor"
mutasyon "kimlik yolunu .gitignore'dan çıkar" \
  "sed -i '/^hafiza\/muvekkil-adlari.txt$/d' $KUM/.gitignore" \
  "kimlik taşıyan yollar .gitignore'da"

# [AT-01] Üç kontrol daha: ölçümde YAN ETKİ olarak kırmızıya dönüyorlardı ama
# hiçbir mutasyonun BEYAN EDİLMİŞ hedefi değillerdi. Yan etkiyle kırmızıya
# dönmek, kontrolün sınandığını göstermez — hangi kontrolün çalıştığını
# bilmeden okunan bir mutasyon, iddia ettiği şeye bakmayan bir kontroldür.
mutasyon "bir koltuktan kaynak beyanını sil" \
  "python3 - <<'PZ'
import glob, io, re
for y in sorted(glob.glob('$KUM/birimler/_koltuklar/*.md')):
    s = io.open(y, encoding='utf-8').read()
    if '## Kaynak durumu' in s and 'KOLTUK BOŞ' not in s:
        i = s.index('## Kaynak durumu')
        j = s.find('##', i + 4)
        io.open(y, 'w', encoding='utf-8').write(s[:i] + (s[j:] if j > 0 else ''))
        break
PZ" \
  "her koltuk kaynak beyanı taşıyor"
mutasyon "engelleyici bulgu işaretini sil" \
  "sed -i 's/DOĞRULANAMADI/x/g' $KUM/birimler/rekabet/yontem/tr-esikler.md" \
  "engelleyici bulgular yerinde işaretli"
mutasyon "egress kanıtını boşalt" \
  "printf '# bos\n' > $KUM/hafiza/egress-kaniti.md" \
  "olumsuz iddia kanıtlı (kural 2)"

echo
echo "-----------------------------------------------------------------------"
echo "$((gecti+kaldi)) mutasyon · $gecti yakalandı · $kaldi KAÇIRILDI"
exit "$kaldi"
