# 🤖 Telegram Prediction & Betting Bot | ربات پیش‌بینی و شرط‌بندی تلگرام

This is a professional and lightweight Telegram bot written in Python using the `pyTelegramBotAPI` library. It allows users to register, place, and manage bets, featuring an SQLite database integration and paginated data retrieval.

این یک ربات تلگرام حرفه‌ای و سبک است که با زبان پایتون و کتابخانه `pyTelegramBotAPI` توسعه یافته است. این ربات به کاربران امکان ثبت، مدیریت و پیگیری شرط‌بندی‌ها و پیش‌بینی‌ها را می‌دهد و از دیتابیس SQLite و سیستم صفحه‌بندی (Pagination) برای نمایش اطلاعات استفاده می‌کند.

---

## ✨ Features | قابلیت‌ها

* **Interactive Betting Wizard:** A step-by-step wizard to register and configure bets.
* **SQLite Integration:** Uses SQLite to locally store user data and active/past bets securely.
* **Data Pagination:** Smart pagination for viewing active bets without cluttering the chat.
* **Admin Controls:** Specific commands restricted to bot administrators.
* **Asynchronous & Threaded:** Built-in multi-threading to handle multiple users simultaneously.

* **ثبت آسان پیش‌بینی‌ها:** دارای ویزارد مرحله‌به‌مرحله و تعاملی برای ثبت شرط‌ها.
* **پشتیبان‌گیری با SQLite:** ذخیره‌سازی امن اطلاعات کاربران و تاریخچه شرط‌ها در دیتابیس محلی.
* **صفحه‌بندی داده‌ها (Pagination):** نمایش مرتب و صفحه‌بندی‌شده‌ی شرط‌های فعال برای جلوگیری از شلوغی چت.
* **کنترل پنل ادمین:** دستورات اختصاصی و محدودشده برای مدیریت ربات توسط ادمین‌ها.
* **پشتیبانی از Multi-threading:** پردازش همزمان درخواست‌های چندین کاربر بدون افت سرعت.

---

## 📁 Project Structure | ساختار فایل‌ها

```text
├── main.py                 # Bot's entry point and core logic
├── requirements.txt        # Third-party dependencies
├── .gitignore              # Files to ignore in Git (e.g., game_bet.db)
└── README.md               # Project documentation

🛠 Setup & Installation | نصب و راه‌اندازی
Prerequisites | پیش‌نیازها
Make sure you have Python 3.8+ installed on your system.
مطمئن شوید که پایتون نسخه ۳.۸ یا بالاتر روی سیستم شما نصب است.

1. Clone the Repository | دانلود پروژه
Bash
git clone https://github.com/ArminT13/predict-bet-telegram-bot.git
cd predict-bet-telegram-bot
2. Install Dependencies | نصب کتابخانه‌ها
Install the required libraries using pip:
کتابخانه‌های مورد نیاز را با دستور زیر نصب کنید:

Bash
pip install -r requirements.txt
3. Environment Variables | تنظیم متغیرهای محیطی
Set up your bot token and admin IDs as environment variables. Do not hardcode them in the script!
توکن ربات و آیدی عددی ادمین‌ها را به عنوان متغیرهای محیطی (Environment Variables) تعریف کنید تا امنیت پروژه حفظ شود:

On Linux/macOS:

Bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export ADMIN_IDS="12345678,87654321"
On Windows (CMD):

DOS
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set ADMIN_IDS=12345678,87654321
4. Run the Bot | اجرای ربات
Once everything is configured, start the bot by running:
پس از انجام تنظیمات، ربات را با دستور زیر روشن کنید:

Bash
python main.py
🔒 Security Note | نکات امنیتی
Never commit your .env or game_bet.db files to GitHub! Make sure they are listed in your .gitignore to protect your bot token and database records.

هرگز فایل دیتابیس (game_bet.db) یا توکن ربات خود را روی گیت‌هاب آپلود نکنید. مطمئن شوید این فایل‌ها در .gitignore قرار دارند.

🤝 Contributing | مشارکت
Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.

مشارکت در بهبود پروژه، گزارش باگ‌ها و ارائه پیشنهادها همواره با آغوش باز پذیرفته می‌شود. در صورت تمایل می‌توانید یک Issue یا Pull Request ثبت کنید.
