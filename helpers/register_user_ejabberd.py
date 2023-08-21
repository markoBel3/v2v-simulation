import requests

def register_user(username, password):
    url = 'http://localhost:5280/api/register'
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "user": username,
        "host": "localhost",
        "password": password
    }

    response = requests.post(url, headers=headers, json=data, verify=False)

if __name__ == '__main__':
    register_user("car40","pass40")