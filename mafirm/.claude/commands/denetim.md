---
description: Sistemdeki her sınamayı ve kapıyı çalıştırır; denetim betiğinin gerçek çıktısını yapıştırır ve başarısız her satırı açıklar.
---

`~/mafirm/denetim.sh` betiğini çalıştır ve GERÇEK çıktısını yapıştır. Özetleme.

Başarısız her satır için:
1. Hangi kontrol, hangi komut.
2. Neden başarısız: eksik dosya mı, başarısız sınama mı, bozulmuş bir kural mı.
3. Düzeltmesi ne ve düzeltme kimin kararı.

Denetim yeşil değilse "kurulum tamam" deme. Kurulumun işe yaradığının tek
kanıtı yeşil bir denetimdir.

Şununla bitir: kaç kontrol çalıştı, kaçı geçti, hangi dosyalar şu anda güvenilir
değil.
