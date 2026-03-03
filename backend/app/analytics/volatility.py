
import os
import math
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Adjust import based on project structure
import sys
from pathlib import Path

# Add project root directory to path to find data_loader and data
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
project_root = backend_dir.parent

if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from data_loader import DataLoader
except ImportError:
    try:
        from backend.data_loader import DataLoader # Fallback if run from outside
    except ImportError:
        # Fallback for weird path config
        sys.path.append(str(project_root))
        from data_loader import DataLoader

logger = logging.getLogger(__name__)

# Correct path relative to project root
CACHE_FILE = project_root / "data" / "price_history_cache.csv"

# ==========================================================
# Helper: Implied Spot Calculation
# ==========================================================

# ==========================================================
# Helper: Constant Maturity Interpolation
# ==========================================================

def interpolate_constant_maturity_iv(
    target_days: float,
    term_structure: List[Dict[str, Any]]
) -> float:
    """
    Calculate Constant Maturity IV using Variance Interpolation.
    Formula: sigma_target^2 * T_target = LinearInterp(sigma_1^2 * T_1, sigma_2^2 * T_2)
    
    term_structure should be sorted by days:
    [{"days": 15, "iv": 0.20}, {"days": 45, "iv": 0.22}, ...]
    """
    if not term_structure:
        return 0.0
        
    # Sort just in case
    curve = sorted(term_structure, key=lambda x: x['days'])
    
    # 1. Extrapolation: if target is outside range, use nearest
    if target_days <= curve[0]['days']:
        return curve[0]['iv']
    if target_days >= curve[-1]['days']:
        return curve[-1]['iv']
        
    # 2. Interpolation
    t_target = target_days / 365.0
    
    prev_point = curve[0]
    next_point = curve[-1]
    
    for i in range(len(curve) - 1):
        if curve[i]['days'] <= target_days <= curve[i+1]['days']:
            prev_point = curve[i]
            next_point = curve[i+1]
            break
            
    # Variance Interpolation
    t1 = prev_point['days'] / 365.0
    v1 = prev_point['iv']
    var1 = (v1 ** 2) * t1
    
    t2 = next_point['days'] / 365.0
    v2 = next_point['iv']
    var2 = (v2 ** 2) * t2
    
    # Linear weight on time
    # (t_target - t1) / (t2 - t1)
    if t2 == t1:
        return v1
        
    w = (t_target - t1) / (t2 - t1)
    
    var_target = var1 + w * (var2 - var1)
    iv_target = np.sqrt(var_target / t_target)
    
    return float(iv_target)

def _calculate_implied_spot(df: pd.DataFrame, r: float = 0.03) -> float:
    """
    Calculate Implied Spot Price using Put-Call Parity from option chain.
    S = K + (C - P) * e^(rT)  ->  S_implied = (C - P + K * e^(-rT)) * e^(rT) ?? 
    Actually: C - P = S - K * e^(-rT)
    => S = C - P + K * e^(-rT)
    """
    try:
        # Pre-process
        if 'strike' not in df.columns: return None
        
        # We need a slice with same expiry. Pick the one with most volume/OI?
        # Or just pick the nearest distinct expiry.
        if 'expiry_date' not in df.columns: return None
        
        expiries = df['expiry_date'].unique()
        # Filter for valid expiries (future)
        # Getting 'today' is hard from just DF unless we pass it. 
        # But we can assume the trade_date is consistent in the DF.
        if 'trade_date' in df.columns:
            current_date = pd.to_datetime(df['trade_date'].iloc[0])
        else:
             # Fallback: assume we process one day
             return None

        # Select the nearest monthly expiry (usually most liquid)
        # Find expiry with > 5 days and < 40 days
        valid_expiries = []
        for exp in expiries:
            exp_date = pd.to_datetime(exp)
            days = (exp_date - current_date).days
            if 5 < days < 50:
                valid_expiries.append((days, exp))
        
        if not valid_expiries:
            # Try any expiry > 0
            for exp in expiries:
                exp_date = pd.to_datetime(exp)
                days = (exp_date - current_date).days
                if days > 0:
                    valid_expiries.append((days, exp))
                    
        if not valid_expiries: 
            return None
            
        # Sort by days and pick first
        valid_expiries.sort()
        target_expiry = valid_expiries[0][1]
        T = valid_expiries[0][0] / 365.0
        
        sub_df = df[df['expiry_date'] == target_expiry]
        
        # Group by strike
        strikes = sub_df['strike'].unique()
        
        implied_prices = []
        
        for k in strikes:
            # Find Call and Put pair
            # Assuming 'type' column 'C'/'P' or similar
            # Logic similar to data.py but simplified
            
            # Filter rows
            rows = sub_df[sub_df['strike'] == k]
            call_row = None
            put_row = None
            
            for _, row in rows.iterrows():
                t = str(row.get('type', '')).upper()
                sym = str(row.get('symbol', ''))
                if t == 'C' or '购' in sym: call_row = row
                if t == 'P' or '沽' in sym: put_row = row
                
            if call_row is not None and put_row is not None:
                # Get close prices
                c = float(call_row.get('close', 0))
                p = float(put_row.get('close', 0))
                
                if c > 0 and p > 0:
                    # S = C - P + K * e^(-rT)
                    s_val = c - p + k * np.exp(-r * T)
                    implied_prices.append(s_val)
        
        if implied_prices:
            return np.median(implied_prices)
            
    except Exception as e:
        pass
        
    return None

def _get_median_strike_price(df: pd.DataFrame) -> float:
    if 'strike' in df.columns:
        strikes = df['strike'].dropna().unique()
        if len(strikes) > 0:
            return float(np.median(strikes))
    return 3.0 # Fallback

# ==========================================================
# Core Logic
# ==========================================================

from concurrent.futures import ThreadPoolExecutor, as_completed

def _process_single_date(loader: DataLoader, date_str: str) -> Optional[Dict]:
    """Helper to process a single date in a thread."""
    try:
        # Optimization: Read only necessary columns
        cols = ['underlying_close', 'strike', 'expiry_date', 'type', 'symbol', 'close', 'trade_date']
        
        # We access the internal path directly to avoid overhead if possible, 
        # or just use load_single_date but with columns arg if supported.
        # DataLoader.load_single_date doesn't support columns arg in the version I saw?
        # Checking DataLoader code... it DOES NOT support columns in load_single_date, 
        # but load_date_range DOES. 
        # Let's peek at the file directly using loader._date_to_path to be safe and fast.
        
        file_path = loader._date_to_path.get(date_str)
        if not file_path: return None
        
        df = pd.read_parquet(file_path, columns=cols)
        
        price = None
        source = "missing"
        
        # Try 1: Explicit Column
        if 'underlying_close' in df.columns:
            valid = df['underlying_close'].dropna()
            if not valid.empty and valid.iloc[0] > 0:
                price = float(valid.iloc[0])
                source = "direct"
        
        # Try 2: Implied Spot
        if price is None:
            price = _calculate_implied_spot(df)
            if price: source = "implied"
            
        # Try 3: Median Strike
        if price is None:
            price = _get_median_strike_price(df)
            source = "median_strike"
            
        if price is not None:
            return {
                "date": date_str,
                "close": price,
                "source": source
            }
    except Exception as e:
        # logger.error(f"Error processing {date_str}: {e}")
        pass
    return None

# Global Progress State (File Based for Reliability across processes)
import json
import time

PROGRESS_FILE = project_root / "data" / "progress.json"

def _update_progress(status: str, current: int, total: int, message: str):
    """Write progress to file to share across processes/threads"""
    try:
        data = {
            "status": status,
            "current": current,
            "total": total,
            "message": message,
            "timestamp": time.time()
        }
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Failed to write progress: {e}")

def get_progress():
    """Read progress from file"""
    try:
        if not PROGRESS_FILE.exists():
             return {"status": "idle", "total": 0, "current": 0, "message": ""}
             
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"status": "idle", "total": 0, "current": 0, "message": ""}

def get_price_history(dataset_id: str = "510050_SH", force_rebuild: bool = False) -> pd.DataFrame:
    """
    Get historical daily price series for the underlying asset.
    Uses caching and PARALLEL processing.
    """
    
    # 1. Check Cache
    if not force_rebuild and CACHE_FILE.exists():
        try:
            # Check modification time, if suspiciously old or small?
            # For now rely on existence.
            df = pd.read_csv(CACHE_FILE)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Reset progress just in case
            _update_progress("idle", 100, 100, "Done")
            
            return df
        except Exception:
            pass

    print(f"Building Price History Cache (Parallel). Looking in {project_root / 'data' / dataset_id}...")
    _update_progress("loading", 0, 0, "Initializing data loader...")
    
    try:
        # Use absolute path for DataLoader
        data_path = project_root / "data" / dataset_id
        
        # Check if dir exists first
        if not data_path.exists():
             _update_progress("error", 0, 0, f"Data directory not found: {data_path}")
             return pd.DataFrame()

        loader = DataLoader(str(data_path))
        print(f"DEBUG: Project Root: {project_root}")
        print(f"DEBUG: Data Path: {data_path}")
        print(f"DEBUG: DataLoader Path: {loader.data_dir}")
        
        dates = loader.get_available_dates()
        print(f"DEBUG: Dates Found: {len(dates)}")
        
        if not dates:
            print(f"No dates found in {data_path}")
            _update_progress("error", 0, 0, f"No data found in {data_path}")
            return pd.DataFrame()

        total_dates = len(dates)
        _update_progress("loading", 0, total_dates, "Scanning historical data...")
        
        records = []
        
        # Use ThreadPool to speed up IO
        # Reduce workers to avoid resource starvation
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_date = {executor.submit(_process_single_date, loader, d): d for d in dates}
            
            completed_count = 0
            for future in as_completed(future_to_date):
                try:
                    res = future.result()
                    if res:
                        records.append(res)
                except Exception as e:
                    print(f"Error processing date: {e}")
                
                completed_count += 1
                # Update Progress
                pct = int((completed_count / total_dates) * 100)
                if completed_count % 5 == 0 or completed_count == total_dates:
                     _update_progress("loading", completed_count, total_dates, f"Scanning historical data... {pct}%")
                
        history_df = pd.DataFrame(records)
        
        _update_progress("loading", total_dates, total_dates, "Finalizing data...")
        
        if not history_df.empty:
            history_df['date'] = pd.to_datetime(history_df['date'])
            history_df = history_df.sort_values('date')
        
        # Save cache
        try:
            history_df.to_csv(CACHE_FILE, index=False)
            print(f"Price history cached to {CACHE_FILE} ({len(history_df)} records)")
        except:
            pass
            
        _update_progress("done", total_dates, total_dates, "Done")
            
        return history_df
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        _update_progress("error", 0, 0, f"Error building history: {str(e)}")
        return pd.DataFrame()

def calculate_volatility_cone(
    current_date_str: str,
    dataset_id: str = "510050_SH", 
    lookback_years: int = 5
) -> Dict[str, Any]:
    """
    Calculate Volatility Cone statistics.
    
    Returns:
    {
        "cone_curves": [
            {"window": 30, "min": 0.1, "q25": 0.15, "median": 0.2, "q75": 0.25, "max": 0.4},
            ...
        ],
        "current_hv": 0.18  (Current 30-day HV for reference)
    }
    """
    # 1. Get History
    df = get_price_history(dataset_id)
    
    # 2. Filter up to current date
    current_date = pd.to_datetime(current_date_str)
    # Ensure we include history UP TO this date
    mask = df['date'] <= current_date
    df = df[mask].copy()
    
    if len(df) < 30:
        return {"error": "Not enough history"}
        
    # 3. Calculate Log Returns
    df['log_ret'] = np.log(df['close'] / df['close'].shift(1))
    
    # 4. Windows to analyze: every 5 days from 5 to 360
    windows = list(range(5, 365, 5))
    
    cone_curves = []
    
    # Annualization factor
    trading_days = 252
    
    for w in windows:
        if len(df) < w: continue
        
        # Calculate Rolling Realized Volatility (std dev of log returns * sqrt(252))
        vol_col = df['log_ret'].rolling(window=w).std() * np.sqrt(trading_days)
        
        # Drop NaNs
        valid_vols = vol_col.dropna()
        
        if valid_vols.empty: continue
        
        # Calculate Quantiles
        stats = {
            "window": w,
            "min": round(float(valid_vols.min()), 4),
            "q25": round(float(valid_vols.quantile(0.25)), 4),
            "median": round(float(valid_vols.median()), 4),
            "q75": round(float(valid_vols.quantile(0.75)), 4),
            "max": round(float(valid_vols.max()), 4),
            "current": round(float(valid_vols.iloc[-1]), 4) # The HV as of today
        }
        cone_curves.append(stats)
        
    return {
        "cone_curves": cone_curves,
        "latest_price": float(df['close'].iloc[-1]) if not df.empty else 0
    }
