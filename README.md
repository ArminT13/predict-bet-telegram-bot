# 🎯 Predict & Bet Telegram Bot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/Telegram-Bot%20API-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram API" />
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/Currency-100%25%20Fake%20%2F%20Virtual-yellow?style=for-the-badge" alt="Virtual Currency" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <b>A fun, casual Telegram bot for predicting match outcomes and friendly betting using purely virtual, fake currency.</b>
</p>

---

## ⚠️ Disclaimer

> **This bot is built exclusively for entertainment and casual friendly competition.**  
> All bets, balances, points, and rewards operate entirely on **100% fake virtual currency** with **zero real-world monetary value**. This project does not support real-money transactions, payment gateways, or financial betting of any kind.

---

## 📖 Overview

**Predict & Bet Telegram Bot** is a lightweight Python application that lets you and your friends wager fake points on sports matches, esports, game nights, or custom challenges. With a local SQLite database and environment-based secret management, it is simple to self-host and customize.

---

## ✨ Features

- 🪙 **Virtual-Only Economy:** Uses strictly fake coins/points designed for casual banter and friendly stakes.
- 🎲 **Match Predictions:** Browse upcoming fixtures and submit predictions with customizable odds/stakes.
- 🏆 **Leaderboard:** Track friend rankings and see who holds the highest point balance.
- 🛡️ **Admin Dashboard:** Create custom events, resolve match results, and automate point payouts.
- 💾 **SQLite Storage:** Lightweight and portable database with zero external database configuration required.
- 🔒 **Secure Configuration:** Keeps sensitive credentials (bot tokens, admin IDs) isolated from version control.

---

## 🤖 Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Register an account, claim initial fake welcome coins, and start playing |
| `/help` | Display instructions and usage guidance |
| `/predict` | View active matches and submit predictions |
| `/mybets` | Check open wagers and settled prediction history |
| `/leaderboard` | View current top players ranked by virtual coin balance |
| `/admin` | Open match creation and resolution controls *(Authorized admins only)* |

---

## 📂 Project Structure

```text
predict-bet-telegram-bot/
├── main.py              # Bot entry point, routing, and core business logic
├── requirements.txt     # Python dependencies
├── .env.example         # Template for environment variables
├── .gitignore           # Files to ignore in Git (e.g., game_bet.db, .env)
└── README.md            # Project documentation
