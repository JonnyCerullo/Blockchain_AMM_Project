# Blockchain_AMM_Project

## AMM Simulation: Stress-Testing Automated Market Makers

A comprehensive Python-based simulation framework for analyzing and comparing Automated Market Maker (AMM) protocols under chaotic market conditions.

## Project Overview

This project implements three fundamental AMM designs and subjects them to extreme stress tests including flash crashes, whale manipulation, and sustained high volatility. The goal is to understand the design trade-offs between different AMM architectures and validate their behavior under adverse conditions.

**Academic Context:** Project for AI course - Blockchain & Cryptocurrencies  
**Authors:** Alessandro Tricca, Jonathan Ted Benson Cerullo Uyi  
**Institution:** University of Bologna

---

## Architecture

### Implemented AMM Models

1. **Uniswap V2 (Constant Product)**
   - Formula: `x × y = k`
   - Best for: Volatile asset pairs (ETH/USDC)
   - Characteristics: Robust, infinite liquidity, high slippage on large trades

2. **Constant Sum**
   - Formula: `x + y = k`
   - Best for: Stablecoin pairs (USDC/USDT)
   - Characteristics: Ultra-low slippage, capital efficient, unstable for volatile pairs

3. **Curve StableSwap (Simplified)**
   - Formula: `k = (x·y)^α · (x+y)^(1-α)` where `α = A/(A+1)`
   - Best for: Stablecoin pairs
   - Characteristics: Hybrid approach, adaptive behavior

### Economic Agents

- **Trader**: Random retail trading behavior
- **SmartTrader**: Slippage-aware trading with rejection threshold
- **Arbitrageur**: Price stabilization through arbitrage opportunities
- **PanicLP**: Liquidity provider with volatility-based exit strategy
- **WhaleTrader**: Large-scale market manipulation capabilities

---

## Project Structure
```
.
├── amm_uniswap.py          # Constant Product AMM implementation
├── amm_constant_sum.py     # Constant Sum AMM implementation
├── amm_curve.py            # Curve StableSwap AMM implementation
├── trader.py               # Retail trader agents
├── agents.py               # Advanced agents (Arb, PanicLP, Whale)
├── run_simulation.py       # Core simulation engine
├── main.py                 # Interactive CLI interface
├── experiments.py          # Automated experiment runner
└── README.md               # This file
```

---

## Getting Started

### Prerequisites
```bash
Python 3.8+
numpy
pandas
matplotlib
seaborn
```

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/amm-simulation.git
cd amm-simulation

# Install dependencies
pip install numpy pandas matplotlib seaborn
```

### Quick Start

#### Interactive Mode
```bash
python main.py
```

Choose your AMM type (Uniswap/Constant Sum/Curve) and interact with the simulation through a menu:
- Execute single/multiple steps
- Trigger market shocks
- Perform whale dumps/pumps
- View real-time statistics
- Generate visualizations

#### Automated Experiments
```bash
python experiments.py
```

Runs complete experimental suite:
- 4 scenarios × 3 AMMs × 10 repetitions = 120 experiments
- Generates comparative analysis plots
- Outputs statistical summaries

---

## Experimental Scenarios

### 1. Baseline
- **Description:** Normal market conditions (±2% volatility per step)
- **Purpose:** Establish performance baseline
- **Steps:** 500

### 2. Flash Crash
- **Description:** Sudden -50% price drop at step 250
- **Purpose:** Test resilience to black swan events
- **Steps:** 500

### 3. Whale Manipulation
- **Description:** Coordinated pump-and-dump attack
  - Step 200: Dump 50% of whale's ETH
  - Step 400: Pump with 50% of whale's USDC
- **Purpose:** Evaluate resistance to market manipulation
- **Steps:** 600

### 4. High Volatility
- **Description:** Sustained extreme volatility (±10% per step)
- **Purpose:** Simulate prolonged market chaos
- **Steps:** 500

---

## Key Findings

### 1. No Universal "Best" AMM
- **Uniswap:** Optimal for volatile pairs (ETH/USDC, BTC/USDT)
- **Constant Sum:** ONLY suitable for stablecoins (USDC/USDT)
- **Curve:** Ideal for stablecoins, suboptimal for volatile pairs

### 2. Design Trade-offs Validated
- **Safety vs Efficiency:** Uniswap sacrifices capital efficiency for robustness
- **Restoring Force:** Essential for stability in volatile markets
- **Amplification:** Only beneficial when used in intended context (near-peg assets)

### 3. Constant Sum Instability Demonstrated
Our simulation proves Constant Sum is **catastrophically unstable** for volatile pairs:
- Price gaps exceed 5,000 USDC (265% deviation)
- Arbitrageurs lose $110k+ trying to correct
- Pool becomes essentially non-functional

This validates why real DeFi protocols evolved away from pure Constant Sum models.

### 4. Arbitrageur Behavior
- **Normal conditions:** Loses money (fees + impermanent loss)
- **High volatility:** Profits significantly (large spread opportunities)
- **Real-world implication:** Arbitrage bots need >1-2% spreads to be profitable

---

## Visualizations

The experiment runner generates:

1. **Comparative Analysis** (`comparative_analysis.png`)
   - Price gap comparison across scenarios
   - Arbitrageur profit distribution
   - LP panic frequency

2. **Performance Heatmap** (`performance_heatmap.png`)
   - Color-coded performance matrix
   - Scenario × AMM analysis

3. **Seed Variability** (`seed_variability.png`)
   - Individual run distributions
   - Statistical confidence intervals

---

## References

1. **Uniswap V2 Core:** [whitepaper](https://uniswap.org/whitepaper.pdf)
2. **Curve StableSwap:** Egorov, M. (2019). "StableSwap - efficient mechanism for Stablecoin liquidity"
3. **AMM Theory:** Bartoletti, M., et al. (2021). "A theory of Automated Market Makers in DeFi"
4. **DeFi Primer:** Mohan, V. (2022). "Automated market makers and decentralized exchanges"

---

## Disclaimers

### Educational Purpose
This project is for **educational and research purposes only**. It is not intended for production use or real trading.

### Simplified Implementations
- **Curve:** Uses pedagogical approximation, not production Newton-Raphson solver
- **Arbitrage:** Simplified strategy (doesn't account for gas fees, MEV, etc.)
- **Market Price:** Simulated via random walk (not real market data)

### Limitations
- No gas costs modeled
- Single pool per simulation (no cross-pool arbitrage)

---

## License

MIT License - See LICENSE file for details

---

## 👥 Authors

- **Alessandro Tricca** - alessandro.tricca@studio.unibo.it
- **Jonathan Ted Benson Cerullo Uyi** - jonathan.cerullouyi@studio.unibo.it

**Supervisor:** Prof. Stefano Ferretti  
**Institution:** University of Bologna - Master's in Artificial Intelligence  
**Course:** Blockchain & Cryptocurrencies  
**Academic Year:** 2025-2026
