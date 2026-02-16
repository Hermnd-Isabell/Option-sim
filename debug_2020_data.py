import urllib.request
import json
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

def debug_2020():
    # User's specific failing date
    date = "2020-03-17"
    url = f"http://localhost:8000/api/analytics/vol-cone?date={date}&symbol=510050_SH"
    
    logger.info(f"Querying: {url}")
    
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                logger.error(f"HTTP Error: {response.status}")
                return
            
            raw = response.read().decode()
            data = json.loads(raw)
            
            logger.info("\n--- DIAGNOSTICS FOR 2020-03-17 ---")
            
            # 1. Spot Price
            spot = data.get('spot_ref')
            logger.info(f"Spot Ref: {spot}")
            if not spot or spot == 0:
                logger.error("!!! Spot Price is ZERO or None. IV Calc will fail.")
            
            # 2. Raw Curve Data (What did we extract?)
            curve = data.get('current_curve', [])
            logger.info(f"Current Curve Points found: {len(curve)}")
            if len(curve) > 0:
                 for i, p in enumerate(curve[:5]):
                     logger.info(f"  [{i}] Exp: {p.get('expiry')} | Days: {p.get('days')} | Strike: {p.get('strike')} | IV: {p.get('iv')}")
            else:
                logger.error("!!! No raw curve points extracted. Check file reading or column mapping.")

            # 3. Interpolated Cone Data
            cone_curves = data.get('cone', {}).get('cone_curves', [])
            if cone_curves:
                first = cone_curves[0]
                logger.info(f"First Cone Window ({first.get('window')}d): Current IV = {first.get('current_iv')}")
                if first.get('current_iv') == 0:
                     logger.error("!!! Interpolated IV is 0.")
            else:
                 logger.error("!!! No cone curves returned.")

    except Exception as e:
        logger.error(f"Request failed: {e}")

if __name__ == "__main__":
    debug_2020()
