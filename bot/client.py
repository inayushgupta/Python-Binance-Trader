"""Binance Futures Testnet API client — direct REST implementation."""

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://testnet.binancefuture.com"


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"APIError(code={code}): {message}")


class BinanceFuturesClient:
    """
    Direct REST client for Binance USDT-M Futures Testnet.
    Uses requests + HMAC-SHA256 signing — no third-party SDK dependency.
    """

    def __init__(self, api_key: str, api_secret: str) -> None:
        if not api_key or not api_secret:
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must not be empty.")
        self._api_key = api_key.strip()
        self._api_secret = api_secret.strip()
        self._session = requests.Session()
        self._session.headers.update({
            "X-MBX-APIKEY": self._api_key,
            "Content-Type": "application/json",
        })
        logger.info("BinanceFuturesClient ready [url=%s]", BASE_URL)

    # ── Signing ───────────────────────────────────────────────────────────────

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add timestamp and HMAC-SHA256 signature to params dict."""
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        sig = hmac.new(
            self._api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = sig
        return params

    def _get(self, path: str, params: Optional[Dict] = None, signed: bool = True) -> Any:
        p = dict(params or {})
        if signed:
            p = self._sign(p)
        url = BASE_URL + path
        logger.debug("GET %s params=%s", url, {k: v for k, v in p.items() if k != "signature"})
        resp = self._session.get(url, params=p, timeout=10)
        return self._handle(resp)

    def _post(self, path: str, params: Dict[str, Any]) -> Any:
        p = self._sign(dict(params))
        url = BASE_URL + path
        logger.debug("POST %s params=%s", url, {k: v for k, v in p.items() if k != "signature"})
        resp = self._session.post(url, params=p, timeout=10)
        return self._handle(resp)

    def _delete(self, path: str, params: Dict[str, Any]) -> Any:
        p = self._sign(dict(params))
        url = BASE_URL + path
        resp = self._session.delete(url, params=p, timeout=10)
        return self._handle(resp)

    @staticmethod
    def _handle(resp: requests.Response) -> Any:
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            return {}
        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))
        return data

    # ── Orders ────────────────────────────────────────────────────────────────

    def create_order(self, **params: Any) -> Dict[str, Any]:
        """Place a futures order. All kwargs are forwarded as POST params."""
        log_params = {k: v for k, v in params.items()}
        logger.info("API REQUEST  → POST /fapi/v1/order | params=%s", log_params)
        response = self._post("/fapi/v1/order", params)
        logger.info(
            "API RESPONSE ← orderId=%s  status=%s  executedQty=%s  avgPrice=%s",
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
            response.get("avgPrice"),
        )
        logger.debug("Full response payload: %s", response)
        return response

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open futures order by order ID."""
        logger.info("Cancelling order — symbol=%s orderId=%s", symbol, order_id)
        response = self._delete("/fapi/v1/order", {"symbol": symbol, "orderId": order_id})
        logger.info("Order cancelled — orderId=%s status=%s", order_id, response.get("status"))
        return response

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all open futures orders, optionally filtered by symbol."""
        params = {"symbol": symbol} if symbol else {}
        return self._get("/fapi/v1/openOrders", params)

    # ── Account ───────────────────────────────────────────────────────────────

    def get_account_info(self) -> Dict[str, Any]:
        """Return full futures account information including balances."""
        logger.debug("Fetching futures account info")
        response = self._get("/fapi/v2/account", {})
        logger.debug(
            "Account info fetched — totalWalletBalance=%s",
            response.get("totalWalletBalance"),
        )
        return response

    # ── Market data ───────────────────────────────────────────────────────────

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return exchange info for a specific symbol, or None if not found."""
        logger.debug("Fetching symbol info — symbol=%s", symbol)
        info = self._get("/fapi/v1/exchangeInfo", signed=False)
        for sym in info.get("symbols", []):
            if sym["symbol"] == symbol.upper():
                return sym
        logger.warning("Symbol not found on exchange: %s", symbol)
        return None
