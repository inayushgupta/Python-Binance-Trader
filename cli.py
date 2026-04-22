#!/usr/bin/env python3
"""
cli.py — Binance Futures Testnet Trading Bot
CLI entry point (Typer + Rich + questionary)

Direct mode:
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 80000
  python cli.py place --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 82000 --stop-price 81000
  python cli.py account
  python cli.py interactive
"""

import os
import sys
from typing import Optional

import questionary
import typer
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logging
from bot.orders import OrderManager, OrderResult
from bot.validators import VALID_ORDER_TYPES, VALID_SIDES, ValidationError

# ── Bootstrap ──────────────────────────────────────────────────────────────────
load_dotenv()
logger = setup_logging()
console = Console()

app = typer.Typer(
    name="trading-bot",
    help="🤖  Binance Futures Testnet Trading Bot",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_client() -> BinanceFuturesClient:
    """Load credentials from env and return an initialised client."""
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        console.print(
            Panel(
                "[bold red]API credentials not found![/bold red]\n\n"
                "Copy [cyan].env.example[/cyan] → [cyan].env[/cyan] and fill in your keys.\n"
                "Get testnet keys at: [link=https://testnet.binancefuture.com]"
                "https://testnet.binancefuture.com[/link]",
                title="⚠️  Configuration Error",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)
    return BinanceFuturesClient(api_key=api_key, api_secret=api_secret)


def _print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> None:
    table = Table(title="📋  Order Request Summary", box=box.ROUNDED, border_style="cyan")
    table.add_column("Field", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")

    side_display = f"[green]{side}[/green]" if side == "BUY" else f"[red]{side}[/red]"
    table.add_row("Symbol", symbol)
    table.add_row("Side", side_display)
    table.add_row("Order Type", order_type)
    table.add_row("Quantity", str(quantity))
    if price is not None:
        table.add_row("Price (USDT)", f"{price:,.2f}")
    if stop_price is not None:
        table.add_row("Stop Price (USDT)", f"{stop_price:,.2f}")

    console.print(table)


def _print_order_result(result: OrderResult) -> None:
    if not result.success:
        console.print(
            Panel(
                f"[bold red]{result.error}[/bold red]",
                title="❌  Order Failed",
                border_style="red",
            )
        )
        logger.error("Order failed: %s", result.error)
        raise typer.Exit(code=1)

    table = Table(title="✅  Order Response", box=box.ROUNDED, border_style="green")
    table.add_column("Field", style="bold green", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Order ID", str(result.order_id))
    table.add_row("Symbol", result.symbol or "—")
    table.add_row("Side", result.side or "—")
    table.add_row("Type", result.order_type or "—")
    table.add_row("Status", f"[bold yellow]{result.status}[/bold yellow]")
    table.add_row("Orig Qty", result.orig_qty or "—")
    table.add_row("Executed Qty", result.executed_qty or "—")

    avg = result.avg_price
    table.add_row("Avg Price", f"{float(avg):,.4f}" if avg and avg != "0" else "—")

    if result.price and result.price != "0":
        table.add_row("Limit Price", f"{float(result.price):,.4f}")
    if result.stop_price and result.stop_price != "0":
        table.add_row("Stop Price", f"{float(result.stop_price):,.4f}")

    console.print(table)
    console.print(
        Panel(
            f"[bold green]Order placed successfully![/bold green]  "
            f"orderId=[cyan]{result.order_id}[/cyan]  status=[yellow]{result.status}[/yellow]",
            border_style="green",
        )
    )


# ── Commands ───────────────────────────────────────────────────────────────────

@app.command()
def place(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair, e.g. BTCUSDT"),
    side: str = typer.Option(..., "--side", help="BUY or SELL"),
    order_type: str = typer.Option(..., "--type", "-t", help="MARKET | LIMIT | STOP"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Order quantity"),
    price: Optional[float] = typer.Option(None, "--price", "-p", help="Limit / Stop-Limit price (USDT)"),
    stop_price: Optional[float] = typer.Option(None, "--stop-price", help="Trigger price for STOP orders"),
    time_in_force: str = typer.Option("GTC", "--tif", help="Time-in-force: GTC | IOC | FOK"),
) -> None:
    """Place a MARKET, LIMIT, or STOP order on Binance Futures Testnet."""

    logger.info(
        "CLI place command — symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
        symbol, side, order_type, quantity, price, stop_price,
    )

    console.print()
    _print_request_summary(symbol, side, order_type.upper(), quantity, price, stop_price)
    console.print()

    client = _build_client()
    manager = OrderManager(client)

    result = manager.dispatch(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )

    console.print()
    _print_order_result(result)


@app.command()
def account() -> None:
    """Display Binance Futures Testnet account balances."""
    logger.info("CLI account command")
    client = _build_client()

    try:
        info = client.get_account_info()
    except (BinanceAPIException, BinanceRequestException) as exc:
        console.print(Panel(f"[red]{exc}[/red]", title="❌ API Error", border_style="red"))
        raise typer.Exit(code=1)

    table = Table(
        title="💰  Account Balances (non-zero)",
        box=box.ROUNDED,
        border_style="magenta",
    )
    table.add_column("Asset", style="bold magenta")
    table.add_column("Wallet Balance", style="white", justify="right")
    table.add_column("Unrealised PnL", style="white", justify="right")
    table.add_column("Margin Balance", style="white", justify="right")

    for asset in info.get("assets", []):
        wb = float(asset.get("walletBalance", 0))
        if wb == 0:
            continue
        table.add_row(
            asset.get("asset", "—"),
            f"{wb:,.4f}",
            f"{float(asset.get('unrealizedProfit', 0)):,.4f}",
            f"{float(asset.get('marginBalance', 0)):,.4f}",
        )

    console.print()
    console.print(table)
    console.print(
        Panel(
            f"Total Wallet Balance: [bold cyan]{info.get('totalWalletBalance', '—')} USDT[/bold cyan]\n"
            f"Available Balance:    [bold green]{info.get('availableBalance', '—')} USDT[/bold green]",
            title="📊  Summary",
            border_style="cyan",
        )
    )


@app.command()
def interactive() -> None:
    """
    [bold cyan]Bonus[/bold cyan]: Guided interactive order placement with menus and prompts.
    """
    console.print(
        Panel(
            "[bold cyan]Binance Futures Testnet — Interactive Mode[/bold cyan]\n"
            "Answer the prompts below to build and place your order.",
            border_style="cyan",
        )
    )

    # ── Gather inputs ──────────────────────────────────────────────────────────
    symbol: str = questionary.text(
        "Trading pair (e.g. BTCUSDT):",
        default="BTCUSDT",
        validate=lambda v: True if v.strip() else "Symbol cannot be empty.",
    ).ask()
    if symbol is None:
        raise typer.Exit()

    side: str = questionary.select(
        "Order side:",
        choices=["BUY", "SELL"],
    ).ask()
    if side is None:
        raise typer.Exit()

    order_type: str = questionary.select(
        "Order type:",
        choices=["MARKET", "LIMIT", "STOP (Stop-Limit)"],
    ).ask()
    if order_type is None:
        raise typer.Exit()
    order_type = order_type.split()[0]   # strip the "(Stop-Limit)" annotation

    quantity_str: str = questionary.text(
        "Quantity:",
        validate=lambda v: True if _is_positive_float(v) else "Enter a positive number.",
    ).ask()
    if quantity_str is None:
        raise typer.Exit()
    quantity = float(quantity_str)

    price: Optional[float] = None
    stop_price: Optional[float] = None

    if order_type in {"LIMIT", "STOP"}:
        price_str: str = questionary.text(
            "Limit price (USDT):",
            validate=lambda v: True if _is_positive_float(v) else "Enter a positive number.",
        ).ask()
        if price_str is None:
            raise typer.Exit()
        price = float(price_str)

    if order_type == "STOP":
        stop_str: str = questionary.text(
            "Stop / trigger price (USDT):",
            validate=lambda v: True if _is_positive_float(v) else "Enter a positive number.",
        ).ask()
        if stop_str is None:
            raise typer.Exit()
        stop_price = float(stop_str)

    # ── Confirm ────────────────────────────────────────────────────────────────
    console.print()
    _print_request_summary(symbol, side, order_type, quantity, price, stop_price)
    console.print()

    confirmed: bool = questionary.confirm("Place this order?", default=False).ask()
    if not confirmed:
        console.print("[yellow]Order cancelled by user.[/yellow]")
        raise typer.Exit()

    # ── Dispatch ───────────────────────────────────────────────────────────────
    logger.info(
        "Interactive order — symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
        symbol, side, order_type, quantity, price, stop_price,
    )
    client = _build_client()
    manager = OrderManager(client)
    result = manager.dispatch(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )
    console.print()
    _print_order_result(result)


# ── Utilities ──────────────────────────────────────────────────────────────────

def _is_positive_float(value: str) -> bool:
    try:
        return float(value) > 0
    except (ValueError, TypeError):
        return False


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
