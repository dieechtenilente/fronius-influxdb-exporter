import json
from time import sleep
from datetime import datetime
import argparse

from requests import get
from urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ConnectTimeout
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.write_api import SYNCHRONOUS

# Variables
SLEEP = 60
API_TIMEOUT = 30

# Parse Parameters

# Set up the argument parser
parser = argparse.ArgumentParser(description="Script to interact with InfluxDB.")

# Adding the command line arguments
parser.add_argument("--froniusIP", type=str, help="IP of the Fronius inverter.")
parser.add_argument("--plantName", type=str, help="Name of plant/inverter.")
parser.add_argument("--InfluxDBserver", type=str, help="InfluxDB server address.")
parser.add_argument("--InfluxDBtoken", type=str, help="InfluxDB token.")
parser.add_argument("--InfluxDBorg", type=str, help="InfluxDB organization.")
parser.add_argument("--InfluxDBbucket", type=str, help="InfluxDB bucket.")

# Parse the arguments
args = parser.parse_args()

# Access the command line arguments
froniusIP = args.froniusIP
plantName = args.plantName
InfluxDBserver = args.InfluxDBserver
InfluxDBorg = args.InfluxDBorg
InfluxDBtoken = args.InfluxDBtoken
InfluxDBbucket = args.InfluxDBbucket

print(f"froniusIP: {froniusIP}")
print(f"plantName: {plantName}")
print(f"InfluxDBserver: {InfluxDBserver}")
print(f"InfluxDBorg: {InfluxDBorg}")
print(f"InfluxDBtoken: {InfluxDBtoken}")
print(f"InfluxDBbucket: {InfluxDBbucket}")

# Define array
responses = []
connection_metrics = [
    {
            "name": "fronius_inverter_1_statuscode",
            "endpoint": "solar_api/v1/GetInverterInfo.cgi",
            "json_search_string": ["Body", "Data", "1", "StatusCode"],
            "protocol": "http"
    },
    {
            "name": "fronius_inverter_1_day_energy",
            "endpoint": "solar_api/v1/GetInverterRealtimeData.cgi",
            "json_search_string": ["Body", "Data", "DAY_ENERGY", "Values", "1"],
            "protocol": "http"
    },
    {
            "name": "fronius_inverter_1_PAC",
            "endpoint": "solar_api/v1/GetInverterRealtimeData.cgi",
            "json_search_string": ["Body", "Data", "PAC", "Values", "1"],
            "protocol": "http"
    },
    {
            "name": "fronius_inverter_1_total_energy",
            "endpoint": "solar_api/v1/GetInverterRealtimeData.cgi",
            "json_search_string": ["Body", "Data", "TOTAL_ENERGY", "Values", "1"],
            "protocol": "http"
    },

]


# Fetching function
def fetch_data():
    # Create InfluxDB Client
    client = InfluxDBClient(url=f"https://{InfluxDBserver}/", token=InfluxDBtoken, org=InfluxDBorg)

    # Loop over metrics
    for connection_metric in connection_metrics:
        name = connection_metric.get("name")
        endpoint = connection_metric.get("endpoint")
        json_search_string = connection_metric.get("json_search_string")
        protocol = connection_metric.get("protocol")

        # Call endpoint
        try:
            r = get(f"{protocol}://{froniusIP}/{endpoint}", timeout=API_TIMEOUT)
            sc = r.status_code

            if sc in [200]:
                # Parse response to json object
                json_object = json.loads(r.text)

                # Parse the json search string and get value
                for key in json_search_string:
                    json_object = json_object[key]

                if json_object != None:
                    print(f"Set metric {name} to {json_object}")
                    p = Point(plantName).tag("address", name).field("value", float(json_object))

                    with client.write_api(write_options=SYNCHRONOUS) as writer:
                        try:
                            writer.write(bucket=InfluxDBbucket, record=[p])
                            print("Wrote " +(str(p)) + " to influxdb")

                        except InfluxDBError as e:
                            print(e)
                        except ReadTimeoutError as e:
                            print("Read timeout" + e)
            else:
                print(f"{protocol}://{froniusIP}/{endpoint} returns status code {sc}!")
        except ConnectTimeout:
            print(f"{protocol}://{froniusIP}/{endpoint} is unreachable!")
        except ValueError:
            print(f"{protocol}://{froniusIP}/{endpoint} returns no json!")
        except KeyError:
            print(f"{protocol}://{froniusIP}/{endpoint} is no valid endpoint!")

    # Close InfluxDB client
    client.close()

while True:
    print(str(datetime.now()) + " - Fetching data")
    fetch_data()

    # TODO: Make this pretty and maybe adjustable
    now = datetime.now()

    sunset = now.replace(hour=22, minute=00, second=0, microsecond=0)
    sunrise = now.replace(hour=4, minute=30, second=0, microsecond=0)

    if datetime.now() >= sunset or datetime.now() < sunrise:
        print(str(datetime.now()) + " - Wait for " + 3600 + " seconds.")
        sleep(3600)
    else:
        print(str(datetime.now()) + " - Wait for " + str(SLEEP) + " seconds.")
        sleep(SLEEP)

    

