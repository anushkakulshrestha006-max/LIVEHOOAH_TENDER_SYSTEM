import requests

url = "https://kinfra.org/wp-content/uploads/2013/04/Tender-documet-Modified-Structural-Consultant-1.pdf"

response = requests.get(
    url,
    timeout=30
)

print("STATUS:", response.status_code)
print("CONTENT TYPE:", response.headers.get("content-type"))
print("SIZE:", len(response.content))