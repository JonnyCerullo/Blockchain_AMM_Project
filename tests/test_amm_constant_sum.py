"""
Tests for ConstantSumAMM.calculate_swap_output

Covers the changes introduced in the PR:
- Threshold changed from reserve_out * 0.95 to reserve_out (exact boundary)
- Error message changed to "Swap too large: would empty the pool"
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'source'))

from amm_constant_sum import ConstantSumAMM


@pytest.fixture
def amm():
    """Standard pool: 1000 USDC / 1000 USDT, fee=0.003 (0.3%)"""
    return ConstantSumAMM("USDC", "USDT", 1000.0, 1000.0, fee=0.003)


@pytest.fixture
def amm_zero_fee():
    """Pool with zero fee for 1:1 ratio tests"""
    return ConstantSumAMM("USDC", "USDT", 1000.0, 1000.0, fee=0.0)


# ---------------------------------------------------------------------------
# Formula correctness
# ---------------------------------------------------------------------------

class TestCalculateSwapOutputFormula:

    def test_standard_swap_applies_fee(self, amm):
        """amount_out = amount_in * (1 - fee)"""
        amount_in = 100.0
        expected = amount_in * (1 - amm.fee)
        result = amm.calculate_swap_output(amount_in, amm.x, amm.y)
        assert result == pytest.approx(expected)

    def test_zero_fee_gives_one_to_one(self, amm_zero_fee):
        """With fee=0, output equals input (1:1 swap)"""
        amount_in = 50.0
        result = amm_zero_fee.calculate_swap_output(amount_in, amm_zero_fee.x, amm_zero_fee.y)
        assert result == pytest.approx(50.0)

    def test_custom_fee_override(self, amm):
        """Explicit fee parameter overrides self.fee"""
        amount_in = 100.0
        custom_fee = 0.01
        expected = amount_in * (1 - custom_fee)
        result = amm.calculate_swap_output(amount_in, amm.x, amm.y, fee=custom_fee)
        assert result == pytest.approx(expected)

    def test_default_fee_none_uses_self_fee(self, amm):
        """fee=None falls back to self.fee"""
        amount_in = 200.0
        result_default = amm.calculate_swap_output(amount_in, amm.x, amm.y, fee=None)
        result_explicit = amm.calculate_swap_output(amount_in, amm.x, amm.y, fee=amm.fee)
        assert result_default == pytest.approx(result_explicit)

    def test_output_is_always_less_than_input_with_positive_fee(self, amm):
        """With a positive fee, output must be strictly less than input"""
        result = amm.calculate_swap_output(10.0, amm.x, amm.y)
        assert result < 10.0

    def test_reserves_do_not_affect_output_amount(self, amm):
        """Constant Sum formula ignores reserve ratio; only amount_in and fee matter"""
        result_small_reserves = amm.calculate_swap_output(10.0, 50.0, 500.0)
        result_large_reserves = amm.calculate_swap_output(10.0, 50000.0, 500000.0)
        assert result_small_reserves == pytest.approx(result_large_reserves)


# ---------------------------------------------------------------------------
# Boundary: new threshold (reserve_out) vs old threshold (reserve_out * 0.95)
# ---------------------------------------------------------------------------

class TestCalculateSwapOutputBoundary:

    def test_amount_out_exactly_at_reserve_out_raises(self, amm_zero_fee):
        """amount_out == reserve_out must raise (new >= boundary)"""
        # With fee=0, amount_out == amount_in; set amount_in == reserve_out
        reserve_out = amm_zero_fee.y  # 1000.0
        with pytest.raises(ValueError, match="Swap too large: would empty the pool"):
            amm_zero_fee.calculate_swap_output(reserve_out, amm_zero_fee.x, reserve_out)

    def test_amount_out_above_reserve_out_raises(self, amm_zero_fee):
        """amount_out > reserve_out must raise"""
        reserve_out = amm_zero_fee.y  # 1000.0
        with pytest.raises(ValueError, match="Swap too large: would empty the pool"):
            amm_zero_fee.calculate_swap_output(reserve_out + 1.0, amm_zero_fee.x, reserve_out)

    def test_amount_out_just_below_reserve_out_succeeds(self, amm_zero_fee):
        """amount_out just below reserve_out must succeed (no longer blocked)"""
        reserve_out = amm_zero_fee.y  # 1000.0
        amount_in = reserve_out - 0.001  # fee=0 → amount_out = amount_in
        result = amm_zero_fee.calculate_swap_output(amount_in, amm_zero_fee.x, reserve_out)
        assert result == pytest.approx(amount_in)

    def test_old_095_threshold_no_longer_blocks(self, amm_zero_fee):
        """
        Regression: old code raised at amount_out >= reserve_out * 0.95.
        New code only raises at amount_out >= reserve_out.
        Swaps between 95% and 100% of reserve_out must now succeed.
        """
        reserve_out = amm_zero_fee.y  # 1000.0
        # 96% of reserve_out — previously blocked, now allowed
        amount_in = reserve_out * 0.96
        result = amm_zero_fee.calculate_swap_output(amount_in, amm_zero_fee.x, reserve_out)
        assert result == pytest.approx(amount_in)

    def test_exactly_95_percent_of_reserve_out_now_allowed(self, amm_zero_fee):
        """
        Regression: amount_out == reserve_out * 0.95 was the old hard limit.
        Under new rules it must succeed.
        """
        reserve_out = amm_zero_fee.y  # 1000.0
        amount_in = reserve_out * 0.95  # fee=0 → amount_out == amount_in
        result = amm_zero_fee.calculate_swap_output(amount_in, amm_zero_fee.x, reserve_out)
        assert result == pytest.approx(amount_in)

    def test_error_message_exact_wording(self, amm_zero_fee):
        """Error message must be exactly 'Swap too large: would empty the pool'"""
        reserve_out = amm_zero_fee.y
        with pytest.raises(ValueError) as exc_info:
            amm_zero_fee.calculate_swap_output(reserve_out + 1.0, amm_zero_fee.x, reserve_out)
        assert str(exc_info.value) == "Swap too large: would empty the pool"

    def test_large_swap_with_fee_still_blocked_when_output_exceeds_reserves(self, amm):
        """With fee > 0, a swap that reduces output below reserve_out*1 but still exceeds reserve_out raises"""
        # fee=0.003, reserve_out=1000
        # amount_out = amount_in * 0.997 >= 1000  →  amount_in >= 1003.009...
        reserve_out = amm.y  # 1000.0
        amount_in = 1004.0  # 1004 * 0.997 = 1000.988 > 1000
        with pytest.raises(ValueError, match="Swap too large: would empty the pool"):
            amm.calculate_swap_output(amount_in, amm.x, reserve_out)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestCalculateSwapOutputValidation:

    def test_zero_amount_in_raises(self, amm):
        with pytest.raises(ValueError, match="Input amount must be positive"):
            amm.calculate_swap_output(0.0, amm.x, amm.y)

    def test_negative_amount_in_raises(self, amm):
        with pytest.raises(ValueError, match="Input amount must be positive"):
            amm.calculate_swap_output(-10.0, amm.x, amm.y)

    def test_zero_reserve_in_raises(self, amm):
        with pytest.raises(ValueError, match="Reserves must be positive"):
            amm.calculate_swap_output(10.0, 0.0, amm.y)

    def test_negative_reserve_in_raises(self, amm):
        with pytest.raises(ValueError, match="Reserves must be positive"):
            amm.calculate_swap_output(10.0, -100.0, amm.y)

    def test_zero_reserve_out_raises(self, amm):
        with pytest.raises(ValueError, match="Reserves must be positive"):
            amm.calculate_swap_output(10.0, amm.x, 0.0)

    def test_negative_reserve_out_raises(self, amm):
        with pytest.raises(ValueError, match="Reserves must be positive"):
            amm.calculate_swap_output(10.0, amm.x, -500.0)

    def test_small_positive_amount_in_succeeds(self, amm):
        """Smallest meaningful positive amount should work"""
        result = amm.calculate_swap_output(0.0001, amm.x, amm.y)
        assert result == pytest.approx(0.0001 * (1 - amm.fee))