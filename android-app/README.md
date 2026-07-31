# Zıpla Kaç — Android (Google Play) paketi

`../game` klasöründeki HTML5 oyununu, [Capacitor](https://capacitorjs.com/) ile
gerçek bir Android uygulamasına saran proje. Oyun tamamen çevrimdışı çalıştığı
için (sunucu yok, `localStorage` + Web Audio) barındırma/domain gerekmiyor —
web dosyaları doğrudan uygulamanın içine paketleniyor.

## Proje yapısı

```
android-app/
├── capacitor.config.json   # appId, appName, webDir (../game'i işaret eder)
├── assets/                 # kaynak ikon (1024x1024) ve splash (2732x2732)
├── android/                 # `npx cap add android` ile üretilen native proje
│   └── app/src/main/assets/public/   # her `cap sync`de ../game'den kopyalanır
└── package.json
```

**Tek doğruluk kaynağı `../game` klasörüdür.** Oyunu güncelledikten sonra
Android projesine yansıtmak için:

```bash
cd android-app
npx cap sync android
```

## Gereksinimler (bu ortamda YOK, kendi makinende/CI'da gerekiyor)

- [Android Studio](https://developer.android.com/studio) (önerilen — SDK,
  emülatör ve imzalama araçlarını otomatik kurar) **veya** komut satırı
  Android SDK + `ANDROID_HOME` ortam değişkeni
- JDK 17+ (bu repo JDK 21 ile test edildi)
- Node.js 18+

## Yerel geliştirme / test

```bash
cd android-app
npm install
npx cap sync android
npx cap open android      # Android Studio'yu bu projeyle açar
```

Android Studio içinden bir emülatör veya USB bağlı telefonla "Run" ile
doğrudan test edebilirsin.

## Play Store için imzalı sürüm (.aab) oluşturma

1. **İmzalama anahtarı oluştur** (yalnızca bir kez, sonsuza kadar sakla —
   kaybedersen uygulamayı bir daha güncelleyemezsin):
   ```bash
   keytool -genkey -v -keystore ziplakac-release.keystore \
     -alias ziplakac -keyalg RSA -keysize 2048 -validity 10000
   ```
   Bu dosyayı **asla** git'e commit'leme (`.gitignore`'da zaten hariç
   tutuldu). Şifreleyip güvenli bir yerde (parola yöneticisi, harici disk)
   yedekle.

2. `android-app/android/key.properties` dosyası oluştur (bu da git-ignored):
   ```properties
   storePassword=***
   keyPassword=***
   keyAlias=ziplakac
   storeFile=../../ziplakac-release.keystore
   ```

3. Android Studio'da **Build → Generate Signed Bundle / APK → Android App
   Bundle**'ı seçip yukarıdaki keystore ile imzalı bir `.aab` üret. (Komut
   satırından da yapılabilir: `./gradlew bundleRelease`, ama SDK/keystore
   ortam değişkenlerinin doğru kurulu olması gerekir.)

Çıktı: `android/app/release/app-release.aab` — Play Console'a yüklenecek
dosya budur (`.apk` değil, Play artık `.aab` istiyor).

## Google Play Console'a yükleme (senin tarafında yapman gerekenler)

1. [Google Play Console](https://play.google.com/console) hesabı aç (tek
   seferlik 25$ kayıt ücreti).
2. Yeni uygulama oluştur, paket adını gir: **`com.instaman.ziplakac`**
   ⚠️ Bu paket adı ilk yüklemeden sonra **değiştirilemez** — yayınlamadan
   önce `android-app/capacitor.config.json` ve
   `android/app/build.gradle` içindeki `applicationId`'i istediğin gibi
   değiştirebilirsin.
3. **Gizlilik politikası URL'si** ekle — Play, içerik olmasa bile zorunlu
   tutuyor. Hazır: [`store/privacy-policy.html`](./store/privacy-policy.html)
   (kaynak dosya) ve geçici canlı linki
   [`store/store-listing.md`](./store/store-listing.md) içinde — Play
   Console'a girmeden önce o linkin **herkese açık** olduğundan emin ol
   (bkz. `store-listing.md` içindeki uyarı), ya da sayfayı kendi kalıcı
   domain'ine taşı.
4. **Mağaza listesi**: [`store/store-listing.md`](./store/store-listing.md)
   içinde kopyala-yapıştıra hazır uygulama adı, kısa/uzun açıklama var.
   İkon (`assets/icon.png`, 512x512'ye küçültülmesi gerekir), en az 2 ekran
   görüntüsü (telefon) ve öne çıkan grafik (1024x500) hâlâ eksik — istersen
   onları da üretebilirim.
5. **İçerik derecelendirme anketi**'ni doldur (basit, şiddet/reklam
   içermeyen bir oyun için birkaç dakika sürer).
6. `.aab` dosyasını yükle, önce **Internal testing** kanalına at, kendi
   cihazında dene, sonra **Production**'a yayınla (Google'ın incelemesi
   genelde birkaç saat–birkaç gün sürer).

## Notlar

- `versionCode`/`versionName` her güncellemede `android/app/build.gradle`
  içinde artırılmalı (Play, aynı versionCode'u iki kez kabul etmez).
- Uygulama internet izni istemiyor (`INTERNET` izni manifest'ten
  kaldırıldı) — oyun tamamen cihaz üzerinde çalışıyor, bu da mağaza
  listesinde "izin istemiyor" olarak görünmesini sağlar.
- Web oyununda büyük bir değişiklik yaptığında bu klasörde tekrar
  `npx cap sync android` çalıştırmayı unutma, yoksa Android uygulaması eski
  sürümü göstermeye devam eder.
