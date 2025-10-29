import sys

def main():
    print("OUVC - Objective Undervalue Checker")
    print("1. Crypto Checker")
    print("2. Dubai Property Checker")
    
    choice = input("Select (1/2): ")
    
    if choice == "1":
        import over_under_value_checker.app as crypto_app
        crypto_app.run()
    elif choice == "2":
        import dubai_property_checker.dubai_property_app as property_app
        property_app.run()

if __name__ == "__main__":
    main()