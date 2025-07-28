from urllib.parse import urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_url_normalization():
    # Example URL to test
    url = "https://www.kingsfoodmarkets.com/shop/product-details.148010437.html"

    # Proxy configuration
    PROXY = "http://brd-customer-hl_3bfca4c1-zone-grocery_ghost:o7hhz0cwt588@brd.superproxy.io:33335"
    proxies = {"http": PROXY, "https": PROXY}

    try:
        response = requests.get(
            url, allow_redirects=True, proxies=proxies, verify=False
        )

        # Get the final URL: Prefer the custom header if present, else fall back to response.url
        final_url = response.headers.get("x-unblocker-redirected-to", response.url)

        # Parse the final URL
        parsed = urlparse(final_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        netloc = parsed.netloc

        # Print the formatted result
        print(
            f"Normalized URL: {base_url} (Netloc: {netloc}), from {url}), final URL: {final_url}"
        )
        print(f"Request made through proxy: {PROXY}")

        # Optional: Print all headers for debugging (to confirm the custom header)
        print("Response Headers:", response.headers)

        # Print response content
        print("\nResponse Content:")
        print(response.text)

    except requests.RequestException as e:
        print(f"Error making request: {e}")


if __name__ == "__main__":
    test_url_normalization()
