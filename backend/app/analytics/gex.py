
import pandas as pd
import numpy as np
import scipy.stats as si
import plotly.graph_objects as go
from datetime import datetime
import math

# Try importing IV calculation from existing module
try:
    from app.api.data import _calculate_iv_bisection
except ImportError:
    # Fallback or mock if running standalone without app context
    def _calculate_iv_bisection(*args, **kwargs):
        return None

def calculate_gamma(S, K, T, r, sigma, option_type='C'):
    """
    Calculate Gamma for European options (Vectorized).
    Gamma = N'(d1) / (S * sigma * sqrt(T))
    S, K, T, r, sigma can be numpy arrays or scalars.
    """
    # Convert to numpy arrays if needed
    S = np.array(S, dtype=float)
    K = np.array(K, dtype=float)
    T = np.array(T, dtype=float)
    r = np.array(r, dtype=float)
    sigma = np.array(sigma, dtype=float)
    
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        prob_density = si.norm.pdf(d1)
        gamma = prob_density / (S * sigma * np.sqrt(T))
    
    # Handle NaN/Inf where T near 0
    gamma = np.nan_to_num(gamma, nan=0.0, posinf=0.0, neginf=0.0)
    return gamma

def calculate_gex_profile(df_options, spot_price):
    """
    Calculate Gamma Exposure Profile.
    
    Args:
        df_options (pd.DataFrame): DataFrame containing option chain.
            Required columns: 'strike', 'type' (or 'contract_type'), 'expiry_date'.
            Optional columns: 'gamma', 'open_interest' (or 'oi', 'position'), 'volume', 'implied_volatility'.
        spot_price (float): Current underlying price.
        
    Returns:
        pd.DataFrame: Aggregated GEX by Strike.
    """
    df = df_options.copy()
    
    # Standardize Column Names
    # Expect: strike, type, open_interest, gamma
    col_map = {
        'strike_price': 'strike',
        'contract_type': 'type',
        'option_type': 'type',
        'oi': 'open_interest',
        'position': 'open_interest',
        'vol': 'volume'
    }
    df = df.rename(columns=col_map)
    
    # 1. Ensure Gamma exists
    if 'gamma' not in df.columns:
        print("Calculating Gamma...")
        r = 0.03 # Risk free rate
        gammas = []
        
        # We need IV
        if 'implied_volatility' not in df.columns:
            # Check for other names
            first_found = next((c for c in df.columns if 'iv' in c.lower() or 'implied' in c.lower()), None)
            if first_found:
                df['implied_volatility'] = df[first_found]
            else:
                # Calculate IV if missing!
                # This is expensive, so warn user
                print("Warning: Implied Volatility missing. Calculating IVs (slow)...")
                ivs = []
                for idx, row in df.iterrows():
                    # Need expiry
                    T = 0.1
                    if 'expiry_date' in row:
                        try:
                            exp_date = pd.to_datetime(row['expiry_date'])
                            # Assume trade_date or today
                            today = pd.to_datetime(row.get('trade_date', datetime.now()))
                            T = (exp_date - today).days / 365.0
                        except: pass
                    
                    price = row.get('close', row.get('price', 0))
                    iv = _calculate_iv_bisection(price, spot_price, row['strike'], T, r, 
                                                 'C' if str(row.get('type')).upper() in ['C', 'CALL', '认购'] else 'P')
                    ivs.append(iv if iv else 0.0)
                df['implied_volatility'] = ivs
        
    # Calculate Gamma
        # Vectorized calculation
        T = np.full(len(df), 0.1)
        if 'expiry_date' in df.columns:
            # Convert expiry to T
            try:
                # Assuming trade_date is available or use today
                today = pd.to_datetime(df.get('trade_date', datetime.now())).values
                exp = pd.to_datetime(df['expiry_date']).values
                
                # Time delta in days / 365
                # Ensure positive T
                T_days = (exp - today).astype('timedelta64[D]').astype(float)
                T = np.maximum(T_days / 365.0, 0.001)
            except Exception as e:
                # Fallback T=0.1 if vector conversion fails
                print(f"Vectorized T calc failed: {e}")
                pass
        
        sigma = df['implied_volatility'].fillna(0).astype(float).values
        strikes = df['strike'].astype(float).values
        
        # Calculate Gamma Vectorized
        gammas = calculate_gamma(
            S=spot_price,
            K=strikes,
            T=T,
            r=r,
            sigma=sigma
        )
        df['gamma'] = gammas

    # 2. Determine Exposure Metric (OI or Volume)
    exposure_col = 'open_interest'
    if 'open_interest' not in df.columns or df['open_interest'].sum() == 0:
        if 'volume' in df.columns:
            print("Warning: Open Interest missing. Using VOLUME as proxy for GEX calculation.")
            exposure_col = 'volume'
        else:
            raise ValueError("No Open Interest or Volume data found.")
            
    # 3. Calculate GEX Components
    # Call: OI * Gamma * (-1)
    # Put: OI * Gamma * (+1) (Based on user request, otherwise usually PotSpotGamma is positive for dealers?)
    # User Request: Put -> Positive Gamma for MM (Short Put)
    
    def get_contribution(row):
        oi = row.get(exposure_col, 0)
        gamma = row.get('gamma', 0)
        
        # Convert type to standard
        t = str(row.get('type', '')).upper()
        is_call = t in ['C', 'CALL', '认购', '购']
        is_put = t in ['P', 'PUT', '认沽', '沽']
        
        if is_call:
            return oi * gamma * (-1)
        elif is_put:
             return oi * gamma * (+1)
        return 0.0
        
    df['gex_raw'] = df.apply(get_contribution, axis=1)
    
    # 4. Convert to Dollar GEX
    # GEX_$ = GEX_K * S^2 * 0.01
    factor = (spot_price ** 2) * 0.01
    df['gex_dollar'] = df['gex_raw'] * factor
    
    # 5. Aggregate by Strike
    gex_profile = df.groupby('strike')['gex_dollar'].sum().reset_index()
    gex_profile = gex_profile.sort_values('strike')
    
    return gex_profile

def plot_gex_profile(gex_df, spot_price):
    """
    Plot Gamma Exposure Profile using Plotly.
    """
    gex_df['color'] = np.where(gex_df['gex_dollar'] >= 0, 'green', 'red')
    
    fig = go.Figure()
    
    # Bar Chart
    fig.add_trace(go.Bar(
        x=gex_df['strike'],
        y=gex_df['gex_dollar'],
        marker_color=gex_df['color'],
        name='Gamma Exposure'
    ))
    
    # Spot Price Line
    # Find Y range for line
    y_min, y_max = gex_df['gex_dollar'].min(), gex_df['gex_dollar'].max()
    margin = (y_max - y_min) * 0.1
    
    fig.add_shape(
        type="line",
        x0=spot_price, y0=y_min - margin,
        x1=spot_price, y1=y_max + margin,
        line=dict(color="blue", width=2, dash="dash"),
        name="Spot Price"
    )
    
    fig.add_annotation(
        x=spot_price,
        y=y_max,
        text=f"Spot: {spot_price:.2f}",
        showarrow=True,
        arrowhead=1
    )
    
    # Zero Line
    fig.add_shape(
        type="line",
        x0=gex_df['strike'].min(), y0=0,
        x1=gex_df['strike'].max(), y1=0,
        line=dict(color="black", width=1),
    )
    
    fig.update_layout(
        title=f"Dealer Gamma Exposure Profile (Spot: {spot_price})",
        xaxis_title="Strike Price",
        yaxis_title="Gamma Exposure ($)",
        template="plotly_dark",
        bargap=0.1
    )
    
    return fig

def calculate_zero_gamma(gex_df, spot_price):
    """
    Calculates the Zero Gamma Flip Level.
    Logic: Find the strike interval where Net GEX changes sign (crosses zero).
    we interpolate between the two strikes.
    """
    if gex_df.empty:
        return None
        
    # Sort by strike
    df = gex_df.sort_values('strike').reset_index(drop=True)
    
    # Check for sign changes
    # We are looking for a transition from + to - or - to +
    # in the vicinity of the spot price (ATM).
    
    crossings = []
    for i in range(len(df) - 1):
        gex1 = df.loc[i, 'gex_dollar'] # Use dollar GEX for flip
        gex2 = df.loc[i+1, 'gex_dollar']
        k1 = df.loc[i, 'strike']
        k2 = df.loc[i+1, 'strike']
        
        if (gex1 > 0 and gex2 < 0) or (gex1 < 0 and gex2 > 0):
            # Linear Interpolation: y = mx + c
            # 0 = gex1 + (slope) * (x - k1)
            # slope = (gex2 - gex1) / (k2 - k1)
            if gex2 != gex1:
                slope = (gex2 - gex1) / (k2 - k1)
                zero_k = k1 + (0 - gex1) / slope
                crossings.append(zero_k)
    
    if not crossings:
        return None
        
    # If multiple crossings, return the one closest to spot price
    closest_flip = min(crossings, key=lambda x: abs(x - spot_price))
    return closest_flip

def get_expiration_summary(df):
    """Returns summary of expiration dates."""
    if 'expiry_date' not in df.columns:
        return None
    
    unique_exps = sorted(df['expiry_date'].dropna().astype(str).unique())
    if len(unique_exps) == 0:
        return None
        
    return {
        "min_expiry": unique_exps[0],
        "max_expiry": unique_exps[-1],
        "count": len(unique_exps),
        "next_expirations": unique_exps[:3]
    }

if __name__ == "__main__":
    # Simple Test
    print("Testing GEX Module...")
