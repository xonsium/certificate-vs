import requests

token = ""

url = "http://127.0.0.1:5000/api/certificates"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

data = {
    "event": "FTMPC",
    "verification_code": "",
    "name": "John Doe",
    "institution": "ABC Institute",
    "segment": "Programming",
    "prize_place": "2nd",
    "installment": "2026"
}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.text)