import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
req = urllib.request.Request('https://stanfordmlgroup.github.io/competitions/mura/', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')

print("=== MURA Page Links ===")
for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL):
    href, text = match.group(1), match.group(2).strip()
    if any(k in href.lower() or k in text.lower() for k in ['download', 'dataset', 'data', 'register', 'competitions', 'google']):
        print(f"Text: {text} -> {href}")

print("\n=== MURA Page Scripts ===")
for script in re.finditer(r'<script[^>]*>(.*?)</script>', html, re.DOTALL):
    s = script.group(1)
    if 'dataset' in s.lower() or 'mura' in s.lower() or 'download' in s.lower():
        print("Script match:", s[:300])
