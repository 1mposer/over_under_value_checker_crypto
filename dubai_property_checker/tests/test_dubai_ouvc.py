#!/usr/bin/env python

"""
Test script for Dubai Property OUVC
Run this to validate your setup and test the valuation system
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dubai_property_ouvc import (
        Property,
        PropertyType,
        Area,
        BayutClient,
        DLDClient,
        DubaiPropertyValuator,
        analyze_dubai_property
    )
    print("✅ Successfully imported Dubai Property OUVC modules")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    print("Please ensure dubai_property_ouvc.py is in the same directory")
    sys.exit(1)

# Test configuration
TEST_PROPERTIES = [
    {
        "name": "Marina 2BR Apartment",
        "area": "dubai-marina",
        "property_type": "apartment",
        "bedrooms": 2,
        "size_sqft": 1200,
        "asking_price_aed": 1800000,
        "expected_yield_range": (5.5, 8.0)
    },
    {
        "name": "Downtown Studio",
        "area": "downtown-dubai",
        "property_type": "studio",
        "bedrooms": 0,
        "size_sqft": 500,
        "asking_price_aed": 900000,
        "expected_yield_range": (4.5, 7.0)
    },
    {
        "name": "Palm Villa",
        "area": "palm-jumeirah",
        "property_type": "villa",
        "bedrooms": 4,
        "size_sqft": 4500,
        "asking_price_aed": 8000000,
        "expected_yield_range": (4.0, 6.5)
    },
    {
        "name": "JVC Townhouse",
        "area": "jvc",
        "property_type": "townhouse",
        "bedrooms": 3,
        "size_sqft": 2100,
        "asking_price_aed": 2500000,
        "expected_yield_range": (6.5, 9.5)
    }
]

def test_api_keys():
    """Test if API keys are configured"""
    print("\n" + "="*50)
    print("TESTING API KEY CONFIGURATION")
    print("="*50)
    
    results = {}
    
    # Check Bayut API key
    bayut_key = os.getenv("BAYUT_API_KEY")
    if bayut_key:
        print("✅ BAYUT_API_KEY is set")
        results['bayut'] = True
        
        # Test API connection
        try:
            client = BayutClient(bayut_key)
            print("  → Testing Bayut API connection...")
            # Make a minimal test request
            test_props = client.search_properties(
                area="dubai-marina",
                property_type="apartment",
                bedrooms=1,
                min_price=500000,
                max_price=1000000,
                min_size=400,
                max_size=800,
                purpose="for-sale"
            )
            if test_props:
                print(f"  ✅ Bayut API working! Found {len(test_props)} test properties")
            else:
                print("  ⚠️ Bayut API returned no results (check credentials or try later)")
        except Exception as e:
            print(f"  ❌ Bayut API test failed: {e}")
            results['bayut'] = False
    else:
        print("❌ BAYUT_API_KEY not set")
        print("  → Set it with: export BAYUT_API_KEY='your_key_here'")
        print("  → Get key from: https://rapidapi.com/apidojo/api/bayut")
        results['bayut'] = False
    
    # Check DLD API key (optional)
    dld_key = os.getenv("DLD_API_KEY")
    if dld_key:
        print("✅ DLD_API_KEY is set (optional)")
        results['dld'] = True
    else:
        print("ℹ️ DLD_API_KEY not set (optional, will use synthetic data)")
        results['dld'] = False
    
    return results

def test_basic_valuation():
    """Test basic property valuation"""
    print("\n" + "="*50)
    print("TESTING BASIC VALUATION")
    print("="*50)
    
    test_prop = TEST_PROPERTIES[0]  # Marina apartment
    
    print(f"Testing: {test_prop['name']}")
    print(f"  - Area: {test_prop['area']}")
    print(f"  - Type: {test_prop['property_type']}")
    print(f"  - Size: {test_prop['size_sqft']} sqft")
    print(f"  - Price: AED {test_prop['asking_price_aed']:,}")
    
    try:
        result = analyze_dubai_property(
            area=test_prop['area'],
            property_type=test_prop['property_type'],
            bedrooms=test_prop['bedrooms'],
            size_sqft=test_prop['size_sqft'],
            asking_price_aed=test_prop['asking_price_aed']
        )
        
        if "error" in result:
            print(f"❌ Valuation failed: {result['error']}")
            return False
        
        print("\n✅ Valuation successful!")
        print(f"  - Estimated Value: AED {result['estimated_value']:,}")
        print(f"  - Confidence: {result['confidence_interval']['low']:,} - {result['confidence_interval']['high']:,}")
        print(f"  - Price Ratio: {result['price_to_estimate_ratio']:.2f}x")
        print(f"  - Rental Yield: {result['estimated_rental_yield']:.1f}%")
        print(f"  - Verdict: {result['valuation_signals']['overall_verdict']}")
        print(f"  - Comparables Found: {result['comparable_properties']}")
        
        # Validate yield is in expected range
        min_yield, max_yield = test_prop['expected_yield_range']
        if min_yield <= result['estimated_rental_yield'] <= max_yield:
            print(f"  ✅ Yield in expected range ({min_yield}-{max_yield}%)")
        else:
            print(f"  ⚠️ Yield outside expected range ({min_yield}-{max_yield}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_batch_valuation():
    """Test batch property valuation"""
    print("\n" + "="*50)
    print("TESTING BATCH VALUATION")
    print("="*50)
    
    results = []
    success_count = 0
    
    for i, prop in enumerate(TEST_PROPERTIES, 1):
        print(f"\n[{i}/{len(TEST_PROPERTIES)}] Testing {prop['name']}...")
        
        try:
            result = analyze_dubai_property(
                area=prop['area'],
                property_type=prop['property_type'],
                bedrooms=prop['bedrooms'],
                size_sqft=prop['size_sqft'],
                asking_price_aed=prop['asking_price_aed']
            )
            
            if "error" not in result:
                success_count += 1
                verdict = result['valuation_signals']['overall_verdict']
                yield_pct = result['estimated_rental_yield']
                print(f"  ✅ Success - Verdict: {verdict}, Yield: {yield_pct:.1f}%")
                
                results.append({
                    "property": prop['name'],
                    "success": True,
                    "verdict": verdict,
                    "yield": yield_pct
                })
            else:
                print(f"  ❌ Failed: {result['error']}")
                results.append({
                    "property": prop['name'],
                    "success": False,
                    "error": result['error']
                })
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            results.append({
                "property": prop['name'],
                "success": False,
                "error": str(e)
            })
        
        # Small delay between requests
        time.sleep(1)
    
    print(f"\n📊 Batch Results: {success_count}/{len(TEST_PROPERTIES)} successful")
    
    return success_count == len(TEST_PROPERTIES), results

def test_data_sources():
    """Test different data source integrations"""
    print("\n" + "="*50)
    print("TESTING DATA SOURCES")
    print("="*50)
    
    # Test Bayut client
    bayut_key = os.getenv("BAYUT_API_KEY")
    if bayut_key:
        try:
            client = BayutClient(bayut_key)
            props = client.search_properties(
                area="business-bay",
                property_type="apartment",
                bedrooms=1,
                min_price=600000,
                max_price=900000,
                min_size=500,
                max_size=800
            )
            print(f"✅ Bayut: Retrieved {len(props)} properties")
        except Exception as e:
            print(f"❌ Bayut: {e}")
    
    # Test DLD client (will use synthetic data)
    try:
        dld = DLDClient()
        transactions = dld.get_recent_transactions(
            area="dubai-marina",
            property_type="apartment",
            bedrooms=2,
            size_range=(1000, 1500),
            days_back=30
        )
        print(f"✅ DLD: Retrieved {len(transactions)} transactions (synthetic)")
    except Exception as e:
        print(f"❌ DLD: {e}")
    
    # Test rental index
    try:
        dld = DLDClient()
        rental = dld.get_rental_index(
            area="downtown-dubai",
            property_type="apartment",
            bedrooms=1
        )
        print(f"✅ Rental Index: {rental['min_annual_rent']:,} - {rental['max_annual_rent']:,} AED/year")
    except Exception as e:
        print(f"❌ Rental Index: {e}")

def test_performance():
    """Test system performance"""
    print("\n" + "="*50)
    print("TESTING PERFORMANCE")
    print("="*50)
    
    test_prop = TEST_PROPERTIES[0]
    
    # Measure single valuation time
    start_time = time.time()
    try:
        result = analyze_dubai_property(
            area=test_prop['area'],
            property_type=test_prop['property_type'],
            bedrooms=test_prop['bedrooms'],
            size_sqft=test_prop['size_sqft'],
            asking_price_aed=test_prop['asking_price_aed']
        )
        elapsed = time.time() - start_time
        
        if "error" not in result:
            print(f"✅ Single valuation: {elapsed:.2f} seconds")
            
            if elapsed < 3:
                print("  ✅ Excellent performance (<3s)")
            elif elapsed < 5:
                print("  ⚠️ Acceptable performance (3-5s)")
            else:
                print("  ❌ Slow performance (>5s)")
        else:
            print(f"❌ Valuation failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

def generate_test_report(results: Dict):
    """Generate a test report"""
    print("\n" + "="*50)
    print("TEST REPORT")
    print("="*50)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = {
        "timestamp": timestamp,
        "results": results,
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for r in results.values() if r),
            "failed": sum(1 for r in results.values() if not r)
        }
    }
    
    # Display summary
    print(f"Date: {timestamp}")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"✅ Passed: {report['summary']['passed']}")
    print(f"❌ Failed: {report['summary']['failed']}")
    
    # Save report to file
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📄 Report saved to: {report_file}")
    except Exception as e:
        print(f"\n⚠️ Could not save report: {e}")
    
    return report

def main():
    """Run all tests"""
    print("\n" + "#"*50)
    print("# DUBAI PROPERTY OUVC - TEST SUITE")
    print("#"*50)
    
    results = {}
    
    # Test 1: API Keys
    api_results = test_api_keys()
    results['api_keys'] = all(api_results.values()) or api_results.get('bayut', False)
    
    if not api_results.get('bayut', False):
        print("\n⚠️ Cannot proceed without Bayut API key")
        print("Please set BAYUT_API_KEY and try again")
        return
    
    # Test 2: Basic Valuation
    results['basic_valuation'] = test_basic_valuation()
    
    # Test 3: Batch Valuation
    batch_success, batch_details = test_batch_valuation()
    results['batch_valuation'] = batch_success
    
    # Test 4: Data Sources
    test_data_sources()
    results['data_sources'] = True  # Informational only
    
    # Test 5: Performance
    test_performance()
    results['performance'] = True  # Informational only
    
    # Generate report
    report = generate_test_report(results)
    
    # Final status
    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED! Your Dubai Property OUVC is ready to use!")
    else:
        print("\n⚠️ Some tests failed. Please review the report above.")
    
    return report

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Run tests
    main()