import requests
import json

# Test evacuation centers endpoint
print("Testing /api/evacuation-centers endpoint...")
try:
    response = requests.get('http://127.0.0.1:5000/api/evacuation-centers')
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        centers = response.json()
        print(f"\nTotal evacuation centers returned: {len(centers)}")
        
        if centers:
            print(f"\nFirst 5 centers:")
            for center in centers[:5]:
                print(f"  - {center['name']} at ({center['latitude']:.4f}, {center['longitude']:.4f})")
            
            # Check geographic distribution
            lats = [c['latitude'] for c in centers]
            lngs = [c['longitude'] for c in centers]
            print(f"\nGeographic coverage:")
            print(f"  Latitude range: {min(lats):.4f} to {max(lats):.4f}")
            print(f"  Longitude range: {min(lngs):.4f} to {max(lngs):.4f}")
        else:
            print("No centers returned!")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")
