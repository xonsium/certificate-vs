import requests

token = "cvs_r-hfGDlXsVpPR0wbWXFBM3XANJ3k6y2HKKXn3BUQjLg"

url = "http://127.0.0.1:5000/api/certificates"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

data = {
    "event": "INIT",
    "verification_code": "",
    "name": "Black Doe",
    "institution": "ABC Institute",
    "segment": "Tech Quiz",
    "prize_place": "1st",
    "installment": "5.0"
}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.text)