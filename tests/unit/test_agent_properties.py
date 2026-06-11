import pytest
from hypothesis import given, strategies as st
from app.agent import calculate_final_total, validate_coupon_code

@given(
    item_id=st.sampled_from(["item-101", "item-102", "item-103"]),
    quantity=st.integers(min_value=1, max_value=100),
    discount_rate=st.floats(min_value=0.0, max_value=1.5)  # Includes values > 1.0 to stress test the invariant
)
def test_calculate_final_total_properties(item_id, quantity, discount_rate):
    result = calculate_final_total(item_id, quantity, discount_rate)
    
    assert result["status"] == "SUCCESS"
    
    # Invariant Property 1: The final total must never be negative
    # (This will fail for discount_rate > 1.0, showing PBT catching a boundary bug!)
    assert result["final_total"] >= 0, f"Violated: final_total is negative ({result['final_total']}) for discount_rate={discount_rate}"
    
    # Invariant Property 2: Final total is always less than or equal to subtotal
    assert result["final_total"] <= result["subtotal"]


@given(
    code=st.text(min_size=1, max_size=20)
)
def test_validate_coupon_code_properties(code):
    result = validate_coupon_code(code)
    
    assert result["status"] == "SUCCESS"
    
    # Invariant Property 3: Any valid promo coupon must respect business limits (0.0 <= rate <= 1.0)
    if result.get("valid", False):
        rate = result["discount_rate"]
        assert 0.0 <= rate <= 1.0, f"Violated: coupon {code} is valid but has out-of-bounds discount rate {rate}"
