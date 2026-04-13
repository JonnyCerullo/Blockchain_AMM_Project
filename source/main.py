# Command-line interface implementation to control AMM simulation.

# aggiungo commento per testare git e CodeRabbit
from amm_uniswap import UniswapAMM
from amm_constant_sum import ConstantSumAMM
from trader import Trader
from run_simulation import Simulation
import sys, os
from dotenv import load_dotenv
import os

load_dotenv()

import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

def main():

    print("\n" + "="*60)
    print("          AMM SIMULATION - Choose AMM Type")
    print("="*60)
    print("1. Uniswap V2 (Constant Product: x × y = k)")
    print("2. Constant Sum (x + y = k)")
    print("3. Curve StableSwap")
    print("="*60)
    
    while True:
        choice = input("Choose AMM type (1 or 2 or 3): ").strip()
        if choice == "1":
            amm_type = "uniswap"
            print("\n✓ Using Uniswap V2 (Constant Product)")
            break
        elif choice == "2":
            amm_type = "constant_sum"
            print("\n✓ Using Constant Sum")
            break
        elif choice == "3":
            amm_type = "curve"  
            print("\n✓ Using Curve StableSwap")
            break
        else:
            print("Invalid choice, please enter 1 or 2 or 3")

    # Create simulation with AMM selected
    sim = Simulation(amm_type=amm_type)
    
    while True:
        print("\n" + "="*30)
        print("      AMM SIMULATION MENU")
        print(f"   Current AMM: {sim.amm_type.upper()}")
        print("="*30)
        print("1. Go forward 1 step")
        print("2. Go forward N steps")
        print("3. Apply market shock")
        print("4. Current status")
        print("5. Show graphs")
        print("6. Save results")
        print("7. See statistics")
        print("8. Whale dump")
        print("9. Whale pump")
        print("0. Exit")
        print("="*30)
        
        try:
            choice = input("Choice: ").strip()
            
            if choice == "1":
                sim.step(verbose = True)
                print("Step completed.")
                
            elif choice == "2":
                try:
                    n = int(input("How many steps? "))
                    if n <= 0:
                        print("Enter a positive number")
                        continue
                    # 1. Salva lo stato INIZIALE
                    start_price = sim.market_price
                    start_amm_price = sim.amm.get_price_x_to_y()
                    start_k = sim.amm.get_k()
                    start_reserves_x = sim.amm.x
                    start_reserves_y = sim.amm.y
                    start_step = sim.step_count
                    
                    print(f"\n⏳ Execution of {n} step...", end="", flush=True)
                
                    arb_count = 0
                    trader_swaps = 0
                    old_stdout = sys.stdout
                    sys.stdout = open(os.devnull, "w")
                    for i in range(n):
                        sim.step(False)
                    
                        if i % 10 == 0: print(".", end="", flush=True) 
            
                    
                    sys.stdout.close()
                    sys.stdout = old_stdout
                    end_price = sim.market_price
                    end_amm_price = sim.amm.get_price_x_to_y()
                    end_k = sim.amm.get_k()
                    
                    delta_price = ((end_price - start_price) / start_price) * 100
                    delta_amm_price = ((end_amm_price - start_amm_price) / start_amm_price) * 100
                    k_growth = end_k - start_k
                    
                    print("="*60)
                    print(f"📊 QUICK REPORT: STEP {start_step} → {sim.step_count} ({n} steps)")
                    print("="*60)
                    print("MARKET PRICE:")
                    print(f"  Start: {start_price:.2f} USDC")
                    print(f"  End:   {end_price:.2f} USDC")
                    print(f"  Change: {delta_price:+.2f}%")
                    print("-" * 30)
                    print(f"AMM PRICE ({sim.amm_type.upper()}):")
                    print(f"  Start: {start_amm_price:.2f} USDC")
                    print(f"  End:   {end_amm_price:.2f} USDC")
                    print(f"  Gap:   {abs(end_price - end_amm_price):.2f} USDC (vs market)")
                    print("-" * 30)
                    print("LIQUIDITY AND PROFIT (K):")
                    print(f"  Start: {start_k:,.2f}")
                    print(f"  End:   {end_k:,.2f}")
                    print(f"  Growth: {k_growth:,.2f} (Fees collected)")
                    print("-" * 30)
                    print("CURRENT RESERVES:")
                    print(f"  {sim.amm.x:.4f} ETH | {sim.amm.y:.2f} USDC")
                    print("="*60)

                except ValueError:
                    print("Please enter a valid number")
                    
            elif choice == "3":
                try:
                    shock_pct = float(input("Shock % (es. -30 o +25): "))
                    shock = shock_pct / 100
                    confirm = input(f"Do you confirm {shock_pct:+.1f}% shock? (y/n): ")
                    if confirm.lower() == 'y':
                        sim.apply_market_shock(shock)
                        print(f"{shock_pct:+.1f}% shock applied")
                except ValueError:
                    print("Invalid value")
                    
            elif choice == "4":
                sim.print_status()
                
            elif choice == "5":
                sim.plot()
                
            elif choice == "6":
                filename = input("File name (default: results.csv): ").strip()
                if not filename:
                    filename = "results.csv"
                sim.save_results(filename)
                print(f"Results saved in {filename}")
                
            elif choice == "7":
                sim.print_stats()

            elif choice == "8":
                try:
                    percent = float(input("Dump % of whale's ETH (0-100): ")) / 100
                    sim.whale_dump(percent)
                except ValueError:
                    print("Invalid value")

            elif choice == "9":
                try:
                    percent = float(input("Pump % of whale's USDC (0-100): ")) / 100
                    sim.whale_pump(percent)
                except ValueError:
                    print("Invalid value")

            elif choice == "0":
                confirm = input("Do you really want to exit? (y/n): ")
                if confirm.lower() == 'y':
                    print("Simulation finished")
                    break
                    
            else:
                print("Invalid option")
                
        except KeyboardInterrupt:
            print("\n\nInterruption detected")
            confirm = input("Do you want to save before exiting? (y/n): ")
            if confirm.lower() == 'y':
                sim.save_results("interrupted_results.csv")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            print("The simulation continues...")

if __name__ == "__main__":
    main()
