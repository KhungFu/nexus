# 🏛️ Nexus Capital Corp - Autonomous Trading Bot



---

## 🇩🇪 Deutsch

Nexus Capital Corp ist eine hochautomatisierte Handelsstruktur, die nach dem Vorbild großer Investmentgesellschaften (wie Berkshire Hathaway oder Apple) arbeitet. Das System wird von einem zentralen **Nexus CEO** gesteuert, der verschiedene Fachabteilungen (Skripte) delegiert.

### 🏢 Unternehmensstruktur
* **CEO (`nexus_ceo.py`):** Strategische Leitung, Krisenmanagement (API-Limits) und Budgetkontrolle.
* **Strategy (`gemini.py`):** KI-gestützte Marktanalyse (Gemini Pro/Flash) basierend auf der Handels-Doktrin.
* **Operations (`capital.py`):** Direkte Ausführung an der Capital.com API (Orders & Positionsmanagement).
* **Research (`nexus_scanner.py`):** Deep-Scan aller verfügbaren Märkte und Erstellung der Marktberichte.
* **Communications (`telegram.py`):** Reporting und Alarmierung via Telegram.

### 🚀 Installation
1.  Klonen Sie das Repository.
2.  Führen Sie den Installer aus: `chmod +x one_click_install.sh && ./one_click_install.sh`
3.  Konfigurieren Sie die `.env` Datei mit Ihren API-Keys.

---

## 🇺🇸 English

Nexus Capital Corp is a highly automated trading framework modeled after major investment firms. Managed by a central **Nexus CEO**, the system delegates tasks to specialized departments (scripts).

### 🏢 Corporate Structure
* **CEO (`nexus_ceo.py`):** Strategic leadership, crisis management (API limits), and budget oversight.
* **Strategy (`gemini.py`):** AI-driven market analysis using Gemini Pro/Flash based on the "Doctrine."
* **Operations (`capital.py`):** Execution layer via Capital.com API (Opening/Closing positions).
* **Research (`nexus_scanner.py`):** Deep-scan of all available markets for opportunity discovery.
* **Communications (`telegram.py`):** Investor relations and alerting via Telegram.

### 🚀 Quick Start
1.  Clone the repository.
2.  Run the installer: `chmod +x one_click_install.sh && ./one_click_install.sh`
3.  Configure your `.env` file with your credentials.

---

## 🇹🇷 Türkçe

Nexus Capital Corp, büyük yatırım şirketlerinin (Apple veya Berkshire Hathaway gibi) yapısını örnek alan tam otonom bir ticaret sistemidir. Sistem, uzmanlaşmış departmanları (scriptleri) yöneten merkezi bir **Nexus CEO** tarafından idare edilir.

### 🏢 Kurumsal Yapı
* **CEO (`nexus_ceo.py`):** Stratejik liderlik, kriz yönetimi (API limitleri) ve bütçe kontrolü.
* **Strateji (`gemini.py`):** Ticaret doktrinine dayalı, Gemini AI destekli piyasa analizi.
* **Operasyon (`capital.py`):** Capital.com API üzerinden emirlerin iletilmesi ve pozisyon yönetimi.
* **Araştırma (`nexus_scanner.py`):** Tüm piyasaların derinlemesine taranması ve raporlanması.
* **İletişim (`telegram.py`):** Telegram üzerinden raporlama ve acil durum bildirimleri.

### 🚀 Hızlı Kurulum
1.  Depoyu (repository) klonlayın.
2.  Yükleyiciyi çalıştırın: `chmod +x one_click_install.sh && ./one_click_install.sh`
3.  `.env` dosyasını API anahtarlarınızla düzenleyin.

---

## ⚖️ Rules & Logic (All Languages)
* **Survival Mode:** If balance < 100€, only Commodities (Gold, Oil, etc.) are traded. / Wenn < 100€, nur Rohstoffe. / 100€ altı bütçede sadece emtialar işlem görür.
* **API Guard:** Automatic 60-minute pause on Rate Limits. / 60 Min. Pause bei API Limit. / API limiti durumunda 60 dakika otomatik bekleme.
* **Weekend:** Crypto trading only if balance > 100€. / Wochenende: Crypto nur > 100€. / Hafta sonu: Sadece 100€ üstü bütçeyle Kripto ticareti.

---

📱 Installation auf Termux (Android)
Nexus Capital Corp kann auch mobil auf deinem Smartphone laufen:

Termux öffnen und System updaten:

```shell
pkg update && pkg upgrade
```

Python & Git installieren:

```shell
pkg install python git
```

Repository klonen (oder Dateien manuell kopieren):

```shell
wget https://raw.githubusercontent.com/KhungFu/nexus/main/one_click_install.sh && chmod +x one_click_install.sh && ./one_click_install.sh
```

⚙️ Konfiguration
Trage deine API-Keys in der erstellten .env Datei ein:

CAPITAL_API_KEY: Dein Key von Capital.com

TELEGRAM_TOKEN: Dein Bot-Token vom BotFather

GEMINI_API_KEY_1: Dein Google AI Studio Key

---
```shell
curl -s https://raw.githubusercontent.com/KhungFu/nexus/main/one_click_install.sh | bash
```
