# docs/design — mekanik v1 tasarım belgeleri (Faz 0)

Durum: inceleme bekliyor · yazan rol: proje-muhendisi · tarih: 2026-11-06

Okuma sırası:

1. [`architecture.md`](architecture.md): ana mimari belge. §1 bir sayfalık özet; §20.2 baş mühendisin açık kararları; §22 kalite mühendisi bulguları.
2. Araştırmalar:
   - [`research/a-agent-runtime.md`](research/a-agent-runtime.md): panelin ajanı arka planda çalıştırması (Claude Code headless ve Agent SDK; kimlik doğrulama, maliyet, şartlar).
   - [`research/b-cad.md`](research/b-cad.md): içe alınan STEP'te OCCT ile doğrudan modelleme; taramadan katıya.
   - [`research/c-mold-print.md`](research/c-mold-print.md): enjeksiyon kalıbında açık kaynakla otomatikleşebilenler; FDM dilimleyici CLI'leri; standartlar.
   - [`research/d-nasa-regulation-licenses.md`](research/d-nasa-regulation-licenses.md): NASA-STD-7009B, AB ve TR mevzuatı, JCGM, bağımlılık lisansları.
3. Envanterler:
   - [`appendix-a-dependency-inventory.md`](appendix-a-dependency-inventory.md): eski sistemde kişiye, makineye, işletim sistemine, kuruma ve alana bağlı her yer (dosya:satır).
   - [`appendix-b-migration-inventory.md`](appendix-b-migration-inventory.md): eski repodaki her öğe için taşınır / yeniden yazılır / taşınmaz; dersler E-01…E-41, öneriler Ö-01…Ö-28, inceleme B1–B8.
4. [`schemas/`](schemas/README.md): v1 JSON şemaları (20), örnekler ve doğrulama aracı.
5. [`wireframes/`](wireframes/index.html): panelin altı ana ekranının tel kafes taslakları (tarayıcıda açılır).

Belgeler eski sisteme atıf için kişi ve kurum adları içerir. Yayından önce bunlar temizlenir (architecture.md §17, ölçüt 4.5).
