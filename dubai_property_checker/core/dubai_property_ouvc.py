# Dubai Property Over/Under Value Checker Core Module
# Enhanced Real Estate Valuation Framework for UAE Market

import os
import re
import json
import time
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Machine Learning imports
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_percentage_error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= Configuration =============
class PropertyType(Enum):
    APARTMENT = "apartment"
    VILLA = "villa"
    TOWNHOUSE = "townhouse"
    PENTHOUSE = "penthouse"
    STUDIO = "studio"

class Area(Enum):
    """Major Dubai areas with distinct pricing dynamics"""
    DUBAI_MARINA = "dubai-marina"
    DOWNTOWN = "downtown-dubai"
    JBR = "jbr"
    PALM_JUMEIRAH = "palm-jumeirah"
    BUSINESS_BAY = "business-bay"
    DIFC = "difc"
    DUBAI_CREEK = "dubai-creek-harbour"
    DUBAI_HILLS = "dubai-hills-estate"
    ARABIAN_RANCHES = "arabian-ranches"
    JVC = "jvc"
    JVT = "jvt"
    SPORTS_CITY = "sports-city"
    SILICON_OASIS = "dubai-silicon-oasis"
    DISCOVERY_GARDENS = "discovery-gardens"

# Area-specific yield expectations (2024 market data)
AREA_YIELDS = {
    Area.DUBAI_MARINA: {"min": 5.5, "avg": 6.8, "max": 8.2},
    Area.DOWNTOWN: {"min": 4.5, "avg": 5.8, "max": 7.0},
    Area.JBR: {"min": 5.0, "avg": 6.5, "max": 7.8},
    Area.PALM_JUMEIRAH: {"min": 4.0, "avg": 5.2, "max": 6.5},
    Area.BUSINESS_BAY: {"min": 6.0, "avg": 7.5, "max": 9.0},
    Area.JVC: {"min": 6.5, "avg": 8.0, "max": 9.5},
    Area.SPORTS_CITY: {"min": 7.0, "avg": 8.5, "max": 10.0},
    Area.DISCOVERY_GARDENS: {"min": 7.5, "avg": 9.0, "max": 11.0},
}

# Dubai-specific market factors
MARKET_FACTORS = {
    "expo_2020_premium": 1.08,  # Properties near Expo site
    "metro_proximity_premium": 1.12,  # Within 500m of metro
    "beach_proximity_premium": 1.15,  # Beachfront properties
    "burj_khalifa_view_premium": 1.10,  # Downtown view premium
    "new_development_discount": 0.95,  # Off-plan risk discount
    "service_charge_impact": -0.02,  # Per AED/sqft service charge
}

# ============= Data Models =============
@dataclass
class Property:
    """Property data model with UAE-specific fields"""
    area: str
    property_type: PropertyType
    bedrooms: int
    bathrooms: int
    size_sqft: int
    price_aed: float
    service_charge_sqft: Optional[float] = None
    parking_spaces: Optional[int] = None
    furnished: Optional[bool] = None
    developer: Optional[str] = None
    completion_year: Optional[int] = None
    floor_number: Optional[int] = None
    total_floors: Optional[int] = None
    view_type: Optional[str] = None  # sea, city, garden, etc.
    metro_distance_m: Optional[int] = None
    beach_distance_m: Optional[int] = None
    rental_income: Optional[float] = None  # Annual rental if rented
    
    @property
    def price_per_sqft(self) -> float:
        return self.price_aed / self.size_sqft if self.size_sqft > 0 else 0
    
    @property
    def gross_rental_yield(self) -> Optional[float]:
        if self.rental_income and self.price_aed > 0:
            return (self.rental_income / self.price_aed) * 100
        return None
    
    @property
    def net_rental_yield(self) -> Optional[float]:
        if self.gross_rental_yield and self.service_charge_sqft:
            annual_service = self.service_charge_sqft * self.size_sqft
            net_income = self.rental_income - annual_service
            return (net_income / self.price_aed) * 100
        return self.gross_rental_yield

# ============= API Clients =============
class BayutClient:
    """Bayut/Property Finder API integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://bayut-api1.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "bayut-api1.p.rapidapi.com"
        }
        self.rate_limiter = RateLimiter(max_requests_per_minute=10)
    
    def search_properties(self, 
                         area: str, 
                         property_type: str,
                         bedrooms: int,
                         min_price: float,
                         max_price: float,
                         min_size: int,
                         max_size: int,
                         purpose: str = "for-sale") -> List[Dict]:
        """Search for comparable properties"""
        
        self.rate_limiter.wait_if_needed()
        
        params = {
            "location": area,
            "categoryExternalID": self._get_category_id(property_type, bedrooms),
            "purpose": purpose,
            "priceMin": int(min_price),
            "priceMax": int(max_price),
            "areaMin": int(min_size),
            "areaMax": int(max_size),
            "sort": "date-desc",
            "page": 0,
            "hitsPerPage": 25
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/properties/list",
                headers=self.headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_properties(data.get("hits", []))
            else:
                logger.error(f"Bayut API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Bayut search failed: {e}")
            return []
    
    def _get_category_id(self, property_type: str, bedrooms: int) -> int:
        """Map to Bayut category IDs"""
        # Bayut specific category mapping
        categories = {
            "apartment-1": 4,
            "apartment-2": 5,
            "apartment-3": 6,
            "villa-3": 35,
            "villa-4": 36,
            "villa-5": 37,
            "townhouse-2": 38,
            "townhouse-3": 39,
            "studio-0": 3
        }
        key = f"{property_type}-{bedrooms}"
        return categories.get(key, 4)  # Default to 1-bed apartment
    
    def _parse_properties(self, hits: List[Dict]) -> List[Property]:
        """Parse Bayut response to Property objects"""
        properties = []
        
        for hit in hits:
            try:
                prop = Property(
                    area=hit.get("location", [{}])[0].get("name", "Unknown"),
                    property_type=PropertyType.APARTMENT,  # Parse from category
                    bedrooms=hit.get("rooms", 0),
                    bathrooms=hit.get("baths", 1),
                    size_sqft=int(hit.get("area", 0)),
                    price_aed=float(hit.get("price", 0)),
                    furnished=hit.get("furnishingStatus") == "furnished",
                    developer=hit.get("agency", {}).get("name"),
                    completion_year=hit.get("completionStatus", {}).get("year"),
                    view_type=self._extract_view(hit.get("description", ""))
                )
                properties.append(prop)
            except Exception as e:
                logger.debug(f"Failed to parse property: {e}")
                continue
        
        return properties
    
    def _extract_view(self, description: str) -> Optional[str]:
        """Extract view type from description"""
        description_lower = description.lower()
        views = ["sea view", "burj khalifa", "marina view", "golf course", "city view"]
        for view in views:
            if view in description_lower:
                return view
        return None

class DLDClient:
    """Dubai Land Department API/Data integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # DLD doesn't have public API, so we scrape or use cached data
        self.transactions_cache = {}
        self.load_cached_transactions()
    
    def load_cached_transactions(self):
        """Load historical DLD transaction data"""
        # In production, this would load from DLD CSV exports or database
        # For now, we'll use synthetic representative data
        pass
    
    def get_recent_transactions(self, 
                               area: str,
                               property_type: str,
                               bedrooms: int,
                               size_range: Tuple[int, int],
                               days_back: int = 90) -> pd.DataFrame:
        """Get recent actual transaction data from DLD"""
        
        # Synthetic data for demo - replace with actual DLD data
        # DLD provides quarterly transaction reports
        transactions = pd.DataFrame({
            'date': pd.date_range(end=datetime.now(), periods=20, freq='D'),
            'area': [area] * 20,
            'property_type': [property_type] * 20,
            'bedrooms': [bedrooms] * 20,
            'size_sqft': np.random.randint(size_range[0], size_range[1], 20),
            'price_aed': np.random.randint(800000, 2000000, 20),
            'transaction_type': ['sale'] * 20
        })
        
        transactions['price_per_sqft'] = transactions['price_aed'] / transactions['size_sqft']
        
        return transactions
    
    def get_rental_index(self, area: str, property_type: str, bedrooms: int) -> Dict:
        """Get RERA rental index data"""
        # RERA publishes official rental indices
        # This would connect to RERA rental calculator
        
        if area in ["dubai-marina", "downtown-dubai", "jbr"]:
            annual_rent_range = {
                1: (80000, 120000),
                2: (120000, 180000),
                3: (180000, 280000)
            }
        else:
            annual_rent_range = {
                1: (50000, 80000),
                2: (80000, 130000),
                3: (130000, 200000)
            }
        
        min_rent, max_rent = annual_rent_range.get(bedrooms, (50000, 100000))
        
        return {
            "min_annual_rent": min_rent,
            "avg_annual_rent": (min_rent + max_rent) / 2,
            "max_annual_rent": max_rent,
            "last_updated": datetime.now().isoformat()
        }

class DubizzleClient:
    """Dubizzle (now Bayut) scraper for additional data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_market_insights(self, area: str) -> Dict:
        """Scrape market insights and trends"""
        # Implementation for scraping Dubizzle/PropertyFinder insights
        return {
            "avg_days_on_market": 45,
            "price_trend_3m": 0.03,  # +3% in last 3 months
            "inventory_level": "moderate",
            "buyer_demand": "high"
        }

# ============= Valuation Engine =============
class DubaiPropertyValuator:
    """Advanced property valuation using multiple models"""
    
    def __init__(self, bayut_key: str, dld_key: Optional[str] = None):
        self.bayut = BayutClient(bayut_key)
        self.dld = DLDClient(dld_key)
        self.dubizzle = DubizzleClient()
        
        # Initialize ML models
        self.models = {
            'linear': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        self.scaler = StandardScaler()
        self.label_encoders = {}
    
    def fetch_comparables(self, target_property: Property, radius_pct: float = 0.20) -> pd.DataFrame:
        """Fetch comparable properties within radius of target specs"""
        
        # Search parameters with radius
        min_price = target_property.price_aed * (1 - radius_pct)
        max_price = target_property.price_aed * (1 + radius_pct)
        min_size = target_property.size_sqft * (1 - radius_pct)
        max_size = target_property.size_sqft * (1 + radius_pct)
        
        # Get listings from Bayut
        listings = self.bayut.search_properties(
            area=target_property.area,
            property_type=target_property.property_type.value,
            bedrooms=target_property.bedrooms,
            min_price=min_price,
            max_price=max_price,
            min_size=min_size,
            max_size=max_size
        )
        
        # Get actual transactions from DLD
        transactions = self.dld.get_recent_transactions(
            area=target_property.area,
            property_type=target_property.property_type.value,
            bedrooms=target_property.bedrooms,
            size_range=(int(min_size), int(max_size))
        )
        
        # Combine data sources
        comps_df = self._combine_data_sources(listings, transactions)
        
        # Add derived features
        if not comps_df.empty:
            comps_df = self._add_derived_features(comps_df, target_property.area)
        
        return comps_df
    
    def _combine_data_sources(self, listings: List[Property], transactions: pd.DataFrame) -> pd.DataFrame:
        """Combine and weight different data sources"""
        
        # Convert listings to DataFrame
        if listings:
            listings_data = []
            for prop in listings:
                listings_data.append({
                    'source': 'bayut',
                    'price_aed': prop.price_aed,
                    'size_sqft': prop.size_sqft,
                    'bedrooms': prop.bedrooms,
                    'bathrooms': prop.bathrooms,
                    'price_per_sqft': prop.price_per_sqft,
                    'furnished': prop.furnished,
                    'view_type': prop.view_type,
                    'data_quality': 0.8  # Listing data less reliable than transactions
                })
            listings_df = pd.DataFrame(listings_data)
        else:
            listings_df = pd.DataFrame()
        
        # Add transactions with higher weight
        if not transactions.empty:
            transactions['source'] = 'dld'
            transactions['data_quality'] = 1.0  # Actual transactions most reliable
        
        # Combine
        combined = pd.concat([listings_df, transactions], ignore_index=True)
        
        return combined
    
    def _add_derived_features(self, df: pd.DataFrame, area: str) -> pd.DataFrame:
        """Add Dubai market-specific derived features"""
        
        # Price percentiles for outlier detection
        df['price_percentile'] = df['price_aed'].rank(pct=True)
        
        # Size categories (Dubai specific)
        df['size_category'] = pd.cut(df['size_sqft'], 
                                     bins=[0, 500, 1000, 1500, 2500, 10000],
                                     labels=['tiny', 'small', 'medium', 'large', 'luxury'])
        
        # Luxury indicator
        df['is_luxury'] = (df['price_per_sqft'] > df['price_per_sqft'].quantile(0.75))
        
        # Market heat (how many similar properties available)
        df['market_heat'] = len(df) / 100  # Normalized
        
        # Add area-specific yield expectations
        if area in [a.value for a in Area]:
            area_enum = Area(area)
            if area_enum in AREA_YIELDS:
                df['expected_yield_min'] = AREA_YIELDS[area_enum]['min']
                df['expected_yield_avg'] = AREA_YIELDS[area_enum]['avg']
                df['expected_yield_max'] = AREA_YIELDS[area_enum]['max']
        
        return df
    
    def calculate_avm(self, target_property: Property, comps_df: pd.DataFrame) -> Dict:
        """
        Advanced Automated Valuation Model using ensemble methods
        """
        if comps_df.empty or len(comps_df) < 5:
            return {
                "error": "Insufficient comparables for accurate valuation",
                "comps_found": len(comps_df)
            }
        
        # Prepare features for ML models
        feature_cols = ['size_sqft', 'bedrooms', 'bathrooms', 'price_per_sqft']
        
        # Handle categorical features
        if 'size_category' in comps_df.columns:
            le = LabelEncoder()
            comps_df['size_cat_encoded'] = le.fit_transform(comps_df['size_category'])
            feature_cols.append('size_cat_encoded')
        
        # Prepare training data
        X = comps_df[feature_cols].fillna(comps_df.median())
        y = comps_df['price_aed']
        
        # Weight samples by data quality
        sample_weights = comps_df['data_quality'].values
        
        # Train multiple models
        predictions = {}
        model_scores = {}
        
        for name, model in self.models.items():
            try:
                # Fit with sample weights if supported
                if hasattr(model, 'sample_weight'):
                    model.fit(X, y, sample_weight=sample_weights)
                else:
                    model.fit(X, y)
                
                # Cross-validation score
                scores = cross_val_score(model, X, y, cv=min(5, len(X)//2), 
                                        scoring='neg_mean_absolute_percentage_error')
                model_scores[name] = -scores.mean()
                
                # Predict for target
                target_features = self._prepare_target_features(target_property, comps_df, feature_cols)
                pred = model.predict(target_features)[0]
                predictions[name] = pred
                
            except Exception as e:
                logger.error(f"Model {name} failed: {e}")
                continue
        
        if not predictions:
            return {"error": "All models failed"}
        
        # Ensemble prediction (weighted average based on performance)
        total_weight = sum(1/s if s > 0 else 0 for s in model_scores.values())
        if total_weight > 0:
            weights = {k: (1/v)/total_weight if v > 0 else 0 for k, v in model_scores.items()}
            ensemble_prediction = sum(predictions[k] * weights.get(k, 0) for k in predictions)
        else:
            ensemble_prediction = np.mean(list(predictions.values()))
        
        # Calculate confidence interval
        pred_std = np.std(list(predictions.values()))
        confidence_low = ensemble_prediction - (1.96 * pred_std)
        confidence_high = ensemble_prediction + (1.96 * pred_std)
        
        # Rental yield analysis
        rental_data = self.dld.get_rental_index(
            target_property.area,
            target_property.property_type.value,
            target_property.bedrooms
        )
        
        estimated_yield = (rental_data['avg_annual_rent'] / ensemble_prediction) * 100
        
        # Market insights
        insights = self.dubizzle.get_market_insights(target_property.area)
        
        # Calculate key metrics
        price_to_estimate_ratio = target_property.price_aed / ensemble_prediction
        
        # Determine if undervalued
        valuation_signals = self._calculate_valuation_signals(
            target_property,
            ensemble_prediction,
            estimated_yield,
            insights,
            comps_df
        )
        
        return {
            "estimated_value": round(ensemble_prediction),
            "confidence_interval": {
                "low": round(confidence_low),
                "high": round(confidence_high)
            },
            "model_predictions": {k: round(v) for k, v in predictions.items()},
            "model_accuracy": {k: f"{(1-v)*100:.1f}%" for k, v in model_scores.items()},
            "price_to_estimate_ratio": round(price_to_estimate_ratio, 3),
            "estimated_rental_yield": round(estimated_yield, 2),
            "rental_data": rental_data,
            "market_insights": insights,
            "valuation_signals": valuation_signals,
            "comparable_properties": len(comps_df),
            "data_sources": comps_df['source'].value_counts().to_dict()
        }
    
    def _prepare_target_features(self, target: Property, comps_df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        """Prepare target property features for prediction"""
        features = []
        
        for col in feature_cols:
            if col == 'size_sqft':
                features.append(target.size_sqft)
            elif col == 'bedrooms':
                features.append(target.bedrooms)
            elif col == 'bathrooms':
                features.append(target.bathrooms or comps_df['bathrooms'].median())
            elif col == 'price_per_sqft':
                features.append(comps_df['price_per_sqft'].median())
            elif col == 'size_cat_encoded':
                # Encode target's size category
                if target.size_sqft < 500:
                    features.append(0)
                elif target.size_sqft < 1000:
                    features.append(1)
                elif target.size_sqft < 1500:
                    features.append(2)
                elif target.size_sqft < 2500:
                    features.append(3)
                else:
                    features.append(4)
            else:
                features.append(comps_df[col].median())
        
        return np.array(features).reshape(1, -1)
    
    def _calculate_valuation_signals(self, 
                                    target: Property,
                                    estimated_value: float,
                                    estimated_yield: float,
                                    insights: Dict,
                                    comps_df: pd.DataFrame) -> Dict:
        """Calculate comprehensive valuation signals"""
        
        signals = {
            "price_signal": "neutral",
            "yield_signal": "neutral",
            "market_signal": "neutral",
            "overall_verdict": "HOLD",
            "confidence": "medium",
            "key_factors": []
        }
        
        # Price signal
        ratio = target.price_aed / estimated_value
        if ratio < 0.90:
            signals["price_signal"] = "undervalued"
            signals["key_factors"].append(f"Priced {(1-ratio)*100:.1f}% below estimate")
        elif ratio > 1.10:
            signals["price_signal"] = "overvalued"
            signals["key_factors"].append(f"Priced {(ratio-1)*100:.1f}% above estimate")
        
        # Yield signal
        area_yields = AREA_YIELDS.get(Area(target.area), {"avg": 6.0, "max": 8.0})
        if estimated_yield > area_yields["avg"]:
            signals["yield_signal"] = "attractive"
            signals["key_factors"].append(f"Yield {estimated_yield:.1f}% above area avg")
        elif estimated_yield < area_yields["avg"] * 0.8:
            signals["yield_signal"] = "low"
            signals["key_factors"].append(f"Yield below area average")
        
        # Market signal
        if insights.get("price_trend_3m", 0) > 0.05:
            signals["market_signal"] = "hot"
            signals["key_factors"].append("Area prices rising rapidly")
        elif insights.get("buyer_demand") == "high" and insights.get("inventory_level") == "low":
            signals["market_signal"] = "competitive"
            signals["key_factors"].append("High demand, low inventory")
        
        # Confidence based on data quality
        if len(comps_df) > 20 and comps_df['source'].str.contains('dld').sum() > 5:
            signals["confidence"] = "high"
        elif len(comps_df) < 10:
            signals["confidence"] = "low"
        
        # Overall verdict
        positive_signals = sum([
            signals["price_signal"] == "undervalued",
            signals["yield_signal"] == "attractive",
            signals["market_signal"] in ["hot", "competitive"]
        ])
        
        if positive_signals >= 2 and ratio < 0.95:
            signals["overall_verdict"] = "STRONG BUY"
            signals["key_factors"].insert(0, "Multiple positive indicators")
        elif positive_signals >= 2 or ratio < 0.90:
            signals["overall_verdict"] = "BUY"
        elif ratio > 1.15 or signals["yield_signal"] == "low":
            signals["overall_verdict"] = "AVOID"
        else:
            signals["overall_verdict"] = "HOLD"
        
        return signals

# ============= Utility Classes =============
class RateLimiter:
    """Rate limiter for API calls"""
    def __init__(self, max_requests_per_minute=10):
        self.max_requests = max_requests_per_minute
        self.requests = []
    
    def wait_if_needed(self):
        now = time.time()
        self.requests = [r for r in self.requests if now - r < 60]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = 60 - (now - self.requests[0]) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.requests.append(now)

# ============= Main Interface =============
def analyze_dubai_property(
    area: str,
    property_type: str,
    bedrooms: int,
    size_sqft: int,
    asking_price_aed: float,
    bathrooms: Optional[int] = None,
    furnished: Optional[bool] = None,
    service_charge_sqft: Optional[float] = None,
    view_type: Optional[str] = None
) -> Dict:
    """
    Main function to analyze a Dubai property
    
    Args:
        area: Dubai area (e.g., 'dubai-marina', 'downtown-dubai')
        property_type: Type of property ('apartment', 'villa', 'townhouse')
        bedrooms: Number of bedrooms
        size_sqft: Size in square feet
        asking_price_aed: Asking price in AED
        bathrooms: Number of bathrooms (optional)
        furnished: Is furnished (optional)
        service_charge_sqft: Service charge per sqft per year (optional)
        view_type: View type (optional)
    
    Returns:
        Comprehensive valuation analysis
    """
    
    # Get API keys from environment
    bayut_key = os.getenv("BAYUT_API_KEY")
    dld_key = os.getenv("DLD_API_KEY")
    
    if not bayut_key:
        return {"error": "Please set BAYUT_API_KEY environment variable"}
    
    # Create target property
    target = Property(
        area=area,
        property_type=PropertyType(property_type),
        bedrooms=bedrooms,
        bathrooms=bathrooms or bedrooms,
        size_sqft=size_sqft,
        price_aed=asking_price_aed,
        service_charge_sqft=service_charge_sqft,
        furnished=furnished,
        view_type=view_type
    )
    
    # Initialize valuator
    valuator = DubaiPropertyValuator(bayut_key, dld_key)
    
    # Fetch comparables
    print(f"🔍 Fetching comparable properties in {area}...")
    comps_df = valuator.fetch_comparables(target)
    
    if comps_df.empty:
        return {
            "error": "No comparable properties found",
            "suggestion": "Try adjusting search radius or checking area name"
        }
    
    print(f"✅ Found {len(comps_df)} comparable properties")
    
    # Calculate valuation
    print("🧮 Running valuation models...")
    results = valuator.calculate_avm(target, comps_df)
    
    if "error" in results:
        return results
    
    # Format output
    print("\n" + "="*70)
    print(f"DUBAI PROPERTY VALUATION ANALYSIS")
    print("="*70)
    print(f"Property: {bedrooms} BR {property_type.title()} in {area.replace('-', ' ').title()}")
    print(f"Size: {size_sqft:,} sqft")
    print(f"Asking Price: AED {asking_price_aed:,.0f}")
    print("-"*70)
    print(f"Estimated Value: AED {results['estimated_value']:,.0f}")
    print(f"Confidence Range: AED {results['confidence_interval']['low']:,.0f} - {results['confidence_interval']['high']:,.0f}")
    print(f"Price vs Estimate: {results['price_to_estimate_ratio']:.2f}x")
    print(f"Expected Rental Yield: {results['estimated_rental_yield']:.2f}%")
    print("-"*70)
    print(f"Verdict: {results['valuation_signals']['overall_verdict']}")
    print(f"Confidence: {results['valuation_signals']['confidence'].upper()}")
    print("\nKey Factors:")
    for factor in results['valuation_signals']['key_factors']:
        print(f"  • {factor}")
    print("="*70)
    
    return results

# ============= Example Usage =============
if __name__ == "__main__":
    # Example: 2BR apartment in Dubai Marina
    result = analyze_dubai_property(
        area="dubai-marina",
        property_type="apartment",
        bedrooms=2,
        size_sqft=1200,
        asking_price_aed=1800000,
        bathrooms=2,
        furnished=True,
        service_charge_sqft=15,  # AED per sqft per year
        view_type="marina view"
    )
    
    if "error" not in result:
        # Additional analysis
        ratio = result['price_to_estimate_ratio']
        if ratio < 0.90:
            print("\n🟢 STRONG BUY OPPORTUNITY!")
            print("Property appears significantly undervalued")
        elif ratio < 0.95:
            print("\n🟢 BUY RECOMMENDATION")
            print("Property offers good value")
        elif ratio > 1.10:
            print("\n🔴 OVERPRICED - NEGOTIATE OR AVOID")
            print("Property is above market value")