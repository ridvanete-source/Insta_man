# Insta_man

Instagram için otomatik paylaşım ve etkileşim odaklı hashtag seçimi yapan bir
araç seti. Sistem canlıda: gerçek bir hesapta (`instagrapi` backend,
`.env` içinde gerçek kimlik bilgileri) saatlik GitHub Actions cron'u ile
çalışıyor, `content_library/queue.yaml` içinde gerçek içerikler var ve
bunlar otomatik paylaşılıyor. Kuyruk hâlâ esnek/genel amaçlı tutuluyor;
yeni içerik geldikçe `content_library/queue.yaml`'a eklenmesi yeterli.

## Proje amacı

1. Instagram hesabında paylaşımları otomatik zamanlamak (feed + Story).
2. Her paylaşım için, konu etiketine göre etkileşim alması beklenen
   hashtag'leri otomatik seçmek (geniş + orta + niş etiket karışımı,
   banlı etiketleri filtreleyerek, tekrarı azaltarak).
3. İçerik teması sabit tek bir niş değil (şehir/sokak, doğa, seyahat, spor
   anları gibi karışık konular olabiliyor), bu yüzden sistem "içerik nedir"
   sorusundan bağımsız, esnek bir kuyruk üzerinden çalışıyor -
   `seed_hashtags.yaml` içindeki 16 konu havuzundan hangisi uygunsa
   `ContentPost.topics` alanına o yazılıyor.

## Mimari

```
src/insta_man/
├── models.py           # ContentPost, MediaItem, PublishResult (paylaşılan veri tipleri)
├── config.py           # .env'den ayarları okur (Config dataclass)
├── hashtags/
│   ├── manager.py       # HashtagManager: konuya göre katmanlı (mega/medium/niche) seçim
│   ├── seed_hashtags.yaml   # konu -> katman -> hashtag listesi (içerik belli olunca güncellenir)
│   └── banned_hashtags.yaml # bilinen banlı/gölgelenmiş etiketler
├── publishers/
│   ├── base.py           # BasePublisher arayüzü (authenticate + publish)
│   ├── graph_api.py       # Resmi Instagram Graph API backend'i
│   ├── instagrapi_adapter.py  # Resmi olmayan instagrapi backend'i
│   └── __init__.py        # get_publisher(config) factory - config'e göre backend seçer
├── queue/
│   └── content_queue.py   # queue.yaml'ı okur/yazar, "şu an paylaşılacak" postları bulur
├── scheduler/
│   └── runner.py          # run_once(): due post'ları bulur, hashtag ekler, publisher'a yollar
└── cli.py                # `insta_man run|list|validate` komutları

content_library/
├── README.md
├── media/                 # gerçek medya dosyaları (instagrapi yerel dosya yolu bekler)
├── queue.example.yaml     # queue.yaml şeması
└── queue.yaml             # gerçek kuyruk - git'e commit'lenir, gerçek postları içerir

scripts/
├── generate_score_graphic.py  # maç skoru gibi anlık Story görselleri üretir
└── run_and_sync.ps1           # yerel makinede: pull -> `insta_man run` -> queue.yaml'daki
                                 # durum değişikliğini commit+push eder (Windows Task
                                 # Scheduler ile tetiklenmesi düşünülerek yazıldı; GitHub
                                 # Actions'a alternatif/yedek olarak çalışır)

.github/workflows/
└── auto-post.yml          # CANLI: her saat başı `insta_man run` çalıştırır (instagrapi,
                             # IG_USERNAME/IG_PASSWORD/IG_SESSION_B64 secrets), queue.yaml
                             # değişikliğini otomatik commit+push eder

tests/                    # hashtag seçimi ve queue mantığı için birim testler (ağ çağrısı yok)
```

### Neden adapter (publisher) yapısı?

Instagram'a paylaşım atmanın iki yolu var ve ikisinin de ciddi tradeoff'ları
var (aşağıya bakın). `instagrapi` kullanılıyor olarak karara bağlansa da,
`BasePublisher` arayüzü arkasında iki backend de kodda duruyor: `config.py`
içindeki `INSTA_MAN_PUBLISHER` değişkeni ("graph_api" veya "instagrapi") ile
hangisinin aktif olacağı seçilir; `scheduler/runner.py` ve `queue` katmanı
hangi backend'in kullanıldığını hiç bilmez. Backend değiştirmek `.env`
içinde tek satır değiştirmektir, kod değişikliği gerekmez.

## ⚠️ İki paylaşım yöntemi ve risk farkı

| | **Graph API (resmi)** | **instagrapi (resmi olmayan)** |
|---|---|---|
| Kullanım Şartları | Uyumlu | **İhlal ediyor** |
| Hesap banlanma riski | Yok (API kotaları dışında) | Var - geçici kısıtlama veya kalıcı ban, itiraz yolu genelde yok |
| Kurulum | Business/Creator hesap + Facebook Sayfası + Meta Developer App onayı gerekir, biraz uğraştırıcı | Kullanıcı adı/şifre ile direkt çalışır, kurulumu kolay |
| Story desteği | Kısıtlı/yok | Var (Story, Reels, DM dahil her şey) |
| Medya kaynağı | **Genel erişime açık HTTPS URL** gerekir (dosya yükleme değil, API URL'den çeker) | Yerel dosya yolu yeterli |
| Rate limit | Meta'nın resmi limitleri, öngörülebilir | Instagram'ın "bot tespiti" davranışına bağlı, öngörülemez |

**Karar verildi: şu an `instagrapi` kullanılıyor.** `.env` ve GitHub Actions
secrets'ları gerçek IG_USERNAME/IG_PASSWORD ile `INSTA_MAN_PUBLISHER=instagrapi`
olarak ayarlı; Story desteği bu kararda belirleyici oldu (Graph API Story'yi
desteklemiyor). Risk kabul edildi - hesap kısıtlama/ban ihtimali bilinerek
devam ediliyor. `graph_api.py` backend'i hâlâ kodda duruyor ve gerekirse
`.env`'de tek satır değiştirerek geri dönülebilir, ama aktif olarak
kullanılmıyor.

### Graph API kurulum kontrol listesi
1. Instagram hesabını **Professional (Business veya Creator)** hesaba çevir.
2. Bir Facebook Sayfası oluştur ve Instagram hesabına bağla.
3. [Meta for Developers](https://developers.facebook.com/) üzerinde bir App
   oluştur, Instagram Graph API + `instagram_content_publish` iznini ekle.
4. Sayfa erişim token'ı (uzun ömürlü) al, `IG_GRAPH_ACCESS_TOKEN` ve
   `IG_GRAPH_USER_ID` olarak `.env`'e yaz.
5. Paylaşılacak medyayı genel erişime açık bir HTTPS adresine koy (S3,
   Cloudinary, hatta bir GitHub repo'sunun raw linki olabilir) - Graph API
   dosya upload'ı değil, URL kabul eder.
6. Token ~60 günde bir yenilenmesi gerekir - bunu takvime not edin
   (otomatik yenileme bu projenin kapsamında değil, roadmap'te).

### instagrapi kurulum (risk kabul edilirse)
1. `pip install instagrapi` (varsayılan `requirements.txt`'de değil, opsiyonel).
2. `.env`'de `INSTA_MAN_PUBLISHER=instagrapi`, `IG_USERNAME`, `IG_PASSWORD`.
3. İlk girişte oturum `.ig_session.json`'a kaydedilir (git-ignored) -
   böylece her çalıştırmada yeniden login olup şüpheli aktivite
   tetiklenmez.
4. Yeni açılan bir hesapta hemen yoğun otomasyona başlamayın; hesabı birkaç
   gün "ısındırıp" (manuel kullanım) sonra otomasyona geçmek ban riskini
   azaltır - bu bir garanti değil, sadece pratikte gözlemlenen bir eğilim.

## Hashtag motoru

`insta_man/hashtags/manager.py` içindeki `HashtagManager.select()`:

- Her post'un `topics` alanına göre `seed_hashtags.yaml` içinden ilgili
  konu havuzlarını bulur.
- Her konu havuzu üç katmana ayrılır: `mega` (>1M gönderi, çok rekabetçi),
  `medium` (~50k-1M, en iyi erişim/rekabet oranı), `niche` (<50k, hedefli
  ama yavaş). Varsayılan karışım: %15 mega / %55 medium / %30 niche.
- `banned_hashtags.yaml`'daki etiketler otomatik elenir (bu liste zamanla
  değişir, periyodik olarak elle kontrol edilmeli).
- `exclude_recent` ile son paylaşımlarda kullanılan etiketler tekrar
  seçilmez (aynı 30 etiketi her postta kullanmak "spam" davranışı olarak
  algılanıp erişimi düşürebiliyor).
- `extra_hashtags` (örn. hesabın marka etiketi) her zaman dahil edilir.

`seed_hashtags.yaml` 16 konu havuzu ile dolu (general, lifestyle, travel,
food, fitness, fashion, business, photography, art, tech, motivation,
beauty, petcare, homedecor, music, city, nature). Yeni bir konu/niş
paylaşımı geldiğinde ya mevcut havuzlardan biri `topics`'e yazılır ya da
buraya yeni bir kategori eklenir - `general` her zaman fallback olarak
kalır.

## İçerik kuyruğu (`content_library/queue.yaml`)

Şema referansı: `content_library/queue.example.yaml`. Her satır bir post:

```yaml
- id: "2026-08-01-launch-post"
  caption: "..."
  media:
    - path: "https://.../image.jpg"   # graph_api: genel URL, instagrapi: yerel dosya yolu
      type: image                      # image | video | reel | carousel item
  scheduled_at: "2026-08-01T09:00:00+03:00"
  topics: ["general"]
  extra_hashtags: ["mybrand"]
  max_hashtags: 25
  target: feed                          # feed | story
  status: pending                       # pending | publishing | posted | failed | skipped
  published_at: null                    # scheduler tarafından publish sonrası doldurulur
  platform_post_id: null
  error: null
```

`queue.yaml` **git-ignored değil** - gerçek postlar (caption, medya yolu,
durumu) doğrudan repoya commit'leniyor; hem GitHub Actions hem
`scripts/run_and_sync.ps1` her çalıştırmadan sonra durum değişikliğini
otomatik push ediyor. Medya dosyaları `content_library/media/` altında
tutuluyor (instagrapi yerel dosya yolu bekliyor, genel erişime açık URL
değil).

## Çalıştırma

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .                # insta_man'i editable kurar, PYTHONPATH gerekmez
cp .env.example .env
cp content_library/queue.example.yaml content_library/queue.yaml

python -m insta_man.cli validate   # config + queue dosyasını kontrol eder
python -m insta_man.cli list       # kuyruktaki postları ve durumlarını listeler
python -m insta_man.cli run        # şu an zamanı gelmiş postları paylaşır
```

### Zamanlama (karar verildi: GitHub Actions, canlı)

- **GitHub Actions (aktif):** `.github/workflows/auto-post.yml` her saat
  başı (`cron: "0 * * * *"`) çalışır; `IG_USERNAME`, `IG_PASSWORD`,
  `IG_SESSION_B64` repo secrets'larından `.env` ve `.ig_session.json`
  üretir, `insta_man.cli run` çalıştırır, `content_library/queue.yaml`
  içindeki durum değişikliğini otomatik commit+push eder
  (`[skip ci]` ile kendi kendini tetiklemez). `queue.yaml` git-ignored
  *değil* artık - gerçek postlar doğrudan repoya commit'leniyor.
- **Yerel yedek (`scripts/run_and_sync.ps1`):** Aynı akışı yerel makinede
  çalıştırır (pull --rebase --autostash -> `insta_man.cli run` -> queue.yaml
  değiştiyse commit+push). Windows Task Scheduler ile tetiklenmek üzere
  yazıldı; GitHub Actions'ın devre dışı kaldığı durumlarda veya yerelde test
  ederken kullanılır.
- Eski `.github/workflows/scheduled_post.yml.example` dosyası artık
  kullanılmıyor (Graph API'ye özgüydü) - referans amaçlı repoda duruyor.

## Testler

```bash
pytest
```

Testler ağ çağrısı yapmaz; hashtag seçim mantığını (`test_hashtags.py`),
queue durum geçişlerini (`test_content_queue.py`) ve instagrapi'nin
login/2FA/challenge akışını (`test_instagrapi_adapter.py`, sahte bir
`instagrapi.Client` ile) doğrular. Asıl `publish()`/medya upload çağrıları
(`instagrapi_adapter.py` ve `graph_api.py` içindeki upload kısımları) henüz
mock'lanmadı - bkz. Yol haritası.

## Yol haritası / henüz yapılmadı

- [x] Hangi publisher backend'inin kullanılacağına karar verilmesi -> `instagrapi` seçildi (Story desteği belirleyici oldu).
- [x] Gerçek içerik konusu/niş belirlenince `seed_hashtags.yaml`'ın doldurulması -> 16 konu havuzu eklendi.
- [x] `content_library/queue.yaml`'a gerçek postların eklenmesi -> devam eden bir süreç, yeni içerik geldikçe ekleniyor.
- [x] Zamanlama ortamının seçilmesi ve devreye alınması -> GitHub Actions (`auto-post.yml`, saatlik) + yerel yedek (`run_and_sync.ps1`).
- [ ] Graph API kullanılmıyor olsa da kod tabanında duruyor; ileride geri dönülürse access token otomatik yenileme hâlâ eksik.
- [ ] Publisher'ların `publish()`/medya upload çağrıları için mock'lu testler (login/2FA akışı zaten test edildi).
- [ ] Paylaşım sonrası basit bir performans/etkileşim log'u (hangi hashtag seti hangi postta kullanıldı - `recent_hashtags` bunun temelini atıyor, raporlama yok).
- [ ] Hesap yeni açıldığı için Instagram'ın bot tespiti / geçici kısıtlama riskine karşı paylaşım sıklığı ve saatleri gözden geçirilmeli (özellikle saatlik cron ile).

## Hesap adı önerileri (karar verildi, tarihsel referans)

Otomasyon mevcut/kişisel bir hesap üzerinden (`.env`'deki `IG_USERNAME`)
devreye alındı - aşağıdaki öneriler yeni bir marka hesabı açılması
ihtimaline karşı daha önce hazırlanmıştı ve şu an kullanılan hesap bu
listedeki isimlerden biri değil. Liste, ileride ayrı/nötr bir hesaba
geçilmek istenirse referans olarak tutuluyor.

**Sade / nötr (İngilizce):**
- `dailydrop.co`
- `the.daily.frame`
- `everyday.edit`
- `quiet.feed`
- `loop.journal`
- `frame.archive`

**Türkçe, sade:**
- `gunluk.kare`
- `sade.an`
- `bir.bakis`
- `kisa.mola`

**Marka tarzı, tek kelime + ek:**
- `driftlane`
- `paperlane`
- `nudge.daily`

**Seçerken dikkat edilecekler:**
- Hesap adını içerik temasına göre daha sonra tamamen değiştirmek
  mümkün (Instagram username değiştirilebilir), o yüzden şimdiden çok
  spesifik bir isme kilitlenmeyin.
- Kullanıcı adında nokta/alt çizgi sayısını azda tutun - hatırlanması ve
  yazılması kolay olsun.
- Aynı adı gelecekte e-posta/domain olarak da kullanmayı düşünüyorsanız
  (örn. `driftlane.com`), şimdiden domain uygunluğunu da kontrol edin.
