import urllib.request
import ssl

proxy = 'http://brd-customer-hl_45763da0-zone-grocery_ghost:hez83y11cjt6@brd.superproxy.io:33335'
url = 'https://geo.brdtest.com/welcome.txt?product=unlocker&method=native'

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({'https': proxy, 'http': proxy}),
    urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
)

try:
    print(opener.open(url).read().decode())
except Exception as e:
    print(f"Error: {e}")
