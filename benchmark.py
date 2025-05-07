import requests
import time
import random
import json
import concurrent.futures
import statistics
import matplotlib.pyplot as plt
from collections import defaultdict
import sys

# --- Configuration ---
BASE_URL = "http://localhost:3001/api/postgres"
VALID_FEED_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 99, 100]
ITEM_COUNTS_TO_TEST = [1, 5, 10, 25, 50, 100, 200, 500, 1000]
REQUESTS_PER_COUNT = 1000
MAX_WORKERS = 20
REQUEST_TIMEOUT = 20

ENDPOINTS = {
    "redis": "random-redis-items",
    "postgres": "random-items",
    "postgres redis cache" : "random-items-cached"
}

if not VALID_FEED_IDS:
    print("ERROR: Please update the VALID_FEED_IDS list in the script with actual feed IDs.")
    sys.exit(1)

def fetch_response_time(endpoint_key, feed_id, item_count):
    """Makes a request and returns (endpoint_key, item_count, reported_took_ms) or None."""
    endpoint_path = ENDPOINTS[endpoint_key]
    url = f"{BASE_URL}/{endpoint_path}/{feed_id}/{item_count}"
    start_time = time.monotonic()
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        try:
            data = response.json()
            if 'took' in data:
                 reported_took_ms = float(data['took'])
            elif 'result' in data and 'took' in data['result']: # Check common nested structure
                 reported_took_ms = float(data['result']['took'])
            else:
                 # Attempt to find 'took' recursively (simple version)
                 found_took = None
                 def find_took(d):
                     nonlocal found_took
                     if isinstance(d, dict):
                         if 'took' in d:
                             found_took = d['took']
                             return True
                         for v in d.values():
                             if find_took(v): return True
                     elif isinstance(d, list):
                         for item in d:
                              if find_took(item): return True
                     return False

                 find_took(data)
                 if found_took is not None:
                      reported_took_ms = float(found_took)
                 else:
                      print(f"WARN: 'took' field not found in response JSON for {url}. Body: {data}")
                      return None # Cannot extract time

            request_duration = (time.monotonic() - start_time) * 1000 # Actual request time
            return (endpoint_key, item_count, reported_took_ms)

        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            print(f"ERROR: Failed to parse JSON or find 'took' for {url}. Error: {e}. Response text: {response.text[:200]}...")
            return None

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed for {url}. Error: {e}")
        return None
        print(f"ERROR: Unexpected error during request for {url}. Error: {e}")
        return None


# --- Main Execution ---
print("Starting benchmark...")
all_results = []
tasks_to_run = []

print("Generating tasks...")
for count in ITEM_COUNTS_TO_TEST:
    for i in range(REQUESTS_PER_COUNT):
        feed_id = random.choice(VALID_FEED_IDS) 
        for key in ENDPOINTS.keys():
            tasks_to_run.append((key, feed_id, count))

print(f"Total tasks to run: {len(tasks_to_run)}")

processed_tasks = 0
start_overall_time = time.monotonic()

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_task = {executor.submit(fetch_response_time, *task): task for task in tasks_to_run}

    for future in concurrent.futures.as_completed(future_to_task):
        task_args = future_to_task[future]
        processed_tasks += 1
        try:
            result = future.result()
            if result:
                all_results.append(result)
        except Exception as exc:
            print(f"ERROR: Task {task_args} generated an exception: {exc}")

        if processed_tasks % 50 == 0 or processed_tasks == len(tasks_to_run):
             elapsed_time = time.monotonic() - start_overall_time
             print(f"  Processed {processed_tasks}/{len(tasks_to_run)} tasks... ({elapsed_time:.2f}s elapsed)")


print(f"\nBenchmark finished. Collected {len(all_results)} successful results.")

aggregated_times = defaultdict(lambda: defaultdict(list))

for endpoint_key, item_count, took_ms in all_results:
    aggregated_times[endpoint_key][item_count].append(took_ms)

average_times = defaultdict(dict)

print("\nCalculating Averages:")
for endpoint_key, counts_data in aggregated_times.items():
    print(f"--- Endpoint: {endpoint_key} ---")
    for count, times in sorted(counts_data.items()):
        if times:
            avg = statistics.mean(times)
            stdev = statistics.stdev(times) if len(times) > 1 else 0
            median = statistics.median(times)
            average_times[endpoint_key][count] = avg
            print(f"  Count: {count:<5} | Samples: {len(times):<3} | Avg: {avg:>8.2f}ms | Median: {median:>8.2f}ms | StDev: {stdev:>7.2f}ms")
        else:
            print(f"  Count: {count:<5} | Samples: 0 | No successful results.")

# --- Plotting ---
print("\nGenerating plot...")
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax = plt.subplots(figsize=(12, 7))

colors = {'redis': 'red', 'postgres': 'blue', 'postgres redis cache' : "orange"}
markers = {'redis': 'o', 'postgres': 's', 'postgres redis cache' : 'x'}

for endpoint_key, avg_data in average_times.items():
    if avg_data: # Only plot if there's data
        counts = sorted(avg_data.keys())
        avg_ms = [avg_data[c] for c in counts]

        ax.plot(counts, avg_ms,
                label=f"{endpoint_key.capitalize()} Endpoint",
                color=colors.get(endpoint_key, 'black'),
                marker=markers.get(endpoint_key, '.'),
                linestyle='-',
                linewidth=2)
        ax.scatter(counts, avg_ms, color=colors.get(endpoint_key, 'black')) # Show individual points


ax.set_xlabel("Number of Items Requested")
ax.set_ylabel("Average Response Time (ms)")
ax.set_title("API Endpoint Performance Comparison (Server Time)")
ax.legend()
ax.grid(True)


info_text = f"Requests per Count: {REQUESTS_PER_COUNT}"
plt.text(0.01, 0.01, info_text, transform=ax.transAxes, fontsize=9, verticalalignment='bottom', bbox=dict(boxstyle='round,pad=0.3', fc='wheat', alpha=0.5))


plt.tight_layout()
plt.savefig("endpoint_benchmark_comparison.png")
print("\nPlot saved as 'endpoint_benchmark_comparison.png'")
plt.show()

print("Done.")
