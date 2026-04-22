# Binance Futures Testnet Trading Bot

I built this focused CLI tool to place orders on Binance USDT-M Futures Testnet. The goal was not to build "just another script". It was to show clean architecture, proper error handling, and a good developer experience for anyone running it.

It supports **Market, Limit, and Stop-Limit** orders, and comes with both a direct command mode and a guided interactive mode.

### Why Testnet?
No real money, same API behavior. Perfect for demonstrating logic safely.

## What it can do

- Place MARKET orders instantly
- Place LIMIT orders with time-in-force options
- Place STOP orders (Stop-Limit, not Stop-Market)
- Check your futures account balance
- Run in interactive mode with menus and validation
- Log everything to rotating files for debugging

## Project structure

I kept it modular so each piece has one job:

```
trading_bot/
├── bot/
│   ├── client.py          # Wraps python-binance, handles testnet connection
│   ├── orders.py          # Builds and places orders, returns a clean OrderResult
│   ├── validators.py      # Validates symbol, side, qty, price before hitting API
│   └── logging_config.py  # Sets up console + rotating file logs
├── logs/                  # Created automatically
├── cli.py                 # The Typer CLI, direct and interactive modes live here
├── .env.example
├── requirements.txt
└── README.md
```

## Setup, takes about 3 minutes

**1. Get the code**
```bash
cd trading_bot
```

**2. Create a venv**
```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

**3. Install**
```bash
pip install -r requirements.txt
```

**4. Get Testnet keys**
1. Go to https://testnet.binancefuture.com
2. Sign in with GitHub
3. Open the API Key tab and click Generate Key
4. Copy the key and secret. The secret is shown only once.

**5. Add your keys**
```bash
cp .env.example .env
```
Then edit `.env`:
```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

That's it.

## How to use it

### 1. Direct mode, great for scripts
```bash
# Market buy 0.001 BTC
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit sell at 80k
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 80000

# Stop-Limit buy: trigger at 81,500, limit at 82,000
python cli.py place --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 82000 --stop-price 81500

# Check balance
python cli.py account
```

### 2. Interactive mode, my favorite for demos
```bash
python cli.py interactive
```
It walks you through symbol, side, type, quantity, and price with dropdowns, validates each input, and shows a confirmation table before submitting. No typos, no surprises.

## CLI options

| Flag | Short | Needed for | What it does |
|---|---|---|---|
| `--symbol` | `-s` | always | e.g., BTCUSDT |
| `--side` |  | always | BUY or SELL |
| `--type` | `-t` | always | MARKET, LIMIT, STOP |
| `--quantity` | `-q` | always | Order size |
| `--price` | `-p` | LIMIT, STOP | Your limit price |
| `--stop-price` |  | STOP only | Trigger price |
| `--tif` |  | optional | GTC, IOC, or FOK (defaults to GTC) |

## Logging

I did not want to clutter the terminal, so:

- Console shows warnings and errors only
- `logs/trading_bot_YYYYMMDD.log` captures everything at DEBUG level, including full request params and raw API responses
- Logs rotate at 10MB and keep the last 7 files

If something fails on Binance's side, you can open the log and see exactly what was sent.

## Tech choices

- **python-binance**: official wrapper, supports `testnet=True` out of the box
- **Typer + Rich + questionary**: fast CLI building, beautiful tables, and safe interactive prompts
- **python-dotenv**: keeps secrets out of code
- **Validators**: I validate locally first to fail fast, then let Binance enforce LOT_SIZE and PRICE_FILTER rules

## What I'd improve next

If this were going to production, I'd add:
1. Websocket stream for order status updates
2. A simple backtesting layer using historical klines
3. Unit tests for validators with pytest
4. Docker file for one-command setup
