from fastapi import FastAPI
import json
import requests
import asyncio

app = FastAPI()


def call_api_table(token: str, url: str):
    with open("tables.json", "r") as file:
        list_table = json.load(file)
        for table in list_table:
            print(table)
            urls = f"{url}/items/{table}"
            print(urls)

            payload = {}
            headers = {
                'Authorization': f'Bearer {token}',
            }

            response = requests.request("POST", urls, headers=headers, data=payload)

            print(response.text)


@app.post("/hook")
async def send_hook():
    # import json file
    with open("connection.json", "r") as file:
        json_data = json.load(file)

    for item in json_data:
        url = item['url'] + f":{item['port']}"
        urls = item['url'] + f":{item['port']}/token"
        username = item['username']
        password = item['password']
        payload = f'username={username}&password={password}'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = requests.post(urls, headers=headers, data=payload)
            response_json = response.json()
            call_api_table(response_json["access_token"], url)
        except requests.RequestException as e:
            response_json = f"Error: {e}"

        print(response_json)

    return json_data


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    asyncio.run(send_hook())
    print("Main program continues executing...")