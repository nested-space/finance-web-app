"""Money value object.

A ``Money`` wraps a non-negative ``Decimal`` with pence precision. It is the
single arithmetic type for amounts in the domain; the persistence layer converts
to and from integer pence at its boundary (``pence`` / ``from_pence``) so the
database never stores a float. See ``docs/ARCHITECTURE.md`` -> "Domain value
objects" and ``docs/OPERATIONS.md`` -> "Data layout".
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

_PENCE = Decimal("0.01")


@dataclass(frozen=True)
class Money:
    """A non-negative monetary amount, normalised to two decimal places."""

    amount: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("Money.amount must be a Decimal")
        if not self.amount.is_finite():
            raise ValueError("Money must be a finite amount")
        if self.amount < 0:
            raise ValueError("Money cannot be negative")
        normalised = self.amount.quantize(_PENCE)
        if normalised != self.amount:
            raise ValueError("Money supports at most two decimal places")
        # Store the canonical two-dp form (e.g. "1.5" -> "1.50").
        object.__setattr__(self, "amount", normalised)

    @classmethod
    def from_form_string(cls, raw: str) -> Money:
        """Parse a form field into ``Money``, rejecting malformed or negative input."""
        text = raw.strip()
        if not text:
            raise ValueError("amount is required")
        try:
            value = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"not a valid amount: {raw!r}") from exc
        return cls(value)

    @classmethod
    def from_pence(cls, pence: int) -> Money:
        """Reconstruct ``Money`` from integer minor units (the stored form)."""
        if pence < 0:
            raise ValueError("pence cannot be negative")
        return cls(Decimal(pence) / 100)

    def pence(self) -> int:
        """Return the amount as integer minor units for persistence."""
        return int((self.amount * 100).to_integral_value())

    def __str__(self) -> str:
        return f"{self.amount:.2f}"
