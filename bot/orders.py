"""Order placement logic — routes, validates, and dispatches orders."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from binance.exceptions import BinanceAPIException, BinanceRequestException

from bot.client import BinanceFuturesClient
from bot.validators import ValidationError, validate_all

logger = logging.getLogger(__name__)


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class OrderResult:
    """Structured representation of an order placement attempt."""

    success: bool
    order_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    # Convenience properties so callers never have to touch raw dict keys

    @property
    def order_id(self) -> Optional[int]:
        return self.order_data.get("orderId")

    @property
    def status(self) -> Optional[str]:
        return self.order_data.get("status")

    @property
    def executed_qty(self) -> Optional[str]:
        return self.order_data.get("executedQty")

    @property
    def avg_price(self) -> Optional[str]:
        return self.order_data.get("avgPrice")

    @property
    def symbol(self) -> Optional[str]:
        return self.order_data.get("symbol")

    @property
    def side(self) -> Optional[str]:
        return self.order_data.get("side")

    @property
    def order_type(self) -> Optional[str]:
        return self.order_data.get("type")

    @property
    def orig_qty(self) -> Optional[str]:
        return self.order_data.get("origQty")

    @property
    def price(self) -> Optional[str]:
        return self.order_data.get("price")

    @property
    def stop_price(self) -> Optional[str]:
        return self.order_data.get("stopPrice")


# ── Order manager ─────────────────────────────────────────────────────────────

class OrderManager:
    """Handles all order placement logic for Binance USDT-M Futures Testnet."""

    def __init__(self, client: BinanceFuturesClient) -> None:
        self.client = client

    # ── Public dispatch entry-point ───────────────────────────────────────────

    def dispatch(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> OrderResult:
        """Route to the correct placement method based on *order_type*."""
        order_type = order_type.upper()
        dispatch_map = {
            "MARKET": self._place_market,
            "LIMIT": self._place_limit,
            "STOP": self._place_stop_limit,
        }
        handler = dispatch_map.get(order_type)
        if handler is None:
            return OrderResult(success=False, error=f"Unknown order type: {order_type}")
        return handler(symbol, side, quantity, price=price, stop_price=stop_price)

    # ── Internal handlers ─────────────────────────────────────────────────────

    def _place_market(
        self,
        symbol: str,
        side: str,
        quantity: float,
        **_: Any,
    ) -> OrderResult:
        """Place a MARKET order."""
        logger.info("Placing MARKET order — symbol=%s side=%s qty=%s", symbol, side, quantity)
        try:
            symbol, side, _, quantity, _, _ = validate_all(
                symbol=symbol, side=side, order_type="MARKET", quantity=quantity
            )
            response = self.client.create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity,
            )
            logger.info("MARKET order placed — orderId=%s", response.get("orderId"))
            return OrderResult(success=True, order_data=response)

        except ValidationError as exc:
            logger.warning("Validation error (MARKET): %s", exc)
            return OrderResult(success=False, error=str(exc))
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("API error (MARKET): %s", exc)
            return OrderResult(success=False, error=str(exc))
        except Exception as exc:
            logger.error("Unexpected error (MARKET): %s", exc, exc_info=True)
            return OrderResult(success=False, error=str(exc))

    def _place_limit(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        **_: Any,
    ) -> OrderResult:
        """Place a LIMIT order."""
        logger.info(
            "Placing LIMIT order — symbol=%s side=%s qty=%s price=%s tif=%s",
            symbol, side, quantity, price, time_in_force,
        )
        try:
            symbol, side, _, quantity, price, _ = validate_all(
                symbol=symbol, side=side, order_type="LIMIT",
                quantity=quantity, price=price,
            )
            response = self.client.create_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                quantity=quantity,
                price=price,
                timeInForce=time_in_force,
            )
            logger.info("LIMIT order placed — orderId=%s", response.get("orderId"))
            return OrderResult(success=True, order_data=response)

        except ValidationError as exc:
            logger.warning("Validation error (LIMIT): %s", exc)
            return OrderResult(success=False, error=str(exc))
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("API error (LIMIT): %s", exc)
            return OrderResult(success=False, error=str(exc))
        except Exception as exc:
            logger.error("Unexpected error (LIMIT): %s", exc, exc_info=True)
            return OrderResult(success=False, error=str(exc))

    def _place_stop_limit(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
        **_: Any,
    ) -> OrderResult:
        """Place a STOP (Stop-Limit) order — bonus order type."""
        logger.info(
            "Placing STOP-LIMIT order — symbol=%s side=%s qty=%s price=%s stop=%s tif=%s",
            symbol, side, quantity, price, stop_price, time_in_force,
        )
        try:
            symbol, side, _, quantity, price, stop_price = validate_all(
                symbol=symbol, side=side, order_type="STOP",
                quantity=quantity, price=price, stop_price=stop_price,
            )
            response = self.client.create_order(
                symbol=symbol,
                side=side,
                type="STOP",
                quantity=quantity,
                price=price,
                stopPrice=stop_price,
                timeInForce=time_in_force,
            )
            logger.info("STOP-LIMIT order placed — orderId=%s", response.get("orderId"))
            return OrderResult(success=True, order_data=response)

        except ValidationError as exc:
            logger.warning("Validation error (STOP-LIMIT): %s", exc)
            return OrderResult(success=False, error=str(exc))
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("API error (STOP-LIMIT): %s", exc)
            return OrderResult(success=False, error=str(exc))
        except Exception as exc:
            logger.error("Unexpected error (STOP-LIMIT): %s", exc, exc_info=True)
            return OrderResult(success=False, error=str(exc))
