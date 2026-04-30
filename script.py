import requests

token = "cvs_iYcVsTDVud3envaHh0D-QthlCj3Lld24ed99iUKBh6Y"

url = "http://127.0.0.1:5000/api/certificates"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

data = {
    "event": "FTMPC",
    "verification_code": "",
    "name": "Black Doe",
    "institution": "ABC Institute",
    "segment": "",
    "cert_type": "participation",
    "prize_place": "1st",
    "installment": "5.0"
}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.text)