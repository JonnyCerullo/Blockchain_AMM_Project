# Automated experiment runner for comparing AMM models under various scenarios.
# Uses MASTER_SEED for reproducibility and generates comparative analysis.

import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
import os
from run_simulation import Simulation

# Set visualization style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

class ExperimentRunner:
    """
    Orchestrates automated experiments across different AMM types and scenarios.
    
    Ensures reproducibility through MASTER_SEED and generates comparative reports.
    """
    
    def __init__(self, master_seed=42, output_dir=None):
        """Initialize experiment runner."""
        self.master_seed = master_seed
        if output_dir is None:
            # Usa la directory corrente se non è stata passata una cartella di output
            self.output_dir = os.getcwd()  # Directory corrente
        else:
            self.output_dir = output_dir
        self.results = []
        self.raw_results = []
        # Crea la directory di output se non esiste
        os.makedirs(self.output_dir, exist_ok=True)

    
    def set_seed(self, seed):
        """Set all random seeds for reproducibility"""
        random.seed(seed)
        np.random.seed(seed)

    def run_experiment_with_repetitions(self, num_runs=10):
        """Run complete experimental suite with multiple repetitions"""
        
        # PULISCI risultati precedenti
        self.results = []
        
        experiments = [
            ("baseline", self.run_baseline_experiment, {}),
            ("flash_crash", self.run_flash_crash_experiment, {"crash_magnitude": -0.5}),
            ("whale_manipulation", self.run_whale_manipulation_experiment, {}),
            ("high_volatility", self.run_high_volatility_experiment, {"volatility_multiplier": 5.0})
        ]
        
        total_runs = len(experiments) * 3 * num_runs  # 4 exp × 3 AMMs × num_runs
        current_run = 0
        
        for amm_type in ["uniswap", "constant_sum", "curve"]:
            for exp_name, exp_func, params in experiments:
                
                run_results = []
                
                for run_idx in range(num_runs):
                    current_run += 1
                    # Progress indicator
                    print(f"\r🔄 Progress: {current_run}/{total_runs} runs completed", end='', flush=True)
                    
                    seed_offset = run_idx * 1000 + hash(exp_name) % 1000
                    
                    # IMPORTANTE: non aggiungere a self.results qui
                    result = exp_func(amm_type, seed_offset=seed_offset, **params)
                    run_results.append(result)

                    result_copy = result.copy()
                    result_copy['run_id'] = run_idx
                    self.raw_results.append(result_copy)
                # Aggregate results
                aggregated = self.aggregate_results(run_results, exp_name, amm_type)
                self.results.append(aggregated)
        
        print("\n")  # New line dopo progress bar
        
        # Stampa riassunto finale
        self.print_final_summary()

    def run_baseline_experiment(self, amm_type, steps=500, seed_offset=0):
        """Run baseline experiment (COMPLETAMENTE SILENZIOSO)"""
        self.set_seed(self.master_seed + seed_offset)
                
        # DISABILITA tutti i print della simulazione
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()  # Redirect output to nowhere
        
        try:
            sim = Simulation(amm_type=amm_type)

            for i in range(steps):
                sim.step(verbose=False)
        finally:
            sys.stdout = old_stdout  # Restore output
        
        stats = sim.get_stats()
        
        result = {
            "experiment": "baseline",
            "amm_type": amm_type,
            "steps": steps,
            "seed": self.master_seed + seed_offset,
            **stats
        }
        
        # NON aggiungere a self.results qui
        return result

    def run_flash_crash_experiment(self, amm_type, crash_step=250, 
                                crash_magnitude=-0.5, total_steps=500, 
                                seed_offset=100):
        """Run flash crash experiment (COMPLETAMENTE SILENZIOSO)"""
        self.set_seed(self.master_seed + seed_offset)
        
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            sim = Simulation(amm_type=amm_type)
            for i in range(crash_step):
                sim.step(verbose=False)
            
            sim.apply_market_shock(crash_magnitude)
            
            for i in range(crash_step, total_steps):
                sim.step(verbose=False)
        finally:
            sys.stdout = old_stdout
        
        stats = sim.get_stats()
        
        result = {
            "experiment": "flash_crash",
            "amm_type": amm_type,
            "steps": total_steps,
            "crash_step": crash_step,
            "crash_magnitude": crash_magnitude,
            "seed": self.master_seed + seed_offset,
            **stats
        }
        
        return result

    def run_whale_manipulation_experiment(self, amm_type, dump_step=200, 
                                        pump_step=400, total_steps=600, 
                                        seed_offset=200):
        """Run whale manipulation experiment (COMPLETAMENTE SILENZIOSO)"""
        self.set_seed(self.master_seed + seed_offset)
        
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()  # Redirect output to nowhere
        
        try:
            sim = Simulation(amm_type=amm_type)
            for i in range(dump_step):
                sim.step(verbose=False)
            
            sim.whale_dump(percent=0.5)
            
            for i in range(dump_step, pump_step):
                sim.step(verbose=False)
            
            sim.whale_pump(percent=0.5)
            
            for i in range(pump_step, total_steps):
                sim.step(verbose=False)
        finally:
            sys.stdout = old_stdout
        
        stats = sim.get_stats()
        
        result = {
            "experiment": "whale_manipulation",
            "amm_type": amm_type,
            "steps": total_steps,
            "dump_step": dump_step,
            "pump_step": pump_step,
            "seed": self.master_seed + seed_offset,
            **stats
        }
        
        return result

    def run_high_volatility_experiment(self, amm_type, steps=500, 
                                    volatility_multiplier=5.0, 
                                    seed_offset=300):
        """Run high volatility experiment (COMPLETAMENTE SILENZIOSO)"""
        self.set_seed(self.master_seed + seed_offset)
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            sim = Simulation(amm_type=amm_type)
            original_step = sim.step

        finally:
            sys.stdout = old_stdout
        
        
        
        def high_volatility_step(verbose=False):
            sim.step_count += 1
            
            base_vol = 0.02
            change_pct = random.uniform(-base_vol * volatility_multiplier, 
                                    base_vol * volatility_multiplier)
            sim.market_price *= (1 + change_pct)
            volatility = abs(change_pct)
            
            sim.arb.act(sim.amm, sim.market_price)
            
            for t in sim.traders:
                t.act(sim.amm, strategy="random", verbose=False)
            
            sim.lp.check_stress(sim.amm, volatility)
            
            sim.price_log.append({
                "step": sim.step_count,
                "amm_price": sim.amm.get_price_x_to_y(),
                "market_price": sim.market_price,
                "price_gap": abs(sim.amm.get_price_x_to_y() - sim.market_price),
                "reserves_x": sim.amm.x,
                "reserves_y": sim.amm.y,
                "k": sim.amm.get_k(),
                "volatility": volatility
            })
        
        sim.step = high_volatility_step
        
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            for i in range(steps):
                sim.step(verbose=False)
        finally:
            sys.stdout = old_stdout
        
        stats = sim.get_stats()
        
        result = {
            "experiment": "high_volatility",
            "amm_type": amm_type,
            "steps": steps,
            "volatility_multiplier": volatility_multiplier,
            "seed": self.master_seed + seed_offset,
            **stats
        }
        
        return result

    def aggregate_results(self, run_results, exp_name, amm_type):
        """Aggrega i risultati di più run"""
        if not run_results:
            return {}
        
        numeric_metrics = [
            'avg_price_gap', 'price_stability', 'k_growth_percent',
            'arb_profit', 'lp_panic_events'
        ]
        
        aggregated = {
            'experiment': exp_name,
            'amm_type': amm_type,
            'num_runs': len(run_results)
        }
        
        for metric in numeric_metrics:
            values = [r[metric] for r in run_results if metric in r]
            if values:
                aggregated[f'{metric}_mean'] = np.mean(values)
                aggregated[f'{metric}_std'] = np.std(values)
        
        return aggregated
        
    def print_final_summary(self):
        """Stampa riassunto finale compatto di tutti gli esperimenti"""
        print(f"\n{'#'*70}")
        print(f"{'FINAL SUMMARY':^70}")
        print(f"{'#'*70}\n")
        
        df = pd.DataFrame(self.results)
        
        for amm_type in ["uniswap", "constant_sum", "curve"]:
            print(f"\n{'='*70}")
            print(f"{amm_type.upper()} AMM - All Experiments")
            print(f"{'='*70}")
            
            amm_data = df[df['amm_type'] == amm_type]
            
            for _, row in amm_data.iterrows():
                exp_name = row['experiment'].replace('_', ' ').title()
                print(f"\n  📊 {exp_name}")
                print(f"     Price Gap:     {row['avg_price_gap_mean']:7.4f} ± {row['avg_price_gap_std']:.4f} USDC")
                print(f"     Arb Profit:    {row['arb_profit_mean']:7.2f} ± {row['arb_profit_std']:.2f} USDC")
                print(f"     Stability:     {row['price_stability_mean']:7.4f}")
                print(f"     LP Panics:     {row['lp_panic_events_mean']:7.1f}")
        
        print(f"\n{'='*70}\n")

    def print_experiment_summary(self, experiment_type, amm_type, results):
        """Stampa un riassunto per ogni esperimento"""
        print(f"\n{'='*60}")
        print(f"{experiment_type.upper()} SUMMARY FOR {amm_type.upper()}")
        print(f"{'='*60}")
        print(f"Number of runs: {len(results)}")
        print(f"Mean Price Gap: {results['avg_price_gap_mean']:.4f} ± {results['avg_price_gap_std']:.4f}")
        print(f"Mean Arbitrage Profit: {results['arb_profit_mean']:.4f} ± {results['arb_profit_std']:.4f}")
        print(f"Price Stability: {results['price_stability_mean']:.4f}")
        print(f"LP Panic Events: {results['lp_panic_events_mean']:.4f}")
        print(f"{'='*60}\n")
    
    def run_all_experiments(self):
        """Run complete experimental suite for both AMM types"""
        print(f"\n{'#'*60}")
        print(f"RUNNING FULL EXPERIMENTAL SUITE")
        print(f"{'#'*60}\n")
        
        experiments = [
            ("baseline", {}),
            ("flash_crash", {"crash_magnitude": -0.5}),
            ("whale_manipulation", {}),
            ("high_volatility", {"volatility_multiplier": 5.0})
        ]
        
        for amm_type in ["uniswap", "constant_sum", "curve"]:
            print(f"\n{'*'*60}")
            print(f"TESTING {amm_type.upper()} AMM")
            print(f"{'*'*60}")
            
            for exp_name, params in experiments:
                if exp_name == "baseline":
                    self.run_baseline_experiment(amm_type, **params)
                elif exp_name == "flash_crash":
                    self.run_flash_crash_experiment(amm_type, **params)
                elif exp_name == "whale_manipulation":
                    self.run_whale_manipulation_experiment(amm_type, **params)
                elif exp_name == "high_volatility":
                    self.run_high_volatility_experiment(amm_type, **params)
        
        print(f"\n{'#'*60}")
        print(f"ALL EXPERIMENTS COMPLETED")
        print(f"Total experiments run: {len(self.results)}")
        print(f"{'#'*60}\n")
    
    
    def plot_comparative_analysis(self):
        """Generate comparative visualizations with error bars"""
        if not self.results:
            print("No results to plot. Run experiments first!")
            return
        plt.close('all')
        df = pd.DataFrame(self.results)
        
        # CHIUDI figure esistenti
        plt.close('all')
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('AMM Comparative Analysis (mean ± std across runs)', 
                    fontsize=16, fontweight='bold')
        
        # 1. Average Price Gap
        ax1 = axes[0, 0]
        pivot_mean = df.pivot(index='experiment', columns='amm_type', 
                            values='avg_price_gap_mean')
        pivot_std = df.pivot(index='experiment', columns='amm_type', 
                            values='avg_price_gap_std')
        
        pivot_mean.plot(kind='bar', ax=ax1, color=['#3498db', '#e74c3c', '#2ecc71'], 
                        yerr=pivot_std, capsize=4, error_kw={'linewidth': 2})
        
        ax1.set_title('Average Price Gap (Log Scale)', fontweight='bold')
        ax1.set_ylabel('USDC (Log Scale)')
        ax1.set_yscale('log')  # <--- QUESTA È LA RIGA MAGICA
        ax1.set_xlabel('')
        ax1.legend(title='AMM Type')
        ax1.grid(axis='y', alpha=0.3, which="both") 
        
        # 2. Price Stability
        ax2 = axes[0, 1]
        pivot_mean = df.pivot(index='experiment', columns='amm_type', 
                            values='price_stability_mean')
        pivot_std = df.pivot(index='experiment', columns='amm_type', 
                            values='price_stability_std')
        pivot_mean.plot(kind='bar', ax=ax2, color=['#3498db', '#e74c3c', '#2ecc71'], 
                        yerr=pivot_std, capsize=4, error_kw={'linewidth': 2})
        ax2.set_title('Price Stability (lower = better)', fontweight='bold')
        ax2.set_ylabel('Std Dev')
        ax2.set_xlabel('')
        ax2.legend(title='AMM Type')
        ax2.grid(axis='y', alpha=0.3)
        
        # 3. Arbitrageur Profit
        ax3 = axes[1, 0]
        pivot_mean = df.pivot(index='experiment', columns='amm_type', 
                            values='arb_profit_mean')
        pivot_std = df.pivot(index='experiment', columns='amm_type', 
                            values='arb_profit_std')
        pivot_mean.plot(kind='bar', ax=ax3, color=['#3498db', '#e74c3c', '#2ecc71'], 
                        yerr=pivot_std, capsize=4, error_kw={'linewidth': 2})
        ax3.set_title('Arbitrageur Profit', fontweight='bold')
        ax3.set_ylabel('USDC')
        ax3.set_xlabel('')
        ax3.legend(title='AMM Type')
        ax3.grid(axis='y', alpha=0.3)
        ax3.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        
        # 4. LP Panic Events
        ax4 = axes[1, 1]
        pivot_mean = df.pivot(index='experiment', columns='amm_type', 
                            values='lp_panic_events_mean')
        pivot_std = df.pivot(index='experiment', columns='amm_type', 
                            values='lp_panic_events_std')
        pivot_mean.plot(kind='bar', ax=ax4, color=['#3498db', '#e74c3c', '#2ecc71'], 
                        yerr=pivot_std, capsize=4, error_kw={'linewidth': 2})
        ax4.set_title('LP Panic Events', fontweight='bold')
        ax4.set_ylabel('Count')
        ax4.set_xlabel('')
        ax4.legend(title='AMM Type')
        ax4.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot - RIMUOVI file esistente prima
        # Alla fine, ELIMINA file vecchio prima di salvare
        plot_path = os.path.join(self.output_dir, "comparative_analysis.png")
        if os.path.exists(plot_path):
            os.remove(plot_path)
        
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close('all')  # Chiudi di nuovo

    def plot_heatmap_analysis(self):
        """Generate heatmap showing performance across dimensions"""
        if not self.results:
            print("No results to plot. Run experiments first!")
            return
        plt.close('all')
        df = pd.DataFrame(self.results)
        
        plt.close('all')
        
        # Select key metrics (use MEAN values)
        metrics = [
            'avg_price_gap_mean', 
            'price_stability_mean', 
            'arb_profit_mean',
            'lp_panic_events_mean'
        ]
        
        metric_labels = [
            'Avg Price Gap',
            'Price Stability',
            'Arb Profit',
            'LP Panics'
        ]
        
        # Create pivot table for each metric
        fig, axes = plt.subplots(1, len(metrics), figsize=(20, 4))
        fig.suptitle('Performance Heatmaps: Uniswap vs Constant Sum (mean values)', 
                    fontsize=14, fontweight='bold')
        
        for idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
            pivot = df.pivot(index='experiment', columns='amm_type', values=metric)
            
            # Choose colormap based on metric
            if 'profit' in metric.lower():
                cmap = 'RdYlGn'
            else:
                cmap = 'RdYlGn_r'
            
            sns.heatmap(pivot, annot=True, fmt='.2f', cmap=cmap, 
                    ax=axes[idx], cbar_kws={'label': label},
                    center=0 if 'profit' in metric.lower() else None)
            axes[idx].set_title(label, fontweight='bold')
            axes[idx].set_xlabel('')
            axes[idx].set_ylabel('')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.output_dir, "performance_heatmap.png")
        if os.path.exists(plot_path):
            os.remove(plot_path)
        
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close('all')  # Chiudi di nuovo

    def plot_seed_distribution(self):
        """Genera grafico dettagliato che mostra ogni singolo seed (Boxplot + Strip)"""
        if not self.raw_results:
            print("Nessun dato grezzo trovato.")
            return
            
        import seaborn as sns
        import matplotlib.pyplot as plt
        
        df_raw = pd.DataFrame(self.raw_results)
        df_raw['experiment'] = df_raw['experiment'].str.replace('_', ' ').str.title()
        
        plt.close('all')
        fig, axes = plt.subplots(1, 2, figsize=(18, 8))
        fig.suptitle('Seed Variability Analysis: Individual Run Performance', 
                    fontsize=16, fontweight='bold')
        
        # Metriche da analizzare
        metrics = [
            ('avg_price_gap', 'Price Gap Distribution (USDC)', 0),
            ('arb_profit', 'Arbitrageur Profit Distribution (USDC)', 1)
        ]
        
        colors = {'uniswap': '#3498db', 'constant_sum': '#e74c3c', 'curve': '#2ecc71'}
        
        for col_name, title, idx in metrics:
            ax = axes[idx]
            
            # 1. Boxplot (mostra la distribuzione generale)
            sns.boxplot(data=df_raw, x='experiment', y=col_name, hue='amm_type',
                        ax=ax, palette=colors, showfliers=False, 
                        boxprops={'alpha': 0.4}) # Trasparente per vedere i punti sotto
            
            # 2. Stripplot (i PUNTINI veri e propri)
            sns.stripplot(data=df_raw, x='experiment', y=col_name, hue='amm_type',
                        ax=ax, palette=colors, dodge=True, jitter=True, 
                        alpha=0.8, s=6, edgecolor='black', linewidth=0.5)
            
            ax.set_title(title, fontweight='bold')
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.grid(axis='y', alpha=0.3)
            
            # Sistema la legenda (ne crea due per colpa del doppio plot, ne teniamo una)
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles[:3], labels[:3], title='AMM Type')
            
            if 'profit' in col_name:
                ax.axhline(0, color='black', linestyle='--', alpha=0.5)

        plt.tight_layout()
        plot_path = os.path.join(self.output_dir, "seed_variability.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
def main():
    """Run complete experimental suite with repetitions"""
    
    # Initialize experiment runner
    runner = ExperimentRunner(master_seed=42, output_dir="experiments_output")
    
    # Ask user for number of repetitions
    print("\n" + "="*60)
    print("How many runs per experiment?")
    print("  • 1 = Quick test")
    print("  • 10 = Good balance (recommended)")
    print("  • 30 = High confidence")
    print("="*60)
    
    try:
        num_runs = int(input("Number of runs (default 10): ").strip() or "10")
        if num_runs < 1:
            num_runs = 10
    except ValueError:
        num_runs = 10
    
    print(f"\n🔄 Running {num_runs} repetitions per experiment...")
    print("Please wait...\n")
    
    # Run all experiments SILENZIOSAMENTE
    runner.run_experiment_with_repetitions(num_runs=num_runs)

    # Generate all visualizations
    print("\n📊 Generating visualizations...")
    runner.plot_comparative_analysis()
    runner.plot_heatmap_analysis()
    runner.plot_seed_distribution()
    
    print(f"\n{'='*60}")
    print(f"✅ EXPERIMENTS COMPLETED")
    print(f"{'='*60}")
    print(f"Check '{runner.output_dir}' directory for results")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()