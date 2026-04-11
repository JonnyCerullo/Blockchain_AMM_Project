# Constant Sum Market Maker: x + y = k
# Simpler than Uniswap but UNSTABLE under stress (could run out of tokens)
# Designed for equal-value tokens only

import math

class ConstantSumAMM:

    """
    Constant Sum Automated Market Maker (x + y = k)
    
    ⚠️  IMPORTANT: This model is designed for EQUAL-VALUE tokens (stablecoins).
    
    Characteristics:
    - Swap rate: ~1:1 (minus fees)
    - Best for: USDC/USDT, DAI/USDC pairs
    - NOT suitable for: ETH/USDC, BTC/USDT (volatile pairs)
    
    ⚠️  Expected behavior with volatile pairs (ETH/USDC):
    - Extreme price divergence (gaps up to 1000%+)
    - Pool depletion of one asset
    - Arbitrageur losses
    - Very high slippage (99%+)
    
    This is INTENTIONAL to demonstrate AMM design trade-offs.
    For volatile pairs, use Constant Product (Uniswap) instead.
    
    Reference: Basic AMM model, used as comparison baseline
    """

    def __init__(self, token_x, token_y, reserve_x, reserve_y, fee=0.003):
        """
        Initializes a Constant Sum AMM (x + y = k).
        
        Args:
            token_x: Name of token X (e.g. "USDC")
            token_y: Name of token Y (e.g. "USDT")
            reserve_x: Initial reserve of X
            reserve_y: Initial reserve of Y
            fee: Swap fee (default 0.3%)
        """
        if reserve_x <= 0 or reserve_y <= 0:
            raise ValueError("Initial reserves must be positive")
        if not 0 <= fee < 1:
            raise ValueError("Fee must be between 0 and 1")
            
        self.token_x = token_x
        self.token_y = token_y
        self.x = float(reserve_x)
        self.y = float(reserve_y)
        self.fee = fee
        
        # KEY DIFFERENCE: k = x + y (not x * y)
        self.k = reserve_x + reserve_y
        
        # LP tokens = (x + y) / 2 (arithmetic mean instead of geometric)
        self.total_supply = (reserve_x + reserve_y) / 2
        
        # Tracking for metrics
        self.total_fee_x = 0.0
        self.total_fee_y = 0.0
        self.swap_count = 0
        self.k_history = [self.get_k()]

        # ⚠️  WARNING: Check if initialization is appropriate
        ratio = reserve_y / reserve_x
        if ratio < 0.9 or ratio > 1.1:
            print(f"\n{'⚠️ '*20}")
            print(f"⚠️  WARNING: Constant Sum AMM initialized with non-equal reserves!")
            print(f"⚠️  Token ratio: {ratio:.4f} (optimal is ~1.0 for stablecoins)")
            print(f"⚠️  ")
            print(f"⚠️  This configuration will cause EXTREME INSTABILITY:")
            print(f"⚠️  - Price divergence from market (100%+ gaps)")
            print(f"⚠️  - Pool depletion of one asset")
            print(f"⚠️  - Arbitrageur losses")
            print(f"⚠️  ")
            print(f"⚠️  This is EXPECTED for demonstration purposes.")
            print(f"⚠️  Use Uniswap (Constant Product) for volatile pairs.")
            print(f"{'⚠️ '*20}\n")

    def get_k(self):
        """Returns the constant sum k"""
        return self.x + self.y

    def get_price_x_to_y(self):
        """
        Price of X in terms of Y.
        
        """

        return self.y / self.x

    def get_price_y_to_x(self):
        """Price of Y in terms of X"""
        if self.y <= 0:
            raise ValueError("Reserve Y is zero or negative")
        return self.x / self.y

    def add_liquidity(self, amount_x, amount_y):
        """
        Adds liquidity to the pool.
        Returns the number of LP tokens minted.
        """
        if amount_x <= 0 or amount_y <= 0:
            raise ValueError("Amounts must be positive")
        
        if self.total_supply == 0:
            # First liquidity: mint (x + y) / 2
            liquidity = (amount_x + amount_y) / 2
            if liquidity <= 0:
                raise ValueError("Initial liquidity too low")
        else:
            # In Constant Sum, la liquidità è proporzionale alla somma
            liquidity = min(
                amount_x * self.total_supply / self.x,
                amount_y * self.total_supply / self.y
            )
            
            # Warn if ratios don't match
            ratio_x = amount_x / self.x
            ratio_y = amount_y / self.y
            if abs(ratio_x - ratio_y) > 0.01:  # 1% tolerance
                print(f"[AMM-CS] Warning: Non-optimal ratio! "
                      f"Ratio X: {ratio_x:.4f}, Ratio Y: {ratio_y:.4f}")
        
        self.x += amount_x
        self.y += amount_y
        self.k = self.x + self.y  # Aggiorna k
        self.total_supply += liquidity
        self.k_history.append(self.get_k())
        
        return liquidity

    def remove_liquidity(self, liquidity):
        """
        Removes liquidity by burning LP tokens.
        Returns (amount_x, amount_y).
        """
        if liquidity <= 0:
            raise ValueError("Liquidity to remove must be positive")
        if liquidity > self.total_supply:
            raise ValueError(f"Insufficient liquidity: {liquidity} > {self.total_supply}")
        if self.total_supply == 0:
            return 0, 0
        
        # Calculate proportional shares
        amount_x = (liquidity * self.x) / self.total_supply
        amount_y = (liquidity * self.y) / self.total_supply
        
        # Verify we're not completely emptying the pool
        if amount_x >= self.x or amount_y >= self.y:
            raise ValueError("Cannot remove all liquidity")
        
        self.x -= amount_x
        self.y -= amount_y
        self.k = self.x + self.y  # Aggiorna k
        self.total_supply -= liquidity
        self.k_history.append(self.get_k())
        
        return amount_x, amount_y

    def calculate_swap_output(self, amount_in, reserve_in, reserve_out, fee=None):
        """
        Calculates swap output for Constant Sum AMM with fee accumulation.
        
        📐 MATHEMATICAL MODEL:
        ----------------------
        Pure Constant Sum (no fees):
            x + y = k  (constant)
            Swap: dx = dy (perfect 1:1)
        
        With fees (current implementation):
            User pays:     amount_in
            Pool receives: amount_in  (ALL enters the pool)
            User receives: amount_out = amount_in * (1 - fee)
            
            Result: k GROWS over time!
            k_new = (x + amount_in) + (y - amount_out)
                = x + y + amount_in * fee
                = k_old + fee_captured
        
        ⚠️ WARNING: This violates the "Constant" Sum property!
        The invariant k increases with each swap due to fee accumulation.
        This is standard for AMMs (fees benefit LPs), but NOT a pure Constant Sum.
        
        Args:
            amount_in: Input token amount
            reserve_in: Current reserve of input token
            reserve_out: Current reserve of output token
            fee: Swap fee (default: self.fee)
        
        Returns:
            amount_out: Output token amount (after fee deduction)
        """
        if fee is None:
            fee = self.fee
            
        if amount_in <= 0:
            raise ValueError("Input amount must be positive")
        if reserve_in <= 0 or reserve_out <= 0:
            raise ValueError("Reserves must be positive")
        
        # Calculate 1:1 swap output with fee deducted
        amount_out = amount_in * (1 - fee)
        
        # SAFETY CHECK: Prevent pool drainage
        # Leave at least 5% of reserves (more conservative than before)
        max_allowed = reserve_out * 0.95
        
        if amount_out >= max_allowed:
            raise ValueError(
                f"Swap too large: would drain the pool!\n"
                f"  Requested output: {amount_out:.4f} {self.token_y if reserve_out == self.y else self.token_x}\n"
                f"  Available (safe): {max_allowed:.4f}\n"
                f"  Try a smaller swap amount."
            )
        
        return amount_out

    def swap_x_for_y_with_fee(self, dx, fee=None, verbose=True):
        """
        Swaps X for Y.
        Returns the amount of Y received.
        """
        if fee is None:
            fee = self.fee
            
        price_before = self.get_price_x_to_y()
        k_before = self.get_k()
        
        # Calculate output (quasi 1:1 in Constant Sum)
        dy = self.calculate_swap_output(dx, self.x, self.y, fee)
        
        # Update reserves
        self.x += dx
        self.y -= dy
        self.k = self.x + self.y  # Aggiorna k
        
        # Fee remains in the pool
        fee_amount = dx * fee
        self.total_fee_x += fee_amount
        
        price_after = self.get_price_x_to_y()
        effective_price = dy / dx
        
        # Slippage
        slippage = abs(effective_price - price_before) / price_before
        
        # Price impact
        price_impact = abs(price_after - price_before) / price_before
        
        self.swap_count += 1
        self.k_history.append(self.get_k())
        
        if verbose:
            print(f"[SWAP-CS #{self.swap_count}] {dx:.4f} {self.token_x} → {dy:.2f} {self.token_y}")
            print(f" - Price before: {price_before:.2f} → after: {price_after:.2f} {self.token_y}/{self.token_x}")
            print(f" - Effective price: {effective_price:.2f} {self.token_y}/{self.token_x}")
            print(f" - Slippage: {slippage:.2%} | Price impact: {price_impact:.2%}")
            print(f" - Fee collected: {fee_amount:.4f} {self.token_x}")
            print(f" - Reserves: {self.x:.2f} {self.token_x}, {self.y:.2f} {self.token_y}")
            print(f" - k: {k_before:.2f} → {self.get_k():.2f} (Δ: {self.get_k() - k_before:.2f})")
        
        return dy

    def swap_y_for_x_with_fee(self, dy, fee=None, verbose=True):
        """
        Swaps Y for X.
        Returns the amount of X received.
        """
        if fee is None:
            fee = self.fee
            
        price_before = self.get_price_x_to_y()
        k_before = self.get_k()
        
        # Calculate output
        dx = self.calculate_swap_output(dy, self.y, self.x, fee)
        
        # Update reserves
        self.y += dy
        self.x -= dx
        self.k = self.x + self.y  # Aggiorna k
        
        # Fee remains in the pool
        fee_amount = dy * fee
        self.total_fee_y += fee_amount
        
        price_after = self.get_price_x_to_y()
        effective_price = dy / dx
        
        slippage = abs(effective_price - price_before) / price_before
        price_impact = abs(price_after - price_before) / price_before
        
        self.swap_count += 1
        self.k_history.append(self.get_k())
        
        if verbose:
            print(f"[SWAP-CS #{self.swap_count}] {dy:.2f} {self.token_y} → {dx:.4f} {self.token_x}")
            print(f"  • Price before: {price_before:.4f} → after: {price_after:.4f} {self.token_x}/{self.token_y}")
            print(f"  • Effective price: {effective_price:.4f} {self.token_x}/{self.token_y}")
            print(f"  • Slippage: {slippage:.2%} | Price impact: {price_impact:.2%}")
            print(f"  • Fee collected: {fee_amount:.2f} {self.token_y}")
            print(f"  • Reserves: {self.x:.2f} {self.token_x}, {self.y:.2f} {self.token_y}")
            print(f"  • k: {k_before:.2f} → {self.get_k():.2f} (Δ: {self.get_k() - k_before:.2f})")
        
        return dx

    def get_stats(self):
        """Returns pool statistics"""
        return {
            "reserves_x": self.x,
            "reserves_y": self.y,
            "price_x_to_y": self.get_price_x_to_y(),
            "price_y_to_x": self.get_price_y_to_x(),
            "total_supply": self.total_supply,
            "k": self.get_k(),
            "total_fee_x": self.total_fee_x,
            "total_fee_y": self.total_fee_y,
            "swap_count": self.swap_count,
            "fee_percentage": self.fee * 100
        }

    def __repr__(self):
        return (f"ConstantSumAMM({self.token_x}/{self.token_y}: "
                f"x={self.x:.2f}, y={self.y:.2f}, "
                f"price={self.get_price_x_to_y():.2f}, "
                f"k={self.get_k():.2f})")


# TEST RAPIDO (opzionale, per verificare che funzioni)
if __name__ == "__main__":
    print("Testing Constant Sum AMM...\n")
    
    # Crea pool con 100 ETH e 200,000 USDC
    amm = ConstantSumAMM("ETH", "USDC", 100, 200000)
    print(f"Initial state: {amm}")
    print(f"k = {amm.get_k()}")
    
    # Test swap: compra 1 ETH con USDC
    print("\n" + "="*60)
    print("Test: Swap 2000 USDC for ETH")
    print("="*60)
    eth_received = amm.swap_y_for_x_with_fee(2000)
    print(f"\nReceived: {eth_received:.4f} ETH")
    print(f"New state: {amm}")
    
    # Test swap: vendi 1 ETH per USDC
    print("\n" + "="*60)
    print("Test: Swap 1 ETH for USDC")
    print("="*60)
    usdc_received = amm.swap_x_for_y_with_fee(1)
    print(f"\nReceived: {usdc_received:.2f} USDC")
    print(f"New state: {amm}")
    
    # Mostra statistiche
    print("\n" + "="*60)
    print("Final Statistics")
    print("="*60)
    stats = amm.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")