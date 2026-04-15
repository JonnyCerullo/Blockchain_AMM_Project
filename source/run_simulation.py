# Simulation engine for AMM behavior analysis under chaotic market conditions.
# Coordinates interactions between AMM, traders, arbitrageurs, and liquidity providers.

import random
from amm_uniswap import UniswapAMM
from amm_constant_sum import ConstantSumAMM
from trader import Trader, SmartTrader
from agents import Arbitrageur, PanicLP, WhaleTrader
import matplotlib.pyplot as plt
import pandas as pd
from amm_curve import CurveStableSwapAMM

class Simulation:
    """
    Main simulation class that orchestrates AMM testing scenarios.
    
    Attributes:
        amm: The Automated Market Maker instance
        market_price: External market price (simulated)
        step_count: Current simulation step
        traders: List of retail traders
        arb: Arbitrageur agent
        lp: Panic liquidity provider
        price_log: Historical data log
    """
    
    def __init__(self, amm_type="uniswap"):
        """Initialize simulation with default parameters.
        
        Args:
            amm_type: Type of AMM to use ("uniswap" or "constant_sum" OR "curve")
        """

        # Initialize AMM based on type, with 100 ETH and 200,000 USDC (price = 2000 USDC/ETH)
        # Total pool value: $400,000
        if amm_type == "uniswap":
            self.amm = UniswapAMM(token_x="ETH", token_y="USDC", 
                                  reserve_x=100, reserve_y=200000)
        elif amm_type == "constant_sum":
             # WARNING: This will trigger instability warning
            # This is INTENTIONAL to demonstrate CS is unsuitable for volatile pairs
            self.amm = ConstantSumAMM(token_x="ETH", token_y="USDC", 
                                      reserve_x=100, reserve_y=200000)
        elif amm_type == "curve":
             self.amm = CurveStableSwapAMM(token_x="ETH", token_y="USDC", 
                                  reserve_x=100, reserve_y=200000,
                                  amplification=100)
        else:
            raise ValueError(f"Unknown AMM type: {amm_type}. Use 'uniswap' or 'constant_sum'")
        
        self.amm_type = amm_type  # <-- Salva il tipo per riferimento
        
        # External market price (independent from AMM)
        self.market_price = 2000
        
        # Simulation step counter
        self.step_count = 0
        
        # Retail traders with random behavior (~2-3% of pool each)
        self.traders = [
            Trader("Alice", eth_amount=5, usdc_amount=1000),     # ~$11k tot (2.75%)
            Trader("Bob", eth_amount=2, usdc_amount=3000),       # ~$7k tot (1.75%)
            SmartTrader("Charlie", eth_amount=10, usdc_amount=10000, max_slippage=0.02)  # ~$30k tot (7.5%)
        ]
        
        # Arbitrageur with substantial capital to close price gaps (~100% of pool)
        # Needs large capital because it must be able to close any gap
        self.arb = Arbitrageur("ArbBot", capital_x=1500, capital_y=2500000)  # ~$4000k (100%)
        
        # Whale trader for manual pump/dump operations (~20% of pool)
        self.whale = WhaleTrader("Moby", capital_x=20, capital_y=40000)  # ~$80k (20%)
        
        # Liquidity provider that panics under high volatility (owns 50% of pool)
        self.lp = PanicLP("PanicLP", 0.5, self.amm)
        
        # Data logging for analysis
        self.price_log = []

    def print_status(self):
        """Display current state of the simulation."""
        print(f"\n{'='*60}")
        print(f"SIMULATION STATUS - Step {self.step_count}")
        print(f"{'='*60}")
        print(f"Market price: {self.market_price:.2f} USDC/ETH")
        print(f"AMM price:    {self.amm.get_price_x_to_y():.2f} USDC/ETH")
        print(f"Price gap:    {abs(self.amm.get_price_x_to_y() - self.market_price):.2f} USDC "
              f"({abs(self.amm.get_price_x_to_y() - self.market_price) / self.market_price * 100:.2f}%)")
        
        print(f"\nPool Reserves:")
        print(f"   • {self.amm.x:.2f} ETH")
        print(f"   • {self.amm.y:.2f} USDC")
        print(f"   • k = {self.amm.get_k():.2f}")
        print(f"   • LP tokens supply: {self.amm.total_supply:.2f}")
        
        print(f"\n👥 Traders:")
        for t in self.traders:
            portfolio_value = t.get_portfolio_value(self.market_price)
            print(f"   • {t.name}: {t.wallet['ETH']:.4f} ETH | "
                  f"{t.wallet['USDC']:.2f} USDC (≈ ${portfolio_value:.2f})")
        
        print(f"\nArbitrageur:")
        print(f"   • {self.arb.name}: {self.arb.capital_x:.4f} ETH | {self.arb.capital_y:.2f} USDC")
        print(f"   • Trades executed: {self.arb.trades_executed}")
        if hasattr(self.arb, 'get_profit'):
            print(f"   • Profit: ${self.arb.get_profit(self.market_price):.2f}")
        
        print(f"\nLiquidity Provider:")
        print(f"   • {self.lp.name}: {self.lp.lp_tokens:.2f} LP tokens")
        print(f"   • Has exited: {self.lp.has_exited}")
        print(f"   • Panic events: {self.lp.panic_events}")
        print(f"{'='*60}\n")

    def apply_market_shock(self, percent):
            """
            Apply an external market shock.
            """
            old_price = self.market_price
            self.market_price *= (1 + percent)
            
            print(f"\n{'⚡'*5}")
            print(f"⚡ MARKET SHOCK APPLIED!")
            print(f"⚡ Price: {old_price:.2f} → {self.market_price:.2f} USDC/ETH ({percent:+.1%})")
            print(f"{'⚡'*5}\n")
            
            # Calcola la volatilità come valore assoluto dello shock
            shock_volatility = abs(percent)
            
            # Forza l'LP a controllare lo stress con questa nuova volatilità enorme
            print("⚠️ Triggering LP stress check due to shock...")
            self.lp.check_stress(self.amm, shock_volatility, verbose=True)
            # ------------------------------
            """
            Trigger whale dump event (whale sells ETH).
            
            Args:
                percent: Percentage of whale's ETH to dump (0-1, e.g., 0.5 = 50%)
            """
            print(f"\n{'🐋'*5}")
            print(f"🐋 WHALE DUMP EVENT!")
            print(f"🐋 Whale selling {percent:.0%} of ETH holdings")
            print(f"{'🐋'*5}\n")
            
            self.whale.dump(self.amm, percent=percent)

    def whale_dump(self, percent=0.5):
        """
        Trigger whale dump event (whale sells ETH).
        
        Args:
            percent: Percentage of whale's ETH to dump (0-1, e.g., 0.5 = 50%)
        """
        print(f"\n{'🐋'*30}")
        print(f"🐋 WHALE DUMP EVENT!")
        print(f"🐋 Whale selling {percent:.0%} of ETH holdings")
        print(f"{'🐋'*30}\n")
        
        self.whale.dump(self.amm, percent=percent)
    
    def whale_pump(self, percent=0.5):
        """
        Trigger whale pump event (whale buys ETH).
        
        Args:
            percent: Percentage of whale's USDC to use for buying (0-1)
        """
        print(f"\n{'🐋'*5}")
        print(f"🐋 WHALE PUMP EVENT!")
        print(f"🐋 Whale buying ETH with {percent:.0%} of USDC")
        print(f"{'🐋'*5}\n")
        
        self.whale.pump(self.amm, percent=percent)

    def step(self, verbose):
        """
        Advance simulation by one time step.
        
        Args:
            verbose: If True, print detailed logs
        """
        self.step_count += 1
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"TICK {self.step_count}")
            print(f"{'='*60}")

        # Simulate random market volatility (±2%)
        change_pct = random.uniform(-0.02, 0.02)
        self.market_price *= (1 + change_pct)
        volatility = abs(change_pct)
        
        if verbose:
            print(f"Market movement: {change_pct:+.2%} → New price: {self.market_price:.2f} USDC/ETH")

        # Arbitrageur attempts to close price gaps
        self.arb.act(self.amm, self.market_price, verbose=verbose)

        # Retail traders execute random trades
        for t in self.traders:
            t.act(self.amm, strategy="random", verbose=verbose)

        # LP monitors volatility and may exit in panic
        self.lp.check_stress(self.amm, volatility)

        # Log data for analysis
        self.price_log.append({
            "step": self.step_count,
            "amm_price": self.amm.get_price_x_to_y(),
            "market_price": self.market_price,
            "price_gap": abs(self.amm.get_price_x_to_y() - self.market_price),
            "reserves_x": self.amm.x,
            "reserves_y": self.amm.y,
            "k": self.amm.get_k(),
            "volatility": volatility
        })
        
        if verbose:
            print(f"{'='*60}")

    def plot(self):
        """Generate visualization plots of simulation results."""
        if not self.price_log:
            print("No data to plot. Execute at least one step!")
            return
        
        df = pd.DataFrame(self.price_log)
        
        # Create 2x2 subplot layout
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'AMM Simulation Results - {self.step_count} steps', 
                     fontsize=16, fontweight='bold')
        
        # Plot 1: Price Evolution (AMM vs Market)
        axes[0, 0].plot(df['step'], df['amm_price'], 
                       label='AMM Price', linewidth=2, color='blue')
        axes[0, 0].plot(df['step'], df['market_price'], 
                       label='Market Price', linewidth=2, alpha=0.7, color='orange')
        axes[0, 0].set_xlabel('Step', fontsize=11)
        axes[0, 0].set_ylabel('Price (USDC/ETH)', fontsize=11)
        axes[0, 0].set_title('Price Evolution', fontsize=12, fontweight='bold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Price Gap (Arbitrage Opportunity)
        axes[0, 1].plot(df['step'], df['price_gap'], color='red', linewidth=2)
        axes[0, 1].set_xlabel('Step', fontsize=11)
        axes[0, 1].set_ylabel('Price Gap (USDC)', fontsize=11)
        axes[0, 1].set_title('AMM-Market Price Gap', fontsize=12, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].fill_between(df['step'], df['price_gap'], alpha=0.3, color='red')
        
        # Add average gap annotation
        avg_gap = df['price_gap'].mean()
        axes[0, 1].axhline(y=avg_gap, color='darkred', linestyle='--', 
                          label=f'Avg: {avg_gap:.2f}')
        axes[0, 1].legend()
        
        # Plot 3: Pool Reserves (Dual Y-axis)
        ax3 = axes[1, 0]
        color_eth = 'tab:blue'
        ax3.plot(df['step'], df['reserves_x'], 
                label='ETH Reserve', linewidth=2, color=color_eth)
        ax3.set_xlabel('Step', fontsize=11)
        ax3.set_ylabel('ETH Reserve', color=color_eth, fontsize=11)
        ax3.tick_params(axis='y', labelcolor=color_eth)
        ax3.set_title('Pool Reserves', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Secondary Y-axis for USDC
        ax3_twin = ax3.twinx()
        color_usdc = 'tab:orange'
        ax3_twin.plot(df['step'], df['reserves_y'], 
                     label='USDC Reserve', linewidth=2, color=color_usdc)
        ax3_twin.set_ylabel('USDC Reserve', color=color_usdc, fontsize=11)
        ax3_twin.tick_params(axis='y', labelcolor=color_usdc)
        
        # Plot 4: Constant Product k (Fee Accumulation)
        axes[1, 1].plot(df['step'], df['k'], color='green', linewidth=2)
        axes[1, 1].set_xlabel('Step', fontsize=11)
        axes[1, 1].set_ylabel('k = x * y', fontsize=11)
        axes[1, 1].set_title('Constant Product (should increase with fees)', 
                           fontsize=12, fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3)
        
        # Calculate and display k growth
        k_initial = df['k'].iloc[0]
        k_final = df['k'].iloc[-1]
        k_growth = ((k_final / k_initial) - 1) * 100
        
        axes[1, 1].text(0.02, 0.98, 
                       f'k growth: {k_growth:.3f}%\nInitial: {k_initial:,.0f}\nFinal: {k_final:,.0f}', 
                       transform=axes[1, 1].transAxes, 
                       verticalalignment='top',
                       fontsize=10,
                       bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
        
        plt.tight_layout()
        plt.show()
        
        print("Plots generated successfully!")

    def save_results(self, filename="simulation_results.csv"):
        """
        Save simulation results to CSV file.
        
        Args:
            filename: Output CSV filename
        """
        if not self.price_log:
            print("No data to save. Execute at least one step!")
            return
        
        df = pd.DataFrame(self.price_log)
        df.to_csv(filename, index=False)
        
        print(f"Results saved to: {filename}")
        print(f"Rows saved: {len(df)}")
        print(f"Columns: {', '.join(df.columns)}")

    def get_stats(self):
        """
        Calculate and return summary statistics of the simulation.
        
        Returns:
            dict: Dictionary containing key metrics
        """
        if not self.price_log:
            print("No data available. Execute at least one step!")
            return {}
        
        df = pd.DataFrame(self.price_log)
        
        stats = {
            "total_steps": self.step_count,
            "avg_price_gap": df['price_gap'].mean(),
            "max_price_gap": df['price_gap'].max(),
            "min_price_gap": df['price_gap'].min(),
            "avg_volatility": df['volatility'].mean(),
            "max_volatility": df['volatility'].max(),
            "price_stability": df['amm_price'].std(),  # Lower = more stable
            "initial_k": df['k'].iloc[0],
            "final_k": df['k'].iloc[-1],
            "k_growth_percent": ((df['k'].iloc[-1] / df['k'].iloc[0]) - 1) * 100,
            "total_swaps": self.amm.swap_count,
            "arb_trades": self.arb.trades_executed,
            "arb_profit": self.arb.get_profit(self.market_price) if hasattr(self.arb, 'get_profit') else 0,
            "lp_exited": self.lp.has_exited,
            "lp_panic_events": self.lp.panic_events
        }
        
        return stats

    def print_stats(self):
        """Print summary statistics in a formatted table."""
        stats = self.get_stats()
        
        if not stats:
            return
        
        print(f"\n{'='*60}")
        print("SIMULATION STATISTICS")
        print(f"{'='*60}")
        
        # Simulation info
        print("\nSimulation Info:")
        print(f"   Total steps: {stats['total_steps']}")
        print(f"   Total swaps: {stats['total_swaps']}")
        
        # Price metrics
        print("\nPrice Metrics:")
        print(f"   Avg price gap: {stats['avg_price_gap']:.2f} USDC")
        print(f"   Max price gap: {stats['max_price_gap']:.2f} USDC")
        print(f"   Min price gap: {stats['min_price_gap']:.2f} USDC")
        print(f"   Price stability (std dev): {stats['price_stability']:.2f}")
        
        # Volatility metrics
        print("\nVolatility Metrics:")
        print(f"   Avg volatility: {stats['avg_volatility']:.2%}")
        print(f"   Max volatility: {stats['max_volatility']:.2%}")
        
        # Pool metrics
        print("\nPool Metrics:")
        print(f"   Initial k: {stats['initial_k']:,.2f}")
        print(f"   Final k: {stats['final_k']:,.2f}")
        print(f"   k growth: {stats['k_growth_percent']:.3f}%")
        
        # Agent metrics
        print("\nAgent Metrics:")
        print(f"   Arbitrageur trades: {stats['arb_trades']}")
        print(f"   Arbitrageur profit: ${stats['arb_profit']:.2f}")
        print(f"   LP exited: {stats['lp_exited']}")
        print(f"   LP panic events: {stats['lp_panic_events']}")
        
        print(f"{'='*60}\n")