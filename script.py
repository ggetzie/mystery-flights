from collections import defaultdict
import csv
import json
import pathlib


routes_file = pathlib.Path("data/flight_routes.csv")
airports_file = pathlib.Path("data/airports.csv")
airports_file_json = pathlib.Path("data/airports.json")
routes_file_json = pathlib.Path("data/flight_routes.json")


def get_airport_codes():
    # organize the airports data into a dictionary indexed by IATA code
    # ignore airports without an IATA code
    if airports_file_json.exists():
        with airports_file_json.open(encoding="utf-8") as f:
            return json.load(f)

    with airports_file.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        res = {
            row["iata_code"]: {
                "name": row["name"],
                "latitude_deg": row["latitude_deg"],
                "longitude_deg": row["longitude_deg"],
            }
            for row in reader
            if row["iata_code"]
        }
        airports_file_json.write_text(json.dumps(res, indent=2), encoding="utf-8")
        return res


def get_routes():
    # organize the flight route data into a dictionary of
    # source airport -> list of possible destination airports
    airports = get_airport_codes()
    if routes_file_json.exists():
        with routes_file_json.open(encoding="utf-8") as f:
            return json.load(f)

    with routes_file.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        res = defaultdict(list)
        for row in reader:
            # only nonstop flights to and from airports we have info for
            if (
                row["stops"] == "0"
                and row["source_airport"] in airports
                and row["destination_airport"] in airports
            ):
                res[row["source_airport"]].append(row["destination_airport"])
        routes_file_json.write_text(json.dumps(res, indent=2), encoding="utf-8")
        return res
