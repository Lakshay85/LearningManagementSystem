from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

MIN_AMOUNT_PAISE = 100  # Razorpay minimum is Rs 1


def effective_price(course) -> Decimal:
    """Price a student pays, in rupees. Free courses return 0."""
    if course.isFree or course.price is None:
        return Decimal("0")
    price = Decimal(str(course.price))
    discount = course.discountPrice
    if discount is not None:
        discount = Decimal(str(discount))
        if Decimal("0") <= discount < price:
            return discount
    return price


def is_paid_course(course) -> bool:
    return effective_price(course) > 0


def amount_in_paise(course) -> int:
    return int((effective_price(course) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
