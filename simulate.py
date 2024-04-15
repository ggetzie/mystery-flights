from collections import defaultdict
import csv
import json
import pathlib
import random

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
        routes = defaultdict(list)
        rows = list(reader)

    for row in rows:
        # only nonstop flights to and from airports we have info for
        if (
            row["stops"] == "0"
            and row["source_airport"] in airports
            and row["destination_airport"] in airports
        ):
            routes[row["source_airport"]].append(row["destination_airport"])
    for key, value in routes.items():
        # remove duplicates and sort the list
        routes[key] = sorted(list(set(value)))
    # remove empty values
    routes = {key: value for key, value in routes.items() if value}
    routes_file_json.write_text(json.dumps(routes, indent=2), encoding="utf-8")
    return routes


AIRPORTS = get_airport_codes()
ROUTES = get_routes()
DEFAULT_MAX_FLIGHTS = 36525
DEFAULT_TRIALS = 10000


def get_mystery_flight(source_airport):
    # return a random destination airport from the list of possible destinations
    return random.choice(ROUTES[source_airport])


def fly_home(start_airport, max_flights=DEFAULT_MAX_FLIGHTS):

    next_airport = get_mystery_flight(start_airport)
    visited = [start_airport, next_airport]
    flights = 1
    while next_airport != start_airport and flights < max_flights:
        try:
            next_airport = get_mystery_flight(next_airport)
        except KeyError:
            # we reached a dead end
            break
        visited.append(next_airport)
        if next_airport == start_airport:
            break
        flights += 1
    return visited


def get_paths(start_airport="IAD", trials=DEFAULT_TRIALS):
    return [fly_home(start_airport) for _ in range(trials)]


def path_stats(paths):
    dead_ends = 0
    didnt_finish = 0
    lengths = []
    for path in paths:
        if path[-1] != path[0]:
            if len(path) < DEFAULT_MAX_FLIGHTS + 1:
                dead_ends += 1
            else:
                didnt_finish += 1
        else:
            lengths.append(len(path))
    return {
        "dead_ends": dead_ends,
        "didnt_finish": didnt_finish,
        "shortest": min(lengths),
        "longest": max(lengths),
        "average": sum(lengths) / len(lengths),
    }


def get_all_paths_stats():
    res = {}
    count = 0
    airports = [airport for airport in AIRPORTS if airport in ROUTES]
    total = len(airports)
    for airport in airports:
        paths = get_paths(airport)
        stats = path_stats(paths)
        res[airport] = stats
        count += 1
        print(
            f"Processed {count} of {total} airports {(count/total)*100:.2f}% complete",
            end="\r",
        )
    with open("data/all_stats.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    return res
