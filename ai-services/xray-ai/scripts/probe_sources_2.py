import urllib.request
import ssl

ctx = ssl.create_default_context()

def check_url(url, name):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            print(f"[{name}] HTTP {resp.status} - {resp.getheader('Content-Type')}")
            content = resp.read(1000).decode('utf-8', errors='ignore')
            print(f"[{name}] Sample: {content[:200]}...\n")
    except Exception as e:
        print(f"[{name}] Failed: {e}\n")

if __name__ == "__main__":
    check_url("https://stanfordmlgroup.github.io/competitions/mura/", "MURA Stanford ML")
    check_url("https://aimi.stanford.edu/datasets/mura-msk-xrays", "MURA AIMI")
    check_url("https://physionet.org/content/vindr-cxr/1.0.0/", "VinDr-CXR PhysioNet")
    check_url("https://github.com/vinbigdata-medical/vindr-cxr", "VinDr-CXR GitHub")
