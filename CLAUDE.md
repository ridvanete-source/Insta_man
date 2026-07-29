# Insta_man

Instagram için otomatik paylaşım ve etkileşim odaklı hashtag seçimi yapan bir
araç seti. İçerikler (fotoğraf/video/reels ve metinler) henüz belirlenmedi;
bu proje **içerik olmadan çalışan bir altyapı**dır — içerikler netleştiğinde
`content_library/queue.yaml` dosyasına eklenir ve otomatik olarak paylaşılır.

## Proje amacı

1. Yeni açılacak bir Instagram hesabında paylaşımları otomatik zamanlamak.
2. Her paylaşım için, hesabın konusuna/etikete göre etkileşim alması
   beklenen hashtag'leri otomatik seçmek (geniş + orta + niş etiket
   karışımı, banlı etiketleri filtreleyerek, tekrarı azaltarak).
3. İçerik türü/sıklığı/teması henüz karara bağlanmadığı için, sistemin
   "içerik nedir" sorusundan bağımsız, esnek bir kuyruk üzerinden çalışması.

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
└── queue.example.yaml    # queue.yaml şeması - gerçek queue.yaml git'e girmez

tests/                    # hashtag seçimi ve queue mantığı için birim testler (ağ çağrısı yok)
```

### Neden adapter (publisher) yapısı?

Instagram'a paylaşım atmanın iki yolu var ve ikisinin de ciddi tradeoff'ları
var (aşağıya bakın). Hangisinin kullanılacağına henüz karar verilmediği için
`BasePublisher` arayüzü arkasında iki backend de hazır: `config.py` içindeki
`INSTA_MAN_PUBLISHER` değişkeni ("graph_api" veya "instagrapi") ile hangisinin
aktif olacağı seçilir; `scheduler/runner.py` ve `queue` katmanı hangi
backend'in kullanıldığını hiç bilmez. Backend değiştirmek `.env` içinde tek
satır değiştirmektir, kod değişikliği gerekmez.

## ⚠️ İki paylaşım yöntemi ve risk farkı

| | **Graph API (resmi)** | **instagrapi (resmi olmayan)** |
|---|---|---|
| Kullanım Şartları | Uyumlu | **İhlal ediyor** |
| Hesap banlanma riski | Yok (API kotaları dışında) | Var - geçici kısıtlama veya kalıcı ban, itiraz yolu genelde yok |
| Kurulum | Business/Creator hesap + Facebook Sayfası + Meta Developer App onayı gerekir, biraz uğraştırıcı | Kullanıcı adı/şifre ile direkt çalışır, kurulumu kolay |
| Story desteği | Kısıtlı/yok | Var (Story, Reels, DM dahil her şey) |
| Medya kaynağı | **Genel erişime açık HTTPS URL** gerekir (dosya yükleme değil, API URL'den çeker) | Yerel dosya yolu yeterli |
| Rate limit | Meta'nın resmi limitleri, öngörülebilir | Instagram'ın "bot tespiti" davranışına bağlı, öngörülemez |

**Öneri: Graph API ile başlayın.** Hesap gerçek bir hesap olacaksa (banlanırsa
kaybedilecek bir şey varsa) risk almaya değmez. instagrapi backend'i sadece
Story gibi Graph API'nin desteklemediği bir şey şart olursa, riski kabul
ederek devreye alınacak şekilde hazır tutuldu.

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

İçerik/niş belirlendiğinde yapılacak iş: `seed_hashtags.yaml`'a gerçek konu
başlıklarını ve o konuya uygun gerçek hashtag'leri eklemek (şu an sadece
`general`, `lifestyle`, `travel` örnek/placeholder olarak var).

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
  status: pending                       # pending | publishing | posted | failed | skipped
```

`queue.yaml` `.gitignore`'da - içindeki yayımlanmamış caption/medya linkleri
public repo'da görünmesin diye. İçerikler netleştiğinde bu dosyayı doldurun.

## Çalıştırma

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp content_library/queue.example.yaml content_library/queue.yaml

python -m insta_man.cli validate   # config + queue dosyasını kontrol eder
python -m insta_man.cli list       # kuyruktaki postları ve durumlarını listeler
python -m insta_man.cli run        # şu an zamanı gelmiş postları paylaşır
```

### Zamanlama (henüz karara bağlanmadı, iki seçenek hazır)

- **cron (kendi sunucu/bilgisayar):** `crontab -e` ile örn. her saat
  `cd /path/to/Insta_man && .venv/bin/python -m insta_man.cli run` çalıştırın.
- **GitHub Actions:** `.github/workflows/scheduled_post.yml.example`
  dosyasını `scheduled_post.yml` olarak yeniden adlandırın, repo secrets'a
  `IG_GRAPH_USER_ID`/`IG_GRAPH_ACCESS_TOKEN` ekleyin. Not: `queue.yaml`
  git-ignored olduğu için, Actions'ın gerçek kuyruğu görmesi için ayrı bir
  adımda (private repo commit'i veya harici depolama) çekilmesi gerekir.

## Testler

```bash
pytest
```

Testler ağ çağrısı yapmaz; sadece hashtag seçim mantığını (`test_hashtags.py`)
ve queue durum geçişlerini (`test_content_queue.py`) doğrular. Publisher
backend'leri (`graph_api.py`, `instagrapi_adapter.py`) gerçek kimlik bilgisi
gerektirdiği için testlerde mock'lanmadı - bu bir sonraki adım (Yol haritası).

## Yol haritası / henüz yapılmadı

- [ ] Hangi publisher backend'inin kullanılacağına karar verilmesi (Graph API önerilir).
- [ ] Hesap açılıp Business/Creator'a çevrilmesi, Meta App onayı.
- [ ] Gerçek içerik konusu/niş belirlenince `seed_hashtags.yaml`'ın doldurulması.
- [ ] `content_library/queue.yaml`'a gerçek postların eklenmesi.
- [ ] Zamanlama ortamının seçilmesi (cron vs GitHub Actions) ve devreye alınması.
- [ ] Graph API access token'ının otomatik yenilenmesi (şu an manuel).
- [ ] Publisher'lar için mock'lu entegrasyon testleri.
- [ ] Paylaşım sonrası basit bir performans/etkileşim log'u (hangi hashtag seti hangi postta kullanıldı - `recent_hashtags` bunun temelini atıyor, raporlama yok).

## Hesap adı önerileri

Niş/konu henüz belirlenmediği için isimler **nötr ve esnek** seçildi - ileride
hangi içerik türüne dönerse dönsün (yaşam tarzı, seyahat, kişisel, vb.)
sıkışmayacak şekilde. Instagram'da kullanılabilirliği uygulama içinden manuel
kontrol edin (otomatik/scraping ile kontrol ToS ihlali olur).

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
