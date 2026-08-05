# Google Play mağaza listesi metinleri

Play Console'daki "Ana mağaza listesi" (Main store listing) formuna
kopyala-yapıştır yapman için hazırlanan metinler. Hepsi Türkçe; ilerde
başka dillere çevirmek istersen aynı yapıyı kullanabilirsin.

## Uygulama adı (App name) — maks. 30 karakter

```
Hoopwave
```

(8 karakter — istersen `Hoopwave - Kaçış Oyunu` gibi bir alt başlık da
eklenebilir, 30 karakter sınırının altında kalır.)

## Kısa açıklama (Short description) — maks. 80 karakter

```
Çöl, deniz, gökyüzü: zıpla, yüz ya da uç! Reklamsız, çevrimdışı kaçış oyunu.
```

(76 karakter)

## Tam açıklama (Full description) — maks. 4000 karakter

```
Hoopwave, tek dokunuşla oynanan basit ve bağımlılık yapan bir kaçış oyunu. Kayalardan zıpla, köpekbalıklarından kaç ya da avcı kuşların arasından süzül — üç farklı dünyadan birini seç, kendi tarzında oyna.

ÜÇ FARKLI TEMA
🏜️ Çöl — Gün batımında kayalardan ve sivri kayalıklardan zıplayarak kaç.
🐟 Deniz — Mercan resifinin ortasında yüz, köpekbalıklarından ve deniz kestanelerinden sakın.
🐦 Gökyüzü — Bulut katmanları arasında kanat çırparak avcı kuşlardan ve kapanlardan kaç.

Her temanın kendi rengi, müziği, oyuncusu ve engelleri var.

NASIL OYNANIR
Ekrana dokun (ya da boşluk tuşuna bas) — o kadar. Çöl temasında zıplarsın, deniz ve gökyüzünde yukarı doğru yüzer/uçarsın.

ÖZELLİKLER
• Skorun arttıkça zorluk seviyesi de artar
• Her 25 puanda bir kazandığın "devam hakkı" ile kaldığın yerden sürmeye devam et
• Her tema için ayrı en yüksek skor takibi
• Temaya özel, sessize alınabilen arka plan müziği
• Tamamen çevrimdışı çalışır — internet gerekmez
• Reklam yok, hesap yok, veri toplama yok

Hoopwave tamamen cihazında çalışır; hiçbir kişisel veri toplamaz ya da göndermez.
```

(~1079 karakter)

## Kategori önerisi

**Oyun → Arcade** (ya da Casual)

## Gizlilik politikası URL'si

Kalıcı adres (GitHub Pages, `gh-pages` branch'inden):

```
https://ridvanete-source.github.io/Insta_man/privacy-policy.html
```

Bu dosyanın kaynağı `privacy-policy.html` (bu klasörde) ile birebir aynı;
`gh-pages` branch'ine zaten push edildi.

⚠️ **Tek eksik adım — Settings'te Pages'i açman gerekiyor** (API üzerinden
otomatik yapılamıyor, GitHub bunu bir admin panel tıklamasıyla istiyor):

1. Repo sayfasında **Settings → Pages**'e git.
2. **Build and deployment → Source**: "Deploy from a branch" seç.
3. **Branch**: `gh-pages` / `/ (root)` seç, **Save**'e bas.
4. Birkaç dakika içinde yukarıdaki URL canlıya çıkar (Settings → Pages
   sayfasında yeşil bir "your site is live at ..." mesajı görünce hazırdır).

Bundan sonra bu URL kalıcıdır — Play Console'a bunu gir.

## Görseller (hazır)

Hepsi bu klasörde, doğrudan Play Console'a yüklenebilir:

- **Uygulama ikonu**: [`icon-512.png`](./icon-512.png) (512×512)
- **Öne çıkan grafik**: [`feature-graphic.png`](./feature-graphic.png) (1024×500)
- **Telefon ekran görüntüleri**: [`screenshots/`](./screenshots) klasöründe
  4 tane (1082×2202, gerçek oynanıştan) —
  `01-tema-secimi.png` (tema seçim ekranı),
  `02-col.png` (çöl oynanışı),
  `03-deniz.png` (deniz oynanışı, köpekbalığı görünür),
  `04-gokyuzu.png` (gökyüzü oynanışı, kapan görünür).
  Play Console'a yükleme sırası önemli değil, ama `01` başta olursa
  mağaza sayfasında "önce ne göreceğim" hissi daha iyi olur.

## İçerik derecelendirmesi

Play Console'daki anket sihirbazında şu soruların cevabı **"hayır"**
olacak: şiddet, cinsel içerik, küfür, kumar, kullanıcı tarafından üretilen
içerik, kişisel veri toplama, reklam. Bu tür bir kaçış oyunu genelde
**"Herkes / PEGI 3"** derecesini alır.
