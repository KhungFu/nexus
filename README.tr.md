# NEXUS CEO

Capital.com API üzerinden emtia ve kripto CFD'leri işleyen Telegram botu: piyasaları tarar, pozisyon açar, Stop Loss kurallarıyla korur ve kademeli olarak satar. Mesajlar ve komutlar **Türkçe, Almanca ve İngilizce** olarak kullanılabilir.

English: [README.md](README.md) · Deutsch: [README.de.md](README.de.md)

> **Risk uyarısı.** Bu bir hobi projesidir; finansal ürün ya da yatırım tavsiyesi değildir. CFD işlemlerinde yatırdığın paranın tamamını kaybedebilirsin. Kod, canlı bir hesapla değil, taklit edilmiş aracı kurum yanıtlarıyla test edildi. Önce ve en az bir hafta **demo hesapta** çalıştır. Kullanım kendi sorumluluğundadır, garanti verilmez.

## Hızlı başlangıç

1. Sürekli açık kalan bir bilgisayarda (Linux, örneğin Raspberry Pi) Python 3.10 veya daha yenisi.
2. `pip install -r requirements.txt`
3. `cp .env.example .env && chmod 600 .env`, sonra Telegram token'ını, Capital.com giriş bilgilerini ve en az bir Gemini key'ini yaz.
4. `python3 nexus_ceo.py`
5. Telegram'da botuna herhangi bir şey yaz. Sana chat ID'ni söyler. Bunu `.env` dosyasına `MY_CHAT_ID` olarak yaz ve botu yeniden başlat.
6. Sonraki başlangıçta bot dili sorar. Birine dokun, onayla, tamam. Bot `BOT_LANGUAGE` satırını `.env` dosyasına kendisi yazar.

Tüm komutlar, ayarlar ve bilinen sınırlar kılavuzda:

- [Kullanım Kılavuzu (Türkçe)](docs/MANUAL.tr.md)
- [Betriebsanleitung (Deutsch)](docs/MANUAL.de.md)
- [Manual (English)](docs/MANUAL.en.md)

## Dosyalar

| Dosya | Amaç |
| --- | --- |
| `nexus_ceo.py` | Bot |
| `nexus_lang.py` | Tüm Telegram metinleri: Almanca, İngilizce, Türkçe |
| `nexus_diagnose.py` | Yalnızca okuyan teşhis: sürüm, ayarlar, log, pozisyon başına sonuç. Telegram'da `/teshis` gönder ya da `python3 nexus_diagnose.py` çalıştır |
| `.env.example` | Ayarların için şablon. `.env` olarak kopyala |
| `requirements.txt` | Python paketleri |
| `systemd/nexus_ceo.service.example` | Botu servis olarak çalıştırmak için şablon |
| `docs/` | Üç dilde kılavuz |
| `capital_markets_config.py` | Piyasa listesi: semboller, epic'ler, asgari büyüklükler, spread'ler. Bu dosya yoksa bot, içine gömülü dokuz piyasalık listeyi işler |
| `market_scanner.py` | `capital_markets_config.py` dosyasını kendi Capital.com hesabından yeniden üretir |
| `hesap_bul.py` | Capital.com girişini sınar, demo ve canlı hesaplarını listeler. Sondaki `CAPITAL_ACCOUNT_ID` ve `IS_DEMO` notu eski bir sürümden kalma; bot `CAPITAL_URL` kullanır |
| `mentor_name.txt`, `toplam_egitim.txt`, `Abfrage_Quellen.txt`, `NewsVerlage.txt`, `Audiobooks.txt`, `Bot_egitim_videolari.txt` | Doktrin ve kaynak listeleri. Herkese açık `KhungFu/kisilerim` deposu bunları saatte bir buradan çeker; bot ilk üçünü çalışırken oradan okur, kendi klasöründen değil |

## Anahtarların gizli kalır

`.env` dosyasında şifreler ve API key'leri var. `.gitignore` onu dışarıda tutar, yani Git onu asla yüklemez. Adını değiştirme, içeriğini hiçbir yere yapıştırma ve ilk push'tan önce `git status` ile kontrol et.

## Dil

Bot ilk başlangıçta dili sorar. Sonradan `/dil`, `/sprache` veya `/language` ile değiştirirsin. Her komutun her dilde bir adı var ve tüm adlar her zaman çalışır.

## Lisans

MIT, bkz. [LICENSE](LICENSE).
