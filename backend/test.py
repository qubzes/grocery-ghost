import requests
from urllib.parse import urlparse


def test_url_normalization():
    # Example URL to test
    url = "http://www.theprimejnr.com/some/path"

    # Proxy configuration
    PROXY = "http://brd-customer-hl_3bfca4c1-zone-grocery_ghost:o7hhz0cwt588@brd.superproxy.io:33335"
    proxies = {"http": PROXY, "https": PROXY}

    try:
        response = requests.get(url, allow_redirects=True, proxies=proxies)

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

    except requests.RequestException as e:
        print(f"Error making request: {e}")


if __name__ == "__main__":
    test_url_normalization()
