from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime

from ..analytics.volatility import calculate_volatility_cone, get_price_history
from ..api.data import _load_date_data, _calculate_implied_spot, _calculate_iv_bisection

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/vol-cone")
async def get_volatility_cone(
    date: str = Query(..., description="Date YYYY-MM-DD"),
    symbol: str = Query("510050_SH")
):
    """
    Get Volatility Cone data and current ATM IV Term Structure.
    """
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        
        # 1. Get History & Cone Stats (Run in ThreadPool to avoid blocking event loop)
        cone_data = await loop.run_in_executor(None, calculate_volatility_cone, date, symbol)
        
        if "error" in cone_data:
            raise HTTPException(status_code=400, detail=cone_data["error"])
            
        # 2. Get Current ATM Term Structure
        # We need to load option data for 'date'
        try:
            df = _load_date_data(date, dataset_id=symbol)
        except:
             # If no data for today, return cone with fallback spot
             spot_fallback = 0
             if "latest_price" in cone_data and cone_data["latest_price"] > 0:
                 spot_fallback = cone_data["latest_price"]
             elif "current" in cone_data: # Sometimes it might be structured differently
                 pass
                 
             if spot_fallback == 0: spot_fallback = 3.0
                 
             return {
                 "cone": cone_data,
                 "current_curve": [],
                 "spot_ref": spot_fallback
             }
        
        # Calculate Spot
        spot = None
        if 'underlying_close' in df.columns:
             v = df['underlying_close'].dropna()
             if not v.empty: spot = float(v.iloc[0])
        
        if spot is None:
             spot = _calculate_implied_spot(df)
             
        if spot is None:
             # Median strike fallback
             if 'strike' in df.columns:
                 spot = float(df['strike'].median())
        
        # FINAL FALLBACK: Use Cone History Latest Price
        # This handles the case where today's option data is missing or has no underlying/strike
        if (spot is None or spot == 0) and "latest_price" in cone_data and cone_data["latest_price"] > 0:
             spot = cone_data["latest_price"]
             
        if spot is None:
             spot = 3.0 # Ultimate fallback
                 
        # Get ATM IVs for each expiry
        current_curve = []
        
        if 'expiry_date' in df.columns and 'strike' in df.columns:
            # Group by expiry
            expiries = df['expiry_date'].unique()
            current_dt = datetime.strptime(date, "%Y-%m-%d")
            
            for exp in expiries:
                try:
                    exp_dt = pd.to_datetime(exp)
                    days = (exp_dt - current_dt).days
                    
                    if days <= 0: continue
                    
                    # Get slice
                    sub = df[df['expiry_date'] == exp].copy()
                    sub['diff'] = abs(sub['strike'] - spot)
                    sub = sub.sort_values('diff')
                    
                    # Robust IV Extraction: Check ATM and neighbors
                    iv = 0
                    iv_found = False
                    
                    # Try top 3 closest strikes
                    candidates = sub.iloc[:3]
                    
                    for _, row in candidates.iterrows():
                        # Try using pre-calculated IV from file
                        # Tushare/BaoStock/Wind common columns
                        iv_aliases = [
                            'us_impliedvol', 'iv', 'implied_volatility', 
                            'implied_vol', 'current_iv', 'delta_iv',
                            'best_bid_iv', 'best_ask_iv', 'mid_iv'
                        ]
                        
                        for col in iv_aliases:
                            if col in row and pd.notna(row[col]):
                                val = float(row[col])
                                if 0.01 < val < 5.0: # Sanity check (up to 500% IV is theoretically possible)
                                    iv = val
                                    iv_found = True
                                    break
                                    
                        # If still no IV found, calculate it!
                        if not iv_found:
                            try:
                                T = days / 365.0
                                K = float(row['strike'])
                                price = float(row['close'])
                                opt_type = str(row['type']).upper()
                                if opt_type in ['C', 'CALL', '认购', '购']: type_flag = 'C'
                                elif opt_type in ['P', 'PUT', '认沽', '沽']: type_flag = 'P'
                                else: type_flag = 'C' # Default
                                
                                calc_iv = _calculate_iv_bisection(price, spot, K, T, 0.03, type_flag)
                                
                                if calc_iv and 0.01 < calc_iv < 5.0:
                                    iv = calc_iv
                                    iv_found = True
                            except:
                                pass
                                
                        if iv_found: break
                        
                    if iv > 0:
                        current_curve.append({
                            "days": int(days),
                            "iv": round(iv, 4),
                            "expiry": str(exp).split(' ')[0],
                            "strike": float(candidates.iloc[0]['strike']) # Log the ATM strike
                        })
                except:
                    continue
                    
        # Sort by days
        current_curve.sort(key=lambda x: x['days'])

        # 3. Interpolate Current IV for Cone Windows (Backend Side)
        from ..analytics.volatility import interpolate_constant_maturity_iv
        
        if 'cone_curves' in cone_data:
            for curve in cone_data['cone_curves']:
                target_days = curve['window']
                # Calculate Constant Maturity IV
                if current_curve:
                    cm_iv = interpolate_constant_maturity_iv(target_days, current_curve)
                    curve['current_iv'] = round(cm_iv, 4) if cm_iv > 0 else 0
                else:
                    curve['current_iv'] = None

        return {
            "cone": cone_data,
            "current_curve": current_curve,
            "spot_ref": spot
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from ..analytics.volatility import get_progress

@router.get("/progress")
async def get_loading_progress():
    """Get global loading progress for analytics."""
    return get_progress()
