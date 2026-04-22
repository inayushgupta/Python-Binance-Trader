# 🤖 Binance Futures Testnet Trading Bot

A clean, well-structured Python CLI trading bot that places **Market**, **Limit**, and **Stop-Limit** orders on **Binance USDT-M Futures Testnet**.

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance API client wrapper
│   ├── orders.py          # Order placement logic + OrderResult
│   ├── validators.py      # Input validation
│   └── logging_config.py  # Rotating file + console logging
├── logs/                  # Auto-created; daily rotating log files
├── cli.py                 # CLI entry point (Typer + Rich + questionary)
├── .env.example           # Template for API credentials
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Clone / unzip the project

```bash
cd trading_bot
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Binance Futures Testnet API keys

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Click **"Sign In"** → authenticate with GitHub or Gmail
3. Once logged in, go to the **"API Key"** tab (top menu)
4. Click **"Generate Key"** — your API Key and Secret will appear
5. Copy both values (the secret is shown **only once**)

### 5. Configure credentials

```bash
cp .env.example .env
```

Edit `.env`:

```env
BINANCE_API_KEY=your_actual_api_key
BINANCE_API_SECRET=your_actual_api_secret
```

---

## 🚀 How to Run

### Direct (non-interactive) mode

**Place a MARKET order:**
```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Place a LIMIT order:**
```bash
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 80000
```

**Place a STOP (Stop-Limit) order:** *(bonus)*
```bash
python cli.py place --symbol BTCUSDT --side BUY --type STOP \
  --quantity 0.001 --price 82000 --stop-price 81500
```

**Check account balances:**
```bash
python cli.py account
```

### Interactive (guided) mode *(bonus)*

```bash
python cli.py interactive
```

Walks you through symbol → side → type → quantity → price with
selection menus, validation, and a confirmation prompt before submitting.

### Help

```bash
python cli.py --help
python cli.py place --help
```

---

## 📋 CLI Options Reference

| Option | Short | Required | Description |
|---|---|---|---|
| `--symbol` | `-s` | ✅ | Trading pair (e.g. `BTCUSDT`) |
| `--side` | | ✅ | `BUY` or `SELL` |
| `--type` | `-t` | ✅ | `MARKET`, `LIMIT`, or `STOP` |
| `--quantity` | `-q` | ✅ | Order size |
| `--price` | `-p` | LIMIT / STOP | Limit price in USDT |
| `--stop-price` | | STOP only | Trigger price in USDT |
| `--tif` | | optional | Time-in-force: `GTC` (default) / `IOC` / `FOK` |

---

## 📜 Logging

All API requests, responses, and errors are logged to:

```
logs/trading_bot_YYYYMMDD.log
```

- **File**: `DEBUG` and above — full request params, raw response payloads, errors with tracebacks
- **Console**: `WARNING` and above — keeps the terminal clean
- Log files rotate at **10 MB**, keeping the last **7 files**

---

## 🧱 Assumptions

- Uses `python-binance` with `testnet=True`, which automatically points to `https://testnet.binancefuture.com`
- Quantities and prices must satisfy Binance Futures symbol filters (`LOT_SIZE`, `PRICE_FILTER`). Invalid values will be rejected by the API with a clear error message.
- STOP orders use Binance Futures type `STOP` (Stop-Limit), not `STOP_MARKET`.
- Credentials are read from a `.env` file via `python-dotenv`.

---

## 🎁 Bonus Features Implemented

| Feature | Details |
|---|---|
| **Stop-Limit orders** | `--type STOP` with `--price` and `--stop-price` |
| **Interactive CLI** | `python cli.py interactive` — guided menus + confirmation prompt |
| **Rich UI output** | Colour-coded tables for request summary and order response |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `python-binance` | Binance REST API client |
| `python-dotenv` | Load `.env` credentials |
| `typer[all]` | CLI framework |
| `rich` | Terminal formatting |
| `questionary` | Interactive prompts / select menus |
