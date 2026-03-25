# sensors/sensor_simulator.py
import csv
import time
import requests
import os
from datetime import datetime

EDGE_URL  = os.environ.get("EDGE_URL", "http://localhost:5000/send_data")
CSV_FILE  = os.environ.get("CSV_FILE", "sensors/dataset.csv")
INTERVAL  = 1
MAX_RETRY = 3


def send_with_retry(data):
    for attempt in range(1, MAX_RETRY + 1):
        try:
            response = requests.post(EDGE_URL, json=data, timeout=5)
            response.raise_for_status()
            fog_status = response.json().get("fog_response", {}).get("status", "unknown")
            print(f"  Sent | {fog_status}")
            return True
        except requests.exceptions.ConnectionError:
            print(f"  Attempt {attempt}/{MAX_RETRY} - edge unreachable, retrying...")
        except requests.exceptions.Timeout:
            print(f"  Attempt {attempt}/{MAX_RETRY} - timed out, retrying...")
        except requests.exceptions.HTTPError as e:
            print(f"  HTTP error: {e}")
            break
        except Exception as e:
            print(f"  Error: {e}")
            break
        time.sleep(1)
    print(f"  Failed after {MAX_RETRY} attempts, skipping.")
    return False


def validate_data(patient_id, heart_rate_raw, spo2_raw, timestamp_raw=None):
    try:
        patient_id = str(patient_id).strip()
        heart_rate = int(heart_rate_raw)
        spo2       = int(spo2_raw)

        if not patient_id:
            raise ValueError("patient_id cannot be empty")
        if not (0 < heart_rate < 300):
            raise ValueError(f"heart_rate out of range: {heart_rate}")
        if not (0 <= spo2 <= 100):
            raise ValueError(f"spo2 out of range: {spo2}")

        if timestamp_raw:
            datetime.strptime(str(timestamp_raw).strip(), "%Y-%m-%d %H:%M:%S")
            timestamp = str(timestamp_raw).strip()
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "patient_id": patient_id,
            "heart_rate": heart_rate,
            "spo2":       spo2,
            "timestamp":  timestamp
        }
    except (ValueError, TypeError) as e:
        print(f"  Validation error: {e}")
        return None


def run_csv_mode():
    print(f"\nReading from {CSV_FILE}")
    print(f"Sending to {EDGE_URL}\n")
    sent = skipped = 0
    try:
        with open(CSV_FILE, newline='') as file:
            reader = csv.DictReader(file)
            for line_num, row in enumerate(reader, start=2):
                data = validate_data(
                    row.get("patient_id", ""),
                    row.get("heart_rate", ""),
                    row.get("spo2", ""),
                    row.get("timestamp", "")
                )
                if data is None:
                    print(f"  Skipping line {line_num}")
                    skipped += 1
                    continue
                print(f"Line {line_num} | Patient: {data['patient_id']} | HR: {data['heart_rate']} | SpO2: {data['spo2']}")
                if send_with_retry(data):
                    sent += 1
                else:
                    skipped += 1
                time.sleep(INTERVAL)
    except FileNotFoundError:
        print(f"  CSV file not found: {CSV_FILE}")
    print(f"\nDone - {sent} sent, {skipped} skipped.")


def run_manual_mode():
    print("\nEnter patient data. Type 'quit' at any prompt to exit.\n")
    sent = skipped = 0
    while True:
        patient_id = input("Patient ID       : ").strip()
        if patient_id.lower() == "quit":
            break

        heart_rate_raw = input("Heart Rate (BPM) : ").strip()
        if heart_rate_raw.lower() == "quit":
            break

        spo2_raw = input("SpO2 (%)         : ").strip()
        if spo2_raw.lower() == "quit":
            break

        timestamp_raw = input("Timestamp (YYYY-MM-DD HH:MM:SS) [blank for now]: ").strip()
        if timestamp_raw.lower() == "quit":
            break

        data = validate_data(patient_id, heart_rate_raw, spo2_raw, timestamp_raw or None)
        if data is None:
            print("  Invalid entry, try again.\n")
            skipped += 1
            continue

        print(f"\nSending | Patient: {data['patient_id']} | HR: {data['heart_rate']} | SpO2: {data['spo2']} | {data['timestamp']}")
        if send_with_retry(data):
            sent += 1
        else:
            skipped += 1
        print()

    print(f"\nSession ended - {sent} sent, {skipped} skipped.")


def choose_mode():
    print("IoMT Sensor Emulator")
    print("1 - CSV mode")
    print("2 - Manual mode")
    while True:
        choice = input("Select mode [1/2]: ").strip()
        if choice == "1":
            run_csv_mode()
            break
        elif choice == "2":
            run_manual_mode()
            break
        else:
            print("  Enter 1 or 2.")


if __name__ == "__main__":
    choose_mode()
