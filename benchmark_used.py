import csv
import hashlib
import json
import platform
import random
import secrets
import shutil
import ssl
import sys
from datetime import datetime
from pathlib import Path
from time import get_clock_info, perf_counter_ns

REPEATS = 30
WARMUPS = 3
KEY_LENGTH = 32
MAX_MEMORY = 512 * 1024 * 1024
ORDER_SEED = 20261120

CONFIGS = [
    {"id": "pbkdf2_100000", "algorithm": "pbkdf2", "iterations": 100_000},
    {"id": "pbkdf2_300000", "algorithm": "pbkdf2", "iterations": 300_000},
    {"id": "pbkdf2_600000", "algorithm": "pbkdf2", "iterations": 600_000},
    {"id": "pbkdf2_1200000", "algorithm": "pbkdf2", "iterations": 1_200_000},
    {"id": "scrypt_32768", "algorithm": "scrypt", "n": 2**15, "r": 8, "p": 1},
    {"id": "scrypt_65536", "algorithm": "scrypt", "n": 2**16, "r": 8, "p": 1},
    {"id": "scrypt_131072", "algorithm": "scrypt", "n": 2**17, "r": 8, "p": 1},
    {"id": "scrypt_262144", "algorithm": "scrypt", "n": 2**18, "r": 8, "p": 1},
]


def derive(config, password, salt):
    if config["algorithm"] == "pbkdf2":
        return hashlib.pbkdf2_hmac(
            "sha256",
            password,
            salt,
            iterations=config["iterations"],
            dklen=KEY_LENGTH
        )

    return hashlib.scrypt(
        password,
        salt=salt,
        n=config["n"],
        r=config["r"],
        p=config["p"],
        maxmem=MAX_MEMORY,
        dklen=KEY_LENGTH
    )


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def main():
    power_mode = input("Enter your current Windows power mode: ").strip()
    notes = input("Any relevant conditions or interruptions before starting? ").strip()

    started = datetime.now().astimezone()
    run_id = started.strftime("%Y%m%d_%H%M%S_%f")
    folder = Path(__file__).resolve().parent / "results" / run_id
    folder.mkdir(parents=True, exist_ok=False)

    shutil.copy2(Path(__file__).resolve(), folder / "benchmark_used.py")

    inputs_path = Path(__file__).resolve().parent / "benchmark_inputs.json"

    if inputs_path.exists():
        input_records = json.loads(inputs_path.read_text(encoding="utf-8"))
    else:
        input_records = [
            {
                "id": i + 1,
                "password_hex": secrets.token_bytes(32).hex(),
                "salt_hex": secrets.token_bytes(16).hex()
            }
            for i in range(REPEATS)
        ]
        save_json(inputs_path, input_records)

    if len(input_records) != REPEATS:
        raise ValueError("The input file must contain exactly 30 input pairs.")

    pairs = [
        (
            record["id"],
            bytes.fromhex(record["password_hex"]),
            bytes.fromhex(record["salt_hex"])
        )
        for record in input_records
    ]

    if any(len(password) != 32 or len(salt) != 16
           for _, password, salt in pairs):
        raise ValueError("Unexpected password or salt length in input file.")

    save_json(folder / "inputs.json", input_records)

    metadata = {
        "status": "started",
        "started_at": started.isoformat(),
        "python": sys.version,
        "openssl": ssl.OPENSSL_VERSION,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_reported_by_student": "Intel Core i5-10210U",
        "installed_ram_gb_reported_by_student": 8,
        "windows_edition_reported_by_student": "Windows 11 Pro",
        "windows_version_reported_by_student": "26H2",
        "windows_build_reported_by_student": "26300.9818",
        "power_mode": power_mode,
        "pre_run_notes": notes,
        "repeats_per_configuration": REPEATS,
        "warmups_per_configuration": WARMUPS,
        "derived_key_bytes": KEY_LENGTH,
        "scrypt_maxmem_bytes": MAX_MEMORY,
        "order_seed": ORDER_SEED,
        "clock": vars(get_clock_info("perf_counter")),
        "configurations": CONFIGS,
        "memory_method": "No process memory measured in this timing experiment."
    }
    save_json(folder / "metadata.json", metadata)

    print("\nWarming up — these calls are not recorded.")
    for config in CONFIGS:
        for _ in range(WARMUPS):
            output = derive(config, pairs[0][1], pairs[0][2])
            if len(output) != KEY_LENGTH:
                raise RuntimeError("Unexpected derived-key length.")

    rng = random.Random(ORDER_SEED)
    fields = [
        "round", "position", "input_id", "configuration",
        "algorithm", "iterations", "n", "r", "p", "elapsed_ns"
    ]

    print("Recording measurements. Please leave the laptop idle.")

    with (folder / "raw_timings.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()

        for round_number, (input_id, password, salt) in enumerate(pairs, 1):
            order = CONFIGS.copy()
            rng.shuffle(order)

            for position, config in enumerate(order, 1):
                start = perf_counter_ns()
                output = derive(config, password, salt)
                elapsed_ns = perf_counter_ns() - start

                if len(output) != KEY_LENGTH:
                    raise RuntimeError("Unexpected derived-key length.")

                writer.writerow({
                    "round": round_number,
                    "position": position,
                    "input_id": input_id,
                    "configuration": config["id"],
                    "algorithm": config["algorithm"],
                    "iterations": config.get("iterations", ""),
                    "n": config.get("n", ""),
                    "r": config.get("r", ""),
                    "p": config.get("p", ""),
                    "elapsed_ns": elapsed_ns
                })
                handle.flush()

            print(f"Completed round {round_number}/{REPEATS}")

    metadata["status"] = "completed"
    metadata["finished_at"] = datetime.now().astimezone().isoformat()
    metadata["measurement_rows"] = REPEATS * len(CONFIGS)
    save_json(folder / "metadata.json", metadata)

    print(f"\nFinished: {metadata['measurement_rows']} measurements saved.")
    print("Results folder:", folder)


if __name__ == "__main__":
    main()
    input("\nPress Enter to close...")