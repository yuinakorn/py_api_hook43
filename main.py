from datetime import datetime, timezone

from fastapi import FastAPI
import json
import requests
import asyncio
import pytz
from dotenv import dotenv_values

config_env = dotenv_values(".env")

app = FastAPI()


async def call_api_table_async(token: str, url: str, name: str):
    # print time now at tz Asia/Bangkok

    time = datetime.now()
    tz = pytz.timezone('Asia/Bangkok')
    thai_time = time.astimezone(tz)
    print("Start at: ", thai_time.strftime('%Y-%m-%d %H:%M:%S'))

    try:
        with open("tables.json", "r") as file:
            list_table = json.load(file)
            for table in list_table:
                print(table)
                urls = f"{url}/items/{table}"
                print(urls)

                response = requests.request("POST", urls, headers={'Authorization': f'Bearer {token}'}, data={})

                res_data = {
                    "hcode": name,
                    "table": table,
                    "method": "replace",
                    "data": response.json()
                }
                # print get data
                # print(res_data)

                # forwarding data to api receiver
                fw_payload = json.dumps(res_data)
                fw_url = config_env['SEND_CLEFT_CMU']
                response = requests.request("POST", fw_url, headers={'Content-Type': 'application/json'}, data=fw_payload)

                print(response.text)
    except requests.RequestException as e:
        error = f"Error: {e}"
        print(error)
        return error

    print("End at: " + thai_time.strftime('%Y-%m-%d %H:%M:%S'))


@app.post("/hook")
async def send_hook():
    # import json file
    items = {}
    i = 0
    with open("connection.json", "r") as file:
        json_data = json.load(file)

    for item in json_data:
        i += 1
        urli = "url" + str(i)
        url = item['url'] + f":{item['port']}"
        urls = item['url'] + f":{item['port']}/token"
        username = item['username']
        password = item['password']
        name = item['name']
        payload = f'username={username}&password={password}'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = requests.post(urls, headers=headers, data=payload)
            response_json = response.json()
            # call_api_table(response_json["access_token"], url)
            asyncio.create_task(call_api_table_async(response_json["access_token"], url, name))
        except requests.RequestException as e:
            error = f"Error in func hook(): {e}"
            print(error)
            return error

        items[urli] = url

    return {"urls": items, "status": "success", "message": "an api is running in background"}


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    asyncio.run(send_hook())
    print("Main program continues executing...")

