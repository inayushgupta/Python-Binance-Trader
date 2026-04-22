"""Input validation for trading bot parameters."""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP"}   # STOP = Stop-Limit (bonus)


class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""


def validate_symbol(symbol: str) -> str:
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol cannot be empty.")
    symbol = symbol.upper().strip()
    if not symbol.isalnum():
        raise ValidationError(
            f"Invalid symbol '{symbol}': must be alphanumeric (e.g. BTCUSDT)."
        )
    if not (3 <= len(symbol) <= 20):
        raise ValidationError(
            f"Invalid symbol length '{symbol}': expected 3–20 characters."
        )
    logger.debug("Symbol validated: %s", symbol)
    return symbol


def validate_side(side: str) -> str:
    side = side.upper().strip()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}': must be one of {sorted(VALID_SIDES)}."
        )
    logger.debug("Side validated: %s", side)
    return side


def validate_order_type(order_type: str) -> str:
    order_type = order_type.upper().strip()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}': must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    logger.debug("Order type validated: %s", order_type)
    return order_type


def validate_quantity(quantity: Optional[float]) -> float:
    if quantity is None:
        raise ValidationError("Quantity is required.")
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError("Quantity must be a valid number.")
    if quantity <= 0:
        raise ValidationError(f"Quantity must be > 0 (got {quantity}).")
    logger.debug("Quantity validated: %s", quantity)
    return quantity


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    if order_type in {"LIMIT", "STOP"}:
        if price is None:
            raise ValidationError(f"Price is required for {order_type} orders.")
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValidationError("Price must be a valid number.")
        if price <= 0:
            raise ValidationError(f"Price must be > 0 (got {price}).")
    elif price is not None:
        price = float(price)
    logger.debug("Price validated: %s (type=%s)", price, order_type)
    return price


def validate_stop_price(stop_price: Optional[float], order_type: str) -> Optional[float]:
    if order_type == "STOP":
        if stop_price is None:
            raise ValidationError("Stop price is required for STOP orders.")
        try:
            stop_price = float(stop_price)
        except (TypeError, ValueError):
            raise ValidationError("Stop price must be a valid number.")
        if stop_price <= 0:
            raise ValidationError(f"Stop price must be > 0 (got {stop_price}).")
    elif stop_price is not None:
        stop_price = float(stop_price)
    logger.debug("Stop price validated: %s", stop_price)
    return stop_price


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> Tuple[str, str, str, float, Optional[float], Optional[float]]:
    """Run all validations and return normalised values."""
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)
    price = validate_price(price, order_type)
    stop_price = validate_stop_price(stop_price, order_type)
    logger.info(
        "All inputs validated — symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
        symbol, side, order_type, quantity, price, stop_price,
    )
    return symbol, side, order_type, quantity, price, stop_price
