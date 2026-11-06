import requests

pages = ["/", "/index.html", "/prescription.html", "/xray.html", "/ct-scan.html", "/dashboard.html"]
assets = ["/css/main.css", "/css/components.css", "/js/api.js", "/js/patient-manager.js", "/js/app.js", "/js/prescription-client.js", "/js/xray-client.js", "/js/ct-client.js"]

all_passed = True
print("--- TESTING PAGES ---", flush=True)
for p in pages:
    r = requests.get(f"http://127.0.0.1:3000{p}", timeout=5)
    status = "OK" if r.status_code == 200 else "FAIL"
    if r.status_code != 200: all_passed = False
    print(f"Page {p:20} -> {status} ({r.status_code}, Length: {len(r.text)})", flush=True)

print("\n--- TESTING ASSETS ---", flush=True)
for a in assets:
    r = requests.get(f"http://127.0.0.1:3000{a}", timeout=5)
    status = "OK" if r.status_code == 200 else "FAIL"
    if r.status_code != 200: all_passed = False
    print(f"Asset {a:25} -> {status} ({r.status_code}, Length: {len(r.text)})", flush=True)

print("\n--- TESTING API ENDPOINTS ---", flush=True)
endpoints = [
    ("/api/health", "GET"),
    ("/api/reports/stats", "GET"),
    ("/api/patients", "GET"),
    ("/api/patients/P-1001/timeline", "GET"),
    ("/api/analysis/prescription/history/P-1001", "GET")
]

for ep, method in endpoints:
    r = requests.request(method, f"http://127.0.0.1:3000{ep}", timeout=5)
    status = "OK" if r.status_code == 200 else "FAIL"
    if r.status_code != 200: all_passed = False
    print(f"API {method} {ep:35} -> {status} ({r.status_code})", flush=True)

print("\nSummary: ALL PASSED" if all_passed else "\nSummary: FAILURES DETECTED", flush=True)
