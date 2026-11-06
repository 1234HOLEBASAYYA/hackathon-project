import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
req = urllib.request.Request("https://physionet.org/content/vindr-cxr/1.0.0/", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, context=ctx) as r:
    html = r.read().decode('utf-8', errors='ignore')
    # search for license or access policy
    m = re.findall(r'<div class="access-policy.*?>.*?</div>', html, re.DOTALL)
    for item in m:
        print("Access policy:", item)
    # search for "Open" or "Credentialed" or "DUA" or "PhysioNet Credentialed"
    m2 = re.findall(r'<h3>Access Policy</h3>.*?(?=<h3>)', html, re.DOTALL)
    for item in m2:
        print("Access Policy Block:\n", item)
