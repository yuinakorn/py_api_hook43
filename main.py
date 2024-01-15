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
            try:
                list_table = json.load(file)
            except json.JSONDecodeError as json_error:
                error = f"Error decoding JSON: {json_error}"
                print(error)
                # Handle the error or return, depending on your requirements
                raise

            for table in list_table:
                print(table)
                urls = f"{url}/items/{table}"
                print(urls)

                try:
                    response = requests.request("POST", urls, headers={'Authorization': f'Bearer {token}'}, data={})
                    response.raise_for_status()
                except requests.RequestException as request_error:
                    error = f"Error making request: {request_error}"
                    print(error)
                    # Handle the error or return, depending on your requirements
                    raise

                # Check if the response contains valid JSON before trying to parse it
                try:
                    response_json = response.json()
                except json.JSONDecodeError:
                    error = "Error decoding response JSON. Response may not be valid JSON or empty."
                    print(error)
                    response_json = None  # Set to None or handle accordingly

                res_data = {
                    "hcode": name,
                    "table": table,
                    "method": "replace",
                    "data": response_json  # Use the parsed JSON, or None if decoding error
                }

                fw_payload = json.dumps(res_data)
                fw_url = config_env['SEND_CLEFT_CMU']

                try:
                    response = requests.request("POST", fw_url, headers={'Content-Type': 'application/json'},
                                                data=fw_payload)
                    response.raise_for_status()
                except requests.RequestException as request_error:
                    error = f"Error making forwarding request: {request_error}"
                    print(error)
                    # Handle the error or return, depending on your requirements
                    raise

                print(response.text)

    except FileNotFoundError:
        print("File 'tables.json' not found.")
    except Exception as e:
        print(f"Unexpected error: {e}")

    print("End at: " + thai_time.strftime('%Y-%m-%d %H:%M:%S'))


@app.post("/hook")
async def send_hook():
    # import json file
    items = {}
    i = 0
    try:
        print("Start hook")
        with open("connection.json", "r") as file:
            print("Read connection.json")

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

    except requests.RequestException as e:
        error = f"Error in try func hook(): {e}"
        print(error)
        return error


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    asyncio.run(send_hook())
    print("Main program continues executing...")
