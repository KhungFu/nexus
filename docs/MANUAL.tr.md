# NEXUS CEO – Kullanım Kılavuzu (v15.24)

NEXUS CEO, Capital.com API'si üzerinden emtia ve kripto CFD pozisyonlarını kendi başına açan, koruyan ve kademeli olarak yeniden satan bir Telegram botudur. Bu kılavuz v15.24 sürümünü kodda olduğu hâliyle anlatır. Tekniği anlatır, yatırım tavsiyesi değildir. CFD işlemleri yatırdığın paranın kaybıyla sonuçlanabilir; önce bir demo hesap kullan.

Diğer diller: [Deutsch](MANUAL.de.md) · [English](MANUAL.en.md)

## 1. İlk kurulum

Sürekli çalışan bir bilgisayara (örneğin bir Raspberry Pi), Python 3.10 veya daha yenisine (3.11 ile test edildi), bir Capital.com hesabına ve kendi Telegram botuna ihtiyacın var.

1. Dosyaları bir klasöre koy, örneğin `~/nexus/`: `nexus_ceo.py`, `nexus_lang.py`, `nexus_diagnose.py`, `requirements.txt`, `.env.example`. İsteğe bağlı olarak: piyasalarının listesini içeren `capital_markets_config.py`. Bu dosya yoksa bot, dokuz piyasalık yerleşik listeyle işlem yapar (EUR/USD, altın, gümüş, Crude, Brent, BTC, ETH, XRP, SOL).
2. Python paketlerini kur: `pip install -r requirements.txt`
3. Telegram botunu oluştur: Telegram'da `@BotFather` ile yazış, `/newbot` gönder, token'ı sakla.
4. Capital.com: hesabının ayarlarından bir API anahtarı oluştur. Bu sırada anahtar için ayrı bir parola belirlersin. `.env` dosyasına anahtarı (`CAPITAL_API_KEY`), giriş e-postanı (`CAPITAL_IDENTIFIER`) ve parolayı (`CAPITAL_PASSWORD`) yaz. Capital.com'un burada hangi parolayı beklediği (anahtarın parolası mı, hesabın parolası mı) Capital.com'un API kılavuzunda yazar; bot girişi reddederse diğerini dene. Başlangıçta demo hesabı kullan.
5. Capital.com hesabında Hedging modunu kapat. Yoksa bot kısmi satış yapamaz.
6. En az bir Gemini anahtarı (Google AI Studio) ve tercihen yedek olarak bir Groq anahtarı al.
7. `.env.example` dosyasını `.env` olarak kopyala ve erişim bilgilerini gir: `cp .env.example .env`, ardından `chmod 600 .env`.
8. Botu başlat: `python3 nexus_ceo.py`
9. Telegram'da bota herhangi bir şey yaz. `MY_CHAT_ID` boş olduğu sürece yalnızca Chat ID'ni yanıt olarak gönderir. Bu sayıyı `.env` dosyasına `MY_CHAT_ID` olarak yaz ve botu yeniden başlat.
10. Sonraki başlatmada bot dili sorar. Dile dokun, onayla. Bot `BOT_LANGUAGE` değerini `.env` dosyasına kendisi yazar.

Sürekli çalıştırmak için botu systemd servisi olarak kur; bir şablon `systemd/nexus_ceo.service.example` içinde duruyor.

`.env` tüm erişim bilgilerini içerir. Onu asla kimseye verme ve hiçbir yere yükleme. Paketteki `.gitignore` dosyası, Git'in onu yok saymasını sağlar.

## 2. Dil

Bot Almanca, İngilizce ve Türkçe konuşur. Metinler `nexus_lang.py` içindedir; bot her mesajı ancak gönderirken çevirir.

- **İlk başlatma:** `.env` içinde `BOT_LANGUAGE` yoksa bot üç düğme gönderir: Deutsch, English, Türkçe. Dokunduktan sonra onay ister; seçimi ancak onay kaydeder.
- **Sonradan değiştirme:** `/dil` gönder. Ya da `.env` içine `BOT_LANGUAGE=de`, `en` veya `tr` yaz ve yeniden başlat.
- **Komutlar:** Her komutun her dilde bir adı vardır. Hangi dil ayarlı olursa olsun bütün adlar her zaman çalışır. Türkçe adlar özgün adlardır.
- **Yapay zekâ metinleri:** Yapay zekâya seçilen dilde yazma görevi verilir. TRADE satırları sabit biçimlerinde kalır.
- **Eksik çeviri:** Kuralı olmayan metinleri bot özgün hâliyle gönderir ve `nexus_lang_missing.log` dosyasına yazar. Çeviriyi `nexus_lang.py` içinde `RULES` altına eklersin; `python3 nexus_lang.py` dosyayı denetler.
- `BOT_LANGUAGE=orig` çeviriyi kapatır.

## 3. Başlatma, durdurma, denetleme

systemd servisi `nexus_ceo.service` olarak:

| Görev | Komut |
| --- | --- |
| Yeniden başlat (`.env` veya kodda yapılan her değişiklikten sonra) | `sudo systemctl restart nexus_ceo.service` |
| Durdur | `sudo systemctl stop nexus_ceo.service` |
| Başlat | `sudo systemctl start nexus_ceo.service` |
| Çalışıyor mu? | `sudo systemctl status nexus_ceo.service --no-pager \| head -10` |
| Servisin son satırları | `journalctl -u nexus_ceo.service -n 50 --no-pager` |
| Log'u canlı izle | `tail -f nexus_ceo.log` |
| Başlatmadan önce kodu denetle | `python3 -m py_compile nexus_ceo.py` |

Her başlatmadan sonra bot bir başlangıç mesajı gönderir. İçinde sürüm, tarama aralığı, stop kuralı ve yeniden giriş kilidi yazar. Bir değer `.env` ile uyuşmuyorsa dosya okunmamış ya da servis yeniden başlatılmamıştır.

`.env` içindeki değişiklikler ancak yeniden başlatmadan sonra geçerli olur. Durdurulmuş bot stop'ları taşımaz ve kademe satmaz; ancak Capital.com'da kayıtlı Stop Loss ve Take Profit fiyatları geçerli kalır.

## 4. Telegram komutları

Bot komutları, metni ve düğmeleri yalnızca `MY_CHAT_ID` sohbetinden kabul eder. Başka sohbetlerden gelen mesajları yok sayar.

### Durum ve analiz

| Komut | Düğme | Ne olur |
| --- | --- | --- |
| `/pozisyon` | 📍 Pozisyon | Pozisyon raporu: her pozisyon için büyüklük, giriş, fiyat, Stop Loss, Take Profit, günlük aralık, günlük hedef, günlük aralık cinsinden stop mesafesi ve durumlarıyla Mirror-TP kademeleri |
| `/status` | 📊 Status | Kurul oylamasıyla tam yapay zekâ analizi. Bir Gemini isteği harcar |
| `/sinyaller` | 📈 Sinyaller | Teknik sinyaller (MA 9/26, ADX, RSI) |
| `/stats` | 🧮 Stats | Bot veritabanından işlem istatistiği ve varlık başına sonuç |
| `/kayip` | 💸 Kayip | Sembol başına bugünün kayıp sayacı |
| `/bloklar` | 🔒 Bloklar | Etkin HARD BLOCK'lar (işlem engelleri) |
| `/volatilite` | – | Kara Kuğu denetimini şimdi çalıştır |
| `/update_models` | – | Yapay zekâ modellerini kontrol et: Gemini zinciri ve reddedilen anahtarlar, ayrıca Groq, Qwen ve Nvidia için model, zincir ve engeller. `/update_models best`, kontrolü geçen en büyük modele geçer |
| `/teshis` | 🔎 Teşhis | Son 7 günün teşhisi: özet mesaj olarak, tam rapor metin dosyası olarak. `/teshis 3` = yalnızca 3 gün. Yalnızca okur |
| `/kilavuz` | – | Tam kılavuz, kendi dilinde dosya olarak; sonunda botun şu anda çalıştığı ayarlar. `/kilavuz tr` = Türkçe, `de` = Almanca, `en` = İngilizce. Dosya botun yanında yoksa GitHub'dan indirir |
| `/dil` | – | Dil seç |
| `/yardim` | 📋 Menü | Komut özeti |

### Pozisyonları yönetme

| Komut | Ne olur |
| --- | --- |
| `/kapat GOLD` | Bu sembolün tüm pozisyonlarını hemen kapatır |
| `/kapat HEPSI` | Onay ister; tüm pozisyonları gerçekten kapatan ancak `/kapat HEPSI ONAYLA` komutudur |
| `/manuel GOLD BUY 100` | Gate-Keeper ve Kurul olmadan hemen 100 EUR'luk bir pozisyon açar. Stop ve hedefi bot kendisi belirler |
| `/manuel GOLD BUY 100 1900 2100` | Aynısı, kendi Stop Loss (1900) ve Take Profit (2100) değerlerinle |
| `/sl_genislet` | Açık pozisyonların hangi stop'larının günlük gürültü içinde kaldığını gösterir. Hiçbir şeyi değiştirmez |
| `/sl_genislet evet` | Bu stop'ları asgari mesafeye çeker. Yalnızca uzaklaştırır, asla yaklaştırmaz; Take Profit aynı kalır |

### Araştırma ve bakım

| Komut | Ne olur |
| --- | --- |
| `/backtest GOLD 200` | Bir sembol için 200 günlük backtest |
| `/deepdive GOLD HOUR_4 30` | Sembol, zaman dilimi ve gün sayısı için ayrıntılı analiz |
| `/haberler OIL 7` | Bir sembolle ilgili son 7 günde toplanan haberler (düğme 📰 Haberler) |
| `/haber_topla` | Haberleri şimdi topla |
| `/kaynaklar` | Haber kaynaklarının güvenilirlik puanları |
| `/spread` | Tüm piyasaların spread'lerini ölç ve piyasa yapılandırmasına yaz |
| `/dbtemizle` | Eski veya bozuk haberleri veritabanından sil |
| `/unut` | Kayıtlı notlarını sil |

### Komutsuz metin

Eğik çizgi olmadan yazdığın her şeyi bot, yapay zekâ analizi için not olarak kaydeder. Botun yardım metni 48 saat geçerlilik belirtir. Yapay zekâ notu da okur; not bir ipucudur, botun uymak zorunda olduğu bir talimat değildir.

**Metinle HARD BLOCK (işlem engeli) şu anda çalışmıyor.** Kod, `Gold nicht handeln` gibi bir cümlenin sembolü hemen kilitlemesini öngörür. Ancak bir hata yüzünden bot cümledeki sembolü hiç tanımaz (bkz. bölüm 15). Buna güvenme. Botun bir sembolde işlem yapmasını istemiyorsan `TRADING_ASSETS` içine yalnızca işlem yapabileceği sembolleri yaz ve yeniden başlat. Hiç işlem yapmasını istemiyorsan servisi durdur.

## 5. Bot nasıl işlem yapar

Bot taramalar hâlinde işlem yapar. İki tarama arasında `SCAN_INTERVAL_SEC` saniye vardır (varsayılan 21600, yani 6 saat). Bir tarama şöyle ilerler:

1. **Karşılaştırma.** Bot durum kayıtlarını Capital.com'daki açık pozisyonlarla karşılaştırır ve günlük kayıp durdurmasını denetler.
2. **Gate-Keeper.** Python her sembol için beş teknik puan hesaplar: MA 9/26 kesişimi, 15'in üzerinde ADX, yöne uygun RSI, Bollinger konumu, bir Fibonacci seviyesine yakınlık. Emtialar altıncı bir puan alabilir (Rogers filtresi, EMA 50/200). Yalnızca en az 5 puanı olan sembol devam eder. Böylece kripto 5 üzerinden 5 puana ihtiyaç duyar.
3. **Kurul.** Beş sabit kural seti (Cihat, Rogers, Dalio, Taleb, Soros) EVET ya da HAYIR oyu verir. 5 oydan 4'ü gerekir, kriptoda 5 oydan 3'ü.
4. **Yapay zekâ analizi.** Gemini adayları haberler, hava durumu ve makro verileriyle birlikte alır ve TRADE satırlarıyla yanıt verir. Gemini yanıt vermezse bir yedek sağlayıcı yalnızca Gate-Keeper'ın onayladığı adayları biçimlendirir.
5. **Emir öncesi denetimler.** Her TRADE satırı bölüm 8'deki kilitlerden geçer. Yedek modda yalnızca Gate-Keeper'ın bu taramada onayladığı sembol ve yön geçebilir.
6. **Emir.** Bot büyüklüğü kendisi hesaplar, stop'u asgari mesafeye çeker, emri gönderir ve 8 saniye sonra pozisyonun gerçekten hesapta olup olmadığını denetler.

Emtia sinyalleri günlük mumlardan gelir. Gün içinde pek değişmezler; bu yüzden her tarama çoğunlukla aynı adayları verir.

### Zaten açık bir pozisyon varsa ne olur

- **Aynı yön:** Bot yalnızca pozisyon en az %2 kârdaysa ekleme yapar (Pyramiding). Aksi hâlde protokolde “… Pyramiding atlandı: …” yazar.
- **Karşı yön:** Taramada yönü açık pozisyonla çelişen bir TRADE satırı gelirse (pozisyon BUY, satır SELL ya da tersi), bot bu sembolün tüm pozisyonlarını kapatır. Karşı pozisyon açmaz.

Şöyle ilerler:

1. Satır bölüm 8'deki kilitlerden geçmelidir: günlük kayıp durdurması, `MAX_POSITIONEN` değerinden az açık pozisyon, piyasa açık, spread, kayıp kilidi.
2. Bot sembolün tüm pozisyonlarını kapatır. Kapatılan ve ekside olan her pozisyon, kayıp kilidi için kayıp sayılır.
3. Protokolde “↩️ …: karşı sinyal …->… - yalnızca kapatıldı, karşı pozisyon yok” yazar. Kapatma başarısız olursa nedeni orada yazar.

Karşı sinyal sürerse, sonraki tarama yeni yönü tüm denetimlerle normal bir pozisyon olarak açar. v15.20'ye kadar bot bu denetimler olmadan hemen karşı emir gönderiyordu.

Karşı sinyale yalnızca tarama tepki verir. Çıkış izleyicisi kendi kurallarına göre kapatır.

### Bunların yanında sürekli çalışanlar

| Sıklık | Görev |
| --- | --- |
| 5 dakikada bir | Koruma turu: Kara Kuğu, Breakeven, Mirror-TP, stop merdiveni, Trailing-Stop, kapanan pozisyonların bildirimi |
| 15 dakikada bir | Günlük hedef bekçisi: Evet/Hayır düğmeleriyle, günlük hedefe ulaşan bir pozisyonun satılıp satılmayacağını sorar |
| 30 dakikada bir | Çıkış izleyicisi: `AUTO_EXIT=true` ise 5 çıkış kuralından 3'ü onaylayınca pozisyonu kapatır |
| 60 dakikada bir | Haber toplama (RSS, X) |
| 6 saatte bir | Gemini model listesini güncelleme |

Bu turlar yapay zekâ kotası harcamaz.

## 6. Pozisyon büyüklüğü

Otomatik işlemlerde büyüklüğü yalnızca `.env` belirler; yapay zekânın SIZE'ın arkasına yazdığı sayı kullanılmaz.

1. Temel = hesap × `POSITION_SIZE_PCT`, en az `MIN_POSITION_EUR`.
2. Üst sınır = şu üç değerin en küçüğü: `MAX_POSITION_EUR` (ayarlıysa), Risk-Parity sınırı (hesabın üçte ikisi) ve hesabın %50'si.
3. BTC, ETH, SOL ve XRP'de tutar yarıya indirilir.
4. Tutar, canlı fiyat ve EUR/USD fiyatıyla birime çevrilir.
5. Sonuç borsanın asgari büyüklüğünün altındaysa bot asgari büyüklüğü alır. Asgari büyüklük bile üst sınırdan pahalıysa işlem yapılmaz.

Bot hesabı veya fiyatı okuyamazsa otomatik işlemlerde hiçbir şey açmaz.

Manuel işlemde senin EUR tutarın geçerlidir. Tutar `MIN_POSITION_EUR` değerine yükseltilir ve hesabın %50'sinde kesilir; `MAX_POSITION_EUR` burada uygulanmaz. 3. adımdaki yarıya indirme manuel işlemde de geçerlidir.

## 7. Stop Loss ve kâr alma

Her pozisyon açılırken Capital.com'da bir Stop Loss ve bir Take Profit alır. Sonrasında koruma turu bunları 5 dakikada bir yönetir.

### Girişte Stop Loss

Yapay zekâ bir stop önerir; fiyata çok yakınsa bot onu asgari mesafeye çeker.

- **Asgari mesafe** = günlük aralık (14 gün üzerinden günlük ATR) × `SL_ATR_MULT` (varsayılan 1.0).
- **Alt sınır:** asla %1,5'ten yakın olmaz (kriptoda hafta sonu %3,75). Bu değer, günlük aralık alınamadığında da geçerlidir.
- **Üst sınır:** en fazla `SL_MAX_PCT` (varsayılan %6); böylece stop Kara Kuğu eşiğinden önce devreye girer.
- Yapay zekânın stop'u asgari mesafeden uzaktaysa olduğu gibi kalır. %8'den fazla uzaktaysa değiştirilir.

Kural otomatik işlemler için geçerlidir. Manuel işlem, ayrı bir değer vermediysen stop'u 2 × saatlik ATR'ye, hedefi de bu mesafenin üç katına koyar.

### Girişte Take Profit

Take Profit yapay zekâdan gelir. Yoksa ya da fiyata %0,3'ten yakınsa bot günlük aralığın %90'ını koyar.

### Girişten sonra ne olur

| Tetikleyici | Bot ne yapar |
| --- | --- |
| Fiyat giriş ± 0,5 × saatlik ATR'ye ulaşır | Mirror-TP kademe 1: başlangıçtaki büyüklüğün %25'ini satar |
| Fiyat ± 1,0 × saatlik ATR'ye ulaşır | Mirror-TP kademe 2: bir %25 daha |
| Fiyat ± 1,5 × saatlik ATR'ye ulaşır | Mirror-TP kademe 3: bir %25 daha |
| Bir kademe satıldı | Stop merdiveni: kademe 1'den sonra stop girişe (artı %0,03), kademe 2'den sonra kademe 1'in satış fiyatına, kademe 3'ten sonra kademe 2'ninkine çekilir. Stop yalnızca daraltılır, asla genişletilmez. Anahtar `STOP_LEITER` |
| Kâr %1,0 ve üzeri | Breakeven: stop giriş fiyatına (artı %0,03) |
| Kâr %1,5 ve üzeri | Trailing-Stop: en iyi fiyatın %5 gerisinde, yalnızca daraltılır |
| Aynı sembolde birden çok pozisyon varken kâr %2 ve üzeri | En küçük pozisyonu kapatır |
| Kâr günlük aralığın %90'ına ulaşır | Günlük hedef: bot Evet/Hayır düğmeleriyle satıp satmayacağını sorar |
| Fiyat Take Profit'e ulaşır | Capital.com kalanı kapatır |

Emtialarda bir saatlik ATR, günlük aralığın yaklaşık beşte biridir. Böylece üç kademe yaklaşık 0,1, 0,2 ve 0,3 günlük aralıkta, stop ise tam bir günlük aralıkta durur. Bu yüzden kademe başına kâr, stop'taki bir kayıptan belirgin biçimde küçüktür.

Stop merdiveni sayesinde kademe 1'i satmış bir pozisyon artık tam stop ile kapanamaz. Bir sonraki turda fiyat yeni stop'un zaten ötesindeyse (örneğin Capital.com stop'u fiyata çok yakın diye reddettiyse), fiyat geri gelene kadar eski stop kalır. v15.24'ten önce bir kademe satmış pozisyonlar stop'u girişe alır.

### Kısmi satış kuralları

- %25 daha küçük kalsa bile en az borsanın asgari büyüklüğü kadar satılır.
- Satıştan sonra asgari büyüklükten azı kalacaksa bot kalanın tamamını satar. Bu yüzden küçük bir pozisyon daha kademe 2'de tamamen kapanmış olabilir.
- Kısmi satışlar yalnızca Capital.com hesabında Hedging modu kapalıysa çalışır.
- Bot her stop değişikliğinde Take Profit'i de birlikte gönderir. Yoksa Capital.com onu siler.

### Açık pozisyonların stop'ları

`SL_ATR_MULT` için yeni değerler yalnızca yeni pozisyonlarda geçerlidir. `/sl_genislet`, hangi açık stop'ların asgari mesafeden yakın olduğunu gösterir; `/sl_genislet evet` onları uzaklaştırır. Daraltmak yalnızca Capital uygulamasında elle yapılabilir.

## 8. Koruma kuralları ve kilitler

Bu kuralları Python kendisi denetler; hiçbir yapay zekâ onları aşamaz. “Kodda sabit” şu demektir: `.env` üzerinden ayarlanamaz.

### Yeni pozisyondan önce

| Kural | Eşik | Etki | Ayar |
| --- | --- | --- | --- |
| Azami pozisyon sayısı | 5 açık pozisyon | Yeni pozisyon yok. 5 veya daha fazlasında ekleme ve yön değiştirme de yok | `MAX_POSITIONEN` |
| Grup sınırı | Grup başına 2 piyasa | İçinde zaten 2 piyasa açık olan bir gruptan yeni piyasa açılmaz. Gruplar: enerji (Crude, Brent, doğalgaz, ısınma yakıtı, benzin), metaller (altın, gümüş, platin, paladyum, bakır, alüminyum, çinko, nikel), tarım (buğday, mısır, soya, kahve, şeker, pamuk, kakao) ve kripto. Açık bir piyasaya ekleme sayılmaz | `MAX_JE_GRUPPE` |
| Yeniden giriş kilidi | Kapanıştan sonra 6 saat | Aynı sembole aynı yönde yeni giriş yok | `WIEDEREINSTIEG_SPERRE_STD` |
| Kayıp kilidi | Sembol ve gün başına 3 Stop Loss kaybı | Sembol bugün için kilitli; ilk kayıptan itibaren uyarı. Girişteki stop sayılmaz | `MAX_VERLUSTE_PRO_TAG` |
| Günlük kayıp durdurması | Hesap değeri günün zirvesinin %5 veya 40 EUR altında | Bugün yeni işlem yok | kodda sabit |
| Spread | Canlı spread `MAX_SPREAD` üzerinde | İşlem reddedilir | `MAX_SPREAD` |
| Piyasa kapalı | Capital.com'a göre | Emir yok, açılış saatini içeren mesaj | – |
| Marjin | İşlem müsait paranın %90'ından fazlasını gerektirir | İşlem reddedilir | kodda sabit |
| Tutarlılık | Stop veya hedef fiyatın yanlış tarafında ya da canlı fiyat yok | İşlem atılır | – |
| HARD BLOCK (işlem engeli) | Haftalık öğrenme turu (pazartesi saat 6): isabet oranı %33'ün altında olan sembol, yön ve haftanın günü | Sembol yeniden başlatmaya kadar kilitli. Yalnızca adında alt çizgi olmayan sembollerde etkilidir (GOLD evet, OIL_CRUDE hayır) | kodda sabit |
| Hafta sonu | Cumartesi ve pazar | Yalnızca kripto, en fazla 3 kripto pozisyonu | kodda sabit |
| Kripto gece kilidi | 23 ile 6 arası | Varsayılan: kapalı | `KRYPTO_NACHT_SPERRE` |

### Açık pozisyonlar için

| Kural | Eşik | Etki | Ayar |
| --- | --- | --- | --- |
| Kara Kuğu seviye 1 | Pozisyon %8 ekside | Yapay zekâ acil durum kararı: tut ya da kapat | kodda sabit |
| Kara Kuğu seviye 2 | Pozisyon %12 ekside | Pozisyon otomatik kapatılır | kodda sabit |
| Kara Kuğu seviye 3 | Bir pozisyon %18 ekside | Tüm pozisyonlar kapatılır | kodda sabit |
| Auto-Exit | 5 çıkış kuralından 3'ü (sinyal değişimi, çok olumsuz haberler, Risk-off) | Pozisyon kapatılır | `AUTO_EXIT` |

`AUTO_EXIT=false` ile çıkış izleyicisi kendisi kapatmaz, yalnızca bir öneri gönderir.

## 9. Yapay zekâ sağlayıcıları

Ana analizi Gemini yapar. Gemini yanıt vermezse bir yedek sağlayıcı devralır; ancak o yalnızca Gate-Keeper'ın onayladığı adayları TRADE satırlarına dökebilir.

### Gemini model zinciri

Her istek en fazla 4 modelden geçer (`GEMINI_CHAIN_MAX`): önce `GEMINI_MODEL_1` içindeki model, sonra Google'ın canlı listesindeki güncel Flash modelleri. Bot her modelde kullanılabilir tüm anahtarları dener.

| Google'ın yanıtı | Bot ne yapar |
| --- | --- |
| 401, anahtar geçersiz | Anahtar 6 saat kullanılmaz; sıradaki anahtar |
| 429 günlük limit | Sıradaki anahtar. Geçerli tüm anahtarlar limitteyse model sıfırlanmaya kadar (ABD Pasifik saatiyle gece yarısı) bekler ve zincire sıradaki model girer |
| 429 dakika limiti, 403 | Sıradaki anahtar |
| 503 aşırı yüklü | 6 saniye sonra ikinci bir deneme (`GEMINI_503_PAUSE`), ardından sıradaki model |
| 404 veya ücretsiz kota yok | Model 24 saat kilitli, model listesi yeniden alınır |
| başka hata | Bu istek için Gemini'den vazgeçilir |

Model listesi 6 saatte bir kendini günceller; `/update_models` onu hemen alır ve reddedilen anahtarları son dört karakteriyle gösterir.

Aynı Google projesindeki anahtarlar tek bir kotayı paylaşır; bir projeden birden çok anahtar, tek anahtardan daha fazla istek sağlamaz. Ücretsiz kota küçüktür. Tarama aralığı ne kadar kısaysa bot o kadar sık yedek sağlayıcı üzerinden çalışır.

### Yedek sağlayıcı

Sıra `PROVIDER_ORDER` içinde yazar. Yerel Ollama modelini `OLLAMA_PRIORITY` yönetir:

- `last`: Ollama yalnızca tüm bulut sağlayıcıları devre dışı kaldığında.
- `first`: Ollama, bilgisayarda çalışıyorsa herkesten önce yanıt verir.
- `only`: yalnızca Ollama.

Yedek modda yapay zekâ yalnızca stop ve hedefi belirler ya da bir adayı reddeder. Sembol ve yön Gate-Keeper'dan, büyüklük `.env` dosyasından gelir ve stop asgari mesafeye çekilir. Telegram mesajı, başka bir sağlayıcı yanıt vermiş olsa bile her zaman “Groq” der; hangisinin yanıt verdiği log'da `[OK] ...` olarak yazar.

### Yedek sağlayıcıların modelleri (v15.22'den itibaren)

Groq, OpenRouter ve Nvidia modelleri sık sık yayından kaldırır. v15.21'e kadar her sağlayıcı `.env` içindeki tek modelle çalışıyordu ve o model kalkınca devre dışı kalıyordu. Artık bot modelleri kendisi güncel tutar; yöntem swarm.py ile aynıdır:

- **İstek başına zincir.** Bot önce `.env` içindeki modele, ardından sağlayıcının model listesinden en çok üç yedek modele sorar (`AI_CHAIN_MAX`). 401, 403 veya 429 gelirse anahtarı değiştirir; anahtarlar bitince modeli. Aşırı yükte veya boş yanıtta hemen modeli değiştirir.
- **Ölü model.** Sağlayıcı modelin artık olmadığını bildirirse (404, 410, “does not exist”, “No endpoints found”), bot onu 24 saat engeller ve bir kontrol başlatır.
- **Yedek.** Kontrol model listesini alır, sohbet modeli olmayanları ayıklar ve en iyi adayları kısa, gerçek bir çağrıyla dener. Yanıt veren ilk model ana model olur: bot onu `.env` dosyasına yazar, hemen kullanır ve değişikliği Telegram'da bildirir. Önce mevcut modele kendisi sorar ve onu yalnızca gerçekten yanıt vermiyorsa değiştirir. Kontrol sonuçsuz kalırsa (limit, ağ) hiçbir şeyi değiştirmez.
- **Ne zaman kontrol edilir.** Başlangıçtan 75 saniye sonra, ardından her `MODEL_AUTOUPDATE_HOURS` saatte bir ve bir arızadan beş dakika sonra.

Yazmadan önce bot `.env.modelupdate.bak` yedeğini oluşturur. Sonra `.env` dosyasını doğrulamak için yeniden okur; bir değer yanlışsa eski içeriği geri yükler. Yorumlar ve diğer tüm satırlar olduğu gibi kalır.

`/update_models` hemen kontrol eder ve her sağlayıcı için modeli, zinciri ve engelli modelleri gösterir. Yanıt veren model yerinde kalır. `/update_models best` ayrıca kontrolü geçen en büyük modele geçer. `MODEL_AUTOUPDATE_PIN=GROQ_MODEL` (ayrıca `QWEN_MODEL`, `NVIDIA_MODEL`, virgülle ayrılmış) yazarsan bot o sağlayıcının modeline hiç dokunmaz.

- **Qwen:** Bot yalnızca OpenRouter'daki ücretsiz modelleri alır, önce Qwen modellerini. Hiçbiri kontrolü geçmezse başka bir ücretsiz model devreye girer. Kendi yazdığın ücretli model yerinde kalır. `QWEN_BASE_URL` OpenRouter'ı göstermiyorsa bot orada hiçbir şeyi değiştirmez.
- **Maliyet:** Her kontrol Groq ve Nvidia'da kısa bir çağrıya, model değişiminde en çok altı çağrıya daha mal olur.
- **Düşünme metni:** Bir modelin `<think>` ile `</think>` arasına yazdıklarını bot yanıttan çıkarır.

## 10. Mesajları anlamak

Tablolar, mesajın bu dilde sohbette göründüğü hâliyle başlangıcını verir. “…” sembol, fiyat veya saat gibi değerlerin yerine geçer.

### Taramayla ilgili

| Mesaj | Anlamı | Ne yapmalısın |
| --- | --- | --- |
| “🕐 … \| NEXUS … başlatıldı” | Bot başladı | Sürümü ve değerleri kısaca denetle |
| `TRADE: OIL_CRUDE \| SIDE: SELL \| SIZE: 0 ...` | Yapay zekânın ham satırları. SIZE 0 doğrudur, büyüklüğü bot hesaplar. Yalnızca işlem yapıldıysa gelir | Hiçbir şey |
| “✅ POZİSYON ONAYLANDI: …” | Emir gerçekleşti, pozisyon hesapta | Hiçbir şey |
| “⚠️ POZİSYON DOĞRULANAMADI: …” | Emir gönderildi, pozisyon 8 saniye sonra görünmüyor | Capital uygulamasında bak |
| “🔔 İşlem Bildirimi:” | Taramanın protokolü: yeni pozisyon, nedeniyle birlikte stop düzeltmesi, atlanan semboller | Oku |
| “🔔 Yeni işlem olmadan tarama:” | Hiçbir şey açılmadı, nedenleriyle birlikte. Yalnızca nedenler değişince gelir, yoksa 6 saatte bir | Hiçbir şey |
| “TRADE SONRASI DEPO:” | İşlem sonrası hesap: nakit, müsait para, açık kâr/kayıp (UPL) | Hiçbir şey |
| “🟢 … \| NEXUS NATURE v12.0 Tarama #… tamamlandı.” | Yaşam belirtisi: sinyalsiz tarama | Hiçbir şey |
| “INFO … \| Gemini quota doldu → Groq ile devam ediliyor” | Gemini yanıt vermedi, yedek sağlayıcı devraldı. Altında model başına neden yazar | Reddedilen anahtarları değiştir; günlük limitte bekle |
| “🤖 Gemini zinciri güncellendi:” | Model listesi değişti | Hiçbir şey |

### Reddedilen işlemler (protokoldeki satırlar)

| Satır | Anlamı |
| --- | --- |
| “⏳ … : … dk önce kapatıldı - yeniden giriş kilitli, kalan süre … sa … dk (WIEDEREINSTIEG_SPERRE_STD=… )” | Sembol 6 saatten kısa süre önce kapatıldı |
| “⛔ …: MAKS POZİSYON …/… sınırına ulaşıldı - açılmadı” | Açık pozisyon üst sınırına ulaşıldı |
| “… Pyramiding atlandı: …” | Pozisyon açık ama henüz %2 kârda değil |
| “⚠️ UYARI …: Bugün …x kayıp var - Kurul dikkatli olsun” | Uyarı: bugün bu sembolde zaten bir Stop Loss kaybı var |
| “🔴 HARD BLOCK …: Bugün …x kayıp (limit=…) - trade durduruldu” | Bugün için kayıp kilidi |
| “⛔ HARD BLOCK … (…): Kullanıcı talimatı aktif — …” | Haftalık öğrenme turundan gelen HARD BLOCK (işlem engeli) |
| “⛔ SPREAD BLOK …: Canlı spread … > MAX_SPREAD … (.env) - Gemini önerse dahi İŞLEM REDDEDİLDİ” | Spread `MAX_SPREAD` üzerinde |
| “⏰ PİYASA KAPALI: …” | Piyasa kapalı |
| “⛔ FALLBACK-BLOCK … (…): Gate-Keeper onaylamadı (izinli: …)” | Yedek yapay zekâ, Gate-Keeper'ın onaylamadığı bir işlem yapmak istedi |
| “⛔ … : SL/TP makul değil (fiyat … , SL … , TP … ) -> trade iptal edildi” | Stop veya hedef fiyatın yanlış tarafında |
| “Margin ENGEL: …” | Müsait para yetersiz |
| “DEPOT DD ALARMI! Bugün yeni trade YOK.” | Günlük kayıp durdurması: bugün yeni işlem yok |

### Açık pozisyonlar

| Mesaj | Anlamı | Ne yapmalısın |
| --- | --- | --- |
| “🎯 MIRROR-TP Kademe … : …” | Kademe satıldı; miktarı, fiyatı ve kalanı gösterir | Hiçbir şey |
| “Kısmi satış mümkün değil: Capital.com hesabında Hedging modu açık. Lütfen orada kapat, sonra bot kademeli olarak satar.” | Hesap Hedging modunda olduğu için kısmi satış yapılamadı | Capital.com'da Hedging modunu kapat |
| “Breakeven: … +%… → SL=…” | Stop artık girişte | Hiçbir şey |
| “Kısmi çıkış: … +%… \| … birim güvenceye alındı” | Bir sembolün birden çok pozisyonundan en küçüğü kapatıldı | Hiçbir şey |
| “… POZİSYON KAPATILDI: … (…)” | Capital.com kapattı (Stop Loss, Take Profit veya broker); neden, sonuç ve kayıp sayacıyla birlikte | Hiçbir şey |
| “… Kapatıldı (bot/elle): … \| … → … \| Büyüklük … \| Sonuç …” | Bot (Mirror-TP, Exit) veya sen kapattın; sonucu içeren tek satır | Hiçbir şey |
| “🎯 GÜNLÜK ATR HEDEFİNE ULAŞILDI (… günlük)” | Pozisyon günlük aralığın %90'ına ulaştı | Evet veya Hayır'a bas |
| “🔍 ÇIKIŞ ÖNERİSİ: …” | 5 çıkış kuralından 3'ü onaylıyor; `AUTO_EXIT=true` ile bot kendisi kapatır | Hiçbir şey |
| “KARA KUĞU (%…)” | Pozisyon en az %8 ekside, yapay zekâ acil durum kararı | Pozisyona bak |
| “KARA KUĞU ALARMI!” | Pozisyon otomatik kapatıldı (%12 eksiden itibaren) | Hesabı denetle |
| “KARA KUĞU ACİL!” | Bir pozisyon %18 ekside: tüm pozisyonlar kapatılır | Hesabı denetle |
| “🔄 Piramiding Düzeltme:” | Kayıt düzeltmesi: durum kayıtları gerçek hesaba uyarlandı | Hiçbir şey |
| “⚠️ NEXUS NATURE v12.0: API bağlantı hatası! Yeniden deneniyor... (Döngü #…)” | Capital.com'a ulaşılamıyor veya giriş reddedildi | Sorun giderme bölümüne bak |

Bir kapanışta “(fiyatlardan hesaplandı, ücretler hariç)” eki varsa bot hesap kaydını bulamamış ve sonucu giriş, çıkış ve büyüklükten, enstrümanın para biriminde hesaplamıştır.

## 11. .env içindeki ayarlar

Dosya `nexus_ceo.py` ile aynı klasördedir. Değişiklikler yeniden başlatmadan sonra geçerli olur. Yorumlar, ayarın üstünde ayrı bir satıra yazılır. Her ad yalnızca bir kez geçebilir; iki kez yazılmışsa sonuncusu geçerlidir.

### İşlem

| Ayar | Varsayılan | Anlamı |
| --- | --- | --- |
| `BOT_LANGUAGE` | boş | `de`, `en` veya `tr`; boş = bot başlangıçta sorar; `orig` = hiç çevirme |
| `SCAN_INTERVAL_SEC` | 21600 | İki tarama arasındaki saniye |
| `TRADING_ASSETS` | boş | Boş = `capital_markets_config.py` içindeki tüm semboller; yoksa virgülle ayrılmış liste |
| `POSITION_SIZE_PCT` | 10.0 | Hesabın yüzdesi olarak pozisyon büyüklüğü |
| `MIN_POSITION_EUR` | 50.0 | Pozisyon başına asgari tutar |
| `MAX_POSITION_EUR` | boş | Pozisyon başına sabit üst sınır; boş = yalnızca Risk-Parity sınırı |
| `MAX_POSITIONEN` | 5 | Açık pozisyonların azami sayısı |
| `MAX_JE_GRUPPE` | 2 | Grup başına aynı anda en fazla bu kadar açık piyasa; 0 = kapalı |
| `MAX_SPREAD` | 0.5 | Fiyat farkı olarak en yüksek spread (Ask eksi Bid), yüzde değil; boş = limit yok |
| `GREMIUM_MIN_JA` | 4 | 5 oydan gereken EVET oyu sayısı |
| `GREMIUM_MIN_JA_KRYPTO` | 3 | Aynısı kripto için |
| `KRYPTO_NACHT_SPERRE` | false | true = kripto 23 ile 6 arası kilitli |
| `AUTO_EXIT` | false | true = çıkış izleyicisi kendisi kapatır; false = yalnızca öneri |

### Stop Loss, kâr alma, kilitler

| Ayar | Varsayılan | Anlamı |
| --- | --- | --- |
| `SL_ATR_MULT` | 1.0 | Stop'un günlük aralık cinsinden asgari mesafesi. 0 = sabit mesafe %1,5 |
| `SL_MAX_PCT` | 6.0 | Bu mesafe için yüzde olarak üst sınır |
| `ATR_DAILY_PERIOD` | 14 | Ortalama günlük aralık için gün sayısı |
| `ATR_DAILY_ORAN` | 0.90 | Günlük aralığın oranı olarak günlük hedef |
| `MIRROR_TP_ENABLED` | true | Kademeli satış açık veya kapalı |
| `MIRROR_TP_LEVEL_1_MULT`, `_2_`, `_3_` | 0.5, 1.0, 1.5 | Üç kademenin saatlik ATR cinsinden mesafesi |
| `MIRROR_TP_CLOSE_PCT` | 25.0 | Kademe başına pozisyon payı |
| `STOP_LEITER` | true | Satılan her kademeden sonra stop'u çek; false = kapalı |
| `MAX_VERLUSTE_PRO_TAG` | 3 | Kilide kadar sembol ve gün başına Stop Loss kaybı sayısı; 0 = kapalı |
| `WIEDEREINSTIEG_SPERRE_STD` | 6 | Kapanıştan sonra yeniden girişe kadar geçen saat; 0 = kapalı |

### Yapay zekâ ve mesajlar

| Ayar | Varsayılan | Anlamı |
| --- | --- | --- |
| `GEMINI_KEYS` | – | Virgülle ayrılmış; her anahtar yalnızca bir kez |
| `GEMINI_MODEL_1` | – | Zincirin ilk modeli |
| `GEMINI_CHAIN_MAX` | 4 | İstek başına azami model sayısı |
| `GEMINI_503_PAUSE` | 6 | Aşırı yükte ikinci denemeye kadar geçen saniye; 0 = deneme yok |
| `MODEL_AUTOUPDATE`, `_HOURS`, `_NOTIFY` | true, 6, true | Modelleri otomatik güncel tut (Gemini listesi ve yedek sağlayıcılar), saat cinsinden aralık, değişiklikte mesaj |
| `MODEL_AUTOUPDATE_PIN` | – | Botun modelini hiç değiştirmeyeceği sağlayıcılar, örn. `GROQ_MODEL,NVIDIA_MODEL` |
| `AI_CHAIN_MAX` | 4 | Groq, Qwen ve Nvidia için istek başına azami model sayısı |
| `PROVIDER_ORDER` | gemini,groq,qwen,nvidia | Yedek sağlayıcıların sırası |
| `GROQ_KEYS`, `GROQ_MODEL` | – | Groq. Model kalkarsa bot onu kendisi değiştirir |
| `QWEN_KEYS`, `QWEN_MODEL`, `QWEN_BASE_URL` | – | OpenAI uyumlu bir erişim üzerinden Qwen. OpenRouter'da bot modeli kendisi değiştirir |
| `NVIDIA_KEYS`, `NVIDIA_MODEL` | – | Nvidia NIM. Model kalkarsa bot onu kendisi değiştirir |
| `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_PRIORITY` | localhost, –, last | Yerel model; `first`, `last` veya `only` |
| `SCAN_MELDUNGEN` | neu | `neu` = işlemsiz taramayı yalnızca değişiklikte bildir; `alle` = her taramada |

### Erişim ve veri kaynakları

| Ayar | Anlamı |
| --- | --- |
| `TG_TOKEN` | Telegram botunun token'ı |
| `MY_CHAT_ID` | Senin sohbetin; bot yalnızca oradan komut kabul eder |
| `CAPITAL_API_KEY`, `CAPITAL_IDENTIFIER`, `CAPITAL_PASSWORD` | Capital.com erişimi |
| `CAPITAL_URL` | Demo veya canlı adres. Canlı adresle bot gerçek parayla işlem yapar |
| `FRED_API_KEY`, `EIA_API_KEY`, `X_API_BEARER` | Analiz için makro, enerji ve X verileri (isteğe bağlı) |

## 12. Botun dosyaları

Durum dosyalarını bot kendisi yazar; bot çalışırken onları elle düzenleme.

| Dosya | İçerik | Silinebilir mi? |
| --- | --- | --- |
| `nexus_ceo.py` | Program | Hayır |
| `nexus_lang.py` | Almanca, İngilizce, Türkçe metinler | Hayır; onsuz bot özgün metinleri gönderir |
| `nexus_diagnose.py` | Teşhis betiği, yalnızca okur. `/teshis` ile ya da terminalde `python3 nexus_diagnose.py` ile çalışır | Evet; o zaman `/teshis` dosyanın eksik olduğunu bildirir |
| `.env` | Ayarlar ve erişim bilgileri | Hayır |
| `.env.modelupdate.bak` | Son otomatik model değişiminden önceki `.env` yedeği. Aynı erişim bilgilerini içerir | Evet |
| `capital_markets_config.py` | Semboller, epic'ler, asgari büyüklükler, spread'ler (isteğe bağlı) | Evet; bot o zaman dokuz piyasalık yerleşik listeyle işlem yapar |
| `nexus_ceo.log` | Log. Gece yarısı yeni dosyaya geçer, 7 gün saklanır | Evet, eski günler |
| `nexus_quant.db` | Veritabanı: haberler, notların, işlemler, istatistik | Hayır, yoksa notlar ve istatistik gider |
| `trailing_sl_state.json` | Trailing-Stop için en iyi fiyatlar ve hangi Mirror-TP kademelerinin satıldığı | Açık pozisyon varken hayır |
| `positions_seen.json` | Son görülen pozisyonlar ve yeniden giriş kilidi için kapanış saatleri | Evet; kilit o zaman önceki kapanışları unutur |
| `pyramiding_state.json` | Sembol başına pozisyon sayısı; her taramada hesapla karşılaştırılır | Evet |
| `daily_loss_counter.json` | Bugünün kayıp sayacı | Evet; bugünkü kayıp kilidini kaldırır |
| `depot_dd_tracker.json` | Hesabın günlük zirvesi ve günlük kayıp durdurması | Evet; bugünkü durdurmayı kaldırır |
| `daily_tp_state.json` | Hangi günlük hedef sorularının sorulduğu | Evet |
| `nexus_lang_missing.log` | Çevirisi bulunmayan metinler | Evet |

### GitHub'dan gelen listeler

Bot üç listeyi kendi klasöründen değil, gerektiğinde herkese açık `KhungFu/kisilerim` deposundan yükler: `mentor_name.txt` (işlem doktrini; ilk 3000 karakter yapay zekâ talimatına eklenir), `toplam_egitim.txt` ve `Abfrage_Quellen.txt` (haber toplama için haber siteleri ve X hesapları). Böylece her kurulum aynı listeleri kullanır. GitHub'a ulaşılamazsa bot onlarsız devam eder. Listeler `nexus` deposunda tutulur; `kisilerim` onları oradan saatte bir çeker.

## 13. Güncelleme ve geri alma

Bir güncelleme `nexus_ceo.py`, `nexus_lang.py` ve `nexus_diagnose.py` dosyalarından oluşur. Üçü bir bütündür; aşağıdaki komutlar her dosya için geçerlidir.

```bash
cp nexus_ceo.py nexus_ceo.py.bak
cp nexus_lang.py nexus_lang.py.bak
# yeni dosyaları klasöre kopyala, sonra:
python3 -m py_compile nexus_ceo.py && python3 nexus_lang.py && sudo systemctl restart nexus_ceo.service
```

Yeniden başlatma yalnızca iki dosya da hatasızsa çalışır. Başlangıç mesajında sürümü denetle.

Eski duruma dönüş:

```bash
cp nexus_ceo.py.bak nexus_ceo.py
cp nexus_lang.py.bak nexus_lang.py
sudo systemctl restart nexus_ceo.service
```

Durum dosyaları güncellemelerde korunur. HARD BLOCK'lar (işlem engelleri) her yeniden başlatmada kaybolur.

## 14. Sorun giderme

| Belirti | Olası neden | Çözüm |
| --- | --- | --- |
| Yeniden başlatmadan sonra başlangıç mesajı yok | Servis çalışmıyor; çoğunlukla kodda veya `.env` içinde bir hata var ya da `MY_CHAT_ID` eksik | `sudo systemctl status nexus_ceo.service` ve `journalctl -u nexus_ceo.service -n 50 --no-pager` |
| Bot yalnızca bir Chat ID ile yanıt veriyor | `MY_CHAT_ID` boş | Sayıyı `.env` dosyasına yaz, yeniden başlat |
| Bot hiç yanıt vermiyor | Servis durmuş, token yanlış ya da `MY_CHAT_ID` dışında bir sohbetten yazıyorsun | Durumu denetle; `TG_TOKEN` ve `MY_CHAT_ID` değerlerini denetle |
| Mesajlar yanlış dilde veya karışık geliyor | `BOT_LANGUAGE` yanlış, `nexus_lang.py` eksik ya da bir metin için kural yok | `/dil` gönder; `nexus_lang_missing.log` dosyasına bak |
| Bot hiçbir şey açmıyor | Bir kilit devrede ya da Gate-Keeper aday bulamıyor | “🔔 Yeni işlem olmadan tarama:” mesajını oku; `/pozisyon`, `/kayip`, `/bloklar`; hafta sonu yalnızca kripto |
| “INFO … \| Gemini quota doldu → Groq ile devam ediliyor” her taramada geliyor | Anahtarlar reddedildi, günlük limite ulaşıldı ya da ücretsiz kota için çok fazla tarama var | `/update_models`; reddedilen anahtarları değiştir; tarama aralığını uzat |
| Log'da her taramada `Groq key 1 hata: ...` (veya Qwen, Nvidia) yazıyor | Model sağlayıcıda kapatılmış, anahtar reddedilmiş ya da limite ulaşılmış | `/update_models` modeli, zinciri ve engelleri gösterir; `/teshis` her sağlayıcı için en sık hata mesajını verir |
| Kademeler satılmıyor | Hesapta Hedging modu açık, `MIRROR_TP_ENABLED=false` ya da saatlik ATR alınamıyor | Hedging'i kapat; `.env` dosyasını denetle |
| Pozisyon raporu Take Profit göstermiyor | Capital.com'da Take Profit eksik | Capital uygulamasında ekle |
| Pozisyon raporu günlük gürültü konusunda uyarıyor | Stop asgari mesafeden yakın | `/sl_genislet`, ardından `/sl_genislet evet` |
| Pozisyon mesajsız kayboldu | Kapanış mesajı ancak bir sonraki 5 dakikalık turla gelir | Bekle; gelmezse Capital uygulamasında geçmişe bak |
| “⚠️ NEXUS NATURE v12.0: API bağlantı hatası! Yeniden deneniyor... (Döngü #…)” | Capital.com'a ulaşılamıyor veya giriş reddedildi | `.env` içindeki erişim bilgilerini denetle, yeniden başlat |
| Sembol bilinmiyor | Sembol `capital_markets_config.py` içinde veya yerleşik listede yok | Sembolü epic ve asgari büyüklükle birlikte `capital_markets_config.py` içine yaz, yeniden başlat |

Yararlı log sorguları:

```bash
# Stop'lara, kademelere ve kapanışlara ne oldu?
grep -E "Breakeven|MIRROR|Trailing SL|Schliess-Melder|KARA" nexus_ceo.log | tail -40

# Gemini neden yanıt vermiyor ve onun yerine kim yanıt verdi?
grep -E "Gemini .*: (tot|tageslimit|key|keytot|modell|abbruch)|\[OK\]" nexus_ceo.log | tail -40

# Neler reddedildi?
grep -E "MAX POSITIONEN|Wiedereinstieg|HARD BLOK|SPREAD BLOK|KAPALI|FALLBACK-BLOCK|unplausibel" nexus_ceo.log | tail -40

# Hatalar
grep -E "ERROR|Traceback" nexus_ceo.log | tail -20
```

Log özgün dilde kalır (Almanca ve Türkçe karışık); yalnızca Telegram mesajları çevrilir.

## 15. Bilinen sınırlar

### Koddaki hatalar ve tuhaflıklar

- **Yarıya indirme yalnızca dört coin için.** BTC, ETH, SOL ve XRP'de yarıya indirilir. Diğer coin'ler tam büyüklükle çalışır.
- **On iki coin kripto sayılmaz.** Bot kriptoyu sabit bir ad listesinden tanır. Birlikte gelen piyasa listesindeki AAVE, BCH, NEAR, ARB, OP, XLM, ALGO, VET, HBAR, IOTA, TRX ve XTZ bu listede yok. Bunlara emtia kuralları uygulanır: 5 Kurul oyundan 4'ü ve hafta sonu işlem yok.
- **Korelasyon yalnızca kabaca denetlenir.** Grup sınırı grup başına piyasaları sayar, yönü ya da büyüklüğü değil. Petrol ve bakır sık sık birlikte hareket etse de farklı gruplardadır.
- **5 pozisyondan itibaren karşı sinyal işlemez.** 5 veya daha fazla açık pozisyonda bot her denetimden önce durur. O zaman karşı sinyal mevcut pozisyonu da kapatmaz.
- **Bot veritabanındaki istatistik ve günlük hedef eksiktir.** Veritabanı yalnızca botun kendisinin tetiklediği kapanışları bilir. Esas alınacak olan Capital uygulamasındaki dökümdür.
- **Manuel işlem** ne gürültü korumasını ne de `MAX_POSITION_EUR` değerini kullanır.
- **Metinle HARD BLOCK (işlem engeli) çalışmaz.** “gold” gibi sözcükleri bir sembole bağlayan tablo, kodun daha aşağısında aynı adı taşıyan ikinci bir tablo (`ASSET_KEYWORDS`, haberler için) tarafından ezilir. Bu yüzden bot hiçbir cümlede sembol tanımaz ve hiçbir zaman engel koymaz. Hata bilerek düzeltilmedi: düzeltilseydi, içinde “sell”, “close”, “verkaufen” veya “kapat” ile bir sembol adı geçen bir cümle bu sembolün pozisyonlarını hemen kapatırdı.
- **Haftalık öğrenme turundan gelen kilitler** yalnızca adında alt çizgi olmayan sembollerde devreye girer.
- **Yedek modellerin sıralaması** modelin büyüklüğüne, bağlam uzunluğuna ve yaşına göredir, analizin kalitesine göre değil. Otomatik seçilen model eskisinden daha zayıf karar verebilir. Bot her değişikliği bildirir; modeli `.env` içinde yeniden belirleyebilir ve `MODEL_AUTOUPDATE_PIN` ile sabitleyebilirsin.

### Koruma işlevlerinin sınırları

- **Kapanış mesajı:** 5 dakika içinde açılıp yeniden kapanan bir pozisyonu bot görmez.
- **HARD BLOCK'lar (işlem engelleri)** yalnızca bellekte durur ve yeniden başlatmadan sonra kalmaz.
- **Durdurulmuş bot:** Breakeven yok, kademeli satış yok, Trailing yok. Yalnızca Capital.com'daki stop ve hedef etkili kalır.
- **Kârlar ve kayıplar eşit büyüklükte değildir.** Varsayılan kademelerle (0.5 / 1.0 / 1.5) kademeler yaklaşık 0,1 ile 0,3 günlük aralıkta, stop ise tam bir günlük aralıkta durur. Üç kısmi satış birlikte, kalanın stop'unun maliyetinden az getirir. Daha büyük kademeler (örneğin 1.0 / 2.0 / 3.0) ve stop merdiveni bunu hafifletir. Yüksek bir isabet oranı tek başına kâr için yetmez.

### Çevirinin sınırları

- Telegram mesajları çevrilir, log çevrilmez.
- Yapay zekâ metinleri yapay zekânın seçtiği dilde gelir; bot ondan yalnızca ayarlı dili rica eder.
- Haber başlıkları kaynağın dilinde kalır.

### Neler test edildi

İşlevler, taklit Capital.com, Telegram, Gemini, Groq, OpenRouter ve Nvidia yanıtlarına karşı test edildi; gerçek bir canlı hesaba karşı değil. Yedek sağlayıcıların model değişimi gerçek bir log'daki hata mesajlarıyla denendi, ama sağlayıcıların gerçek model listelerine karşı değil. `CAPITAL_URL` değerini canlı adrese çevirmeden önce botu en az bir hafta demo hesapta çalıştır.
