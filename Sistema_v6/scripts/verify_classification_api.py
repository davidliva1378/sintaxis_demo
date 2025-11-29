
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_get_rules():
    print("\n--- Testing GET /classification/rules ---")
    try:
        response = requests.get(f"{BASE_URL}/classification/rules")
        if response.status_code == 200:
            rules = response.json()
            print(f"✅ Success! Retrieved {len(rules)} rules.")
            # Print first rule as sample
            if rules:
                print(f"Sample rule: {rules[0]['tipo']}")
            return rules
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_classification(text):
    print(f"\n--- Testing POST /classification/test with text: '{text[:30]}...' ---")
    try:
        payload = {"texto": text}
        response = requests.post(f"{BASE_URL}/classification/test", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Result: {result['tipo']} (Conf: {result['confianza']})")
            print(f"Method: {result.get('metodo', 'unknown')}")
            return result
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_update_rules(current_rules):
    print("\n--- Testing POST /classification/rules (Adding a test rule) ---")
    if not current_rules:
        print("Skipping update test because GET failed.")
        return

    # Add a test rule
    new_rule = {
        "tipo": "TEST_RULE",
        "patrones": [{"texto": "patron de prueba unico 12345", "confianza": 0.99}]
    }
    updated_rules = current_rules + [new_rule]
    
    try:
        response = requests.post(f"{BASE_URL}/classification/rules", json={"rules": updated_rules})
        if response.status_code == 200:
            print("✅ Success! Rules updated.")
            
            # Verify it works
            test_classification("Este es un patron de prueba unico 12345 para verificar.")
            
            # Revert changes
            print("\n--- Reverting changes ---")
            requests.post(f"{BASE_URL}/classification/rules", json={"rules": current_rules})
            print("✅ Changes reverted.")
        else:
            print(f"❌ Failed to update: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Verifying Classification API...")
    rules = test_get_rules()
    
    # Test existing rule
    test_classification("VISTOS: ... RESUELVO: Hacer lugar a la demanda. SENTENCIA DEFINITIVA.")
    
    # Test update
    if rules:
        test_update_rules(rules)
