import urllib.request
import re
import ssl

ctx = ssl.create_default_context()

def analyze_mura():
    req = urllib.request.Request("https://stanfordmlgroup.github.io/competitions/mura/", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print("=== MURA Competition Page ===")
        # Find download links or forms
        links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        for l in links:
            if 'download' in l.lower() or 'mura' in l.lower() or 'form' in l.lower():
                print("Link:", l)
        forms = re.findall(r'<form[^>]*>(.*?)</form>', html, re.DOTALL)
        print(f"Forms found: {len(forms)}")

def analyze_vindr():
    req = urllib.request.Request("https://physionet.org/content/vindr-cxr/1.0.0/", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print("\n=== VinDr-CXR PhysioNet Page ===")
        # Look for access policy / credentialing
        for match in re.findall(r'<p>.*?(?:access|credential|license|training|DUA).*?</p>', html, re.IGNORECASE):
            print("Access info:", match[:300])

if __name__ == "__main__":
    analyze_mura()
    analyze_vindr()
