# Password-Hashing Performance Benchmark

This repository contains the code and raw results for a small controlled benchmark of PBKDF2-HMAC-SHA-256 and scrypt on a consumer laptop.

## Research question

How do PBKDF2-HMAC-SHA-256 iteration counts and scrypt cost parameter N affect execution time and estimated memory requirements on a consumer laptop?

## What was measured

The benchmark measured the execution time of individual password-hashing calls using Python's `hashlib` module.

PBKDF2-HMAC-SHA-256 was tested at:

- 100,000 iterations
- 300,000 iterations
- 600,000 iterations
- 1,200,000 iterations

scrypt was tested at:

- N = 32,768
- N = 65,536
- N = 131,072
- N = 262,144

For all scrypt tests, `r = 8` and `p = 1`.

Each configuration was measured 30 times, producing 240 timing observations in total.

## Files

- `benchmark_used.py`: the Python benchmark script used to collect the final measurements.
- `raw_timings.csv`: the raw timing results from the final experiment.
- `metadata.json`: information about the hardware, software, power mode, and benchmark settings.
- `inputs.json`: the synthetic password and salt inputs used in the experiment.
- `requirements.txt`: the Python dependencies required to run the benchmark.

## How to run

1. Install Python 3.
2. Install the required package:

```bash
pip install -r requirements.txt
```

3. Run the benchmark:

```bash
python benchmark_used.py
```

The script creates a new results folder containing raw timing data, metadata, and input definitions.

## Memory estimate

Process memory was not measured during the experiment. The scrypt memory values reported in the research paper are calculated estimates based on OpenSSL's documented approximate relationship:

```text
M = 128 * N * r * p bytes
```

Because `r = 8` and `p = 1`, this becomes:

```text
M = 1,024 * N bytes
```

The estimated working-memory requirements were:

- N = 32,768: 32 MiB
- N = 65,536: 64 MiB
- N = 131,072: 128 MiB
- N = 262,144: 256 MiB

These are calculated estimates, not measured peak process memory.

## Limitations

The results describe one consumer laptop, one software environment, synthetic inputs, and the specific configurations tested. The study did not measure real-world password-cracking performance, GPU or ASIC performance, concurrent server throughput, or actual process memory. Background processes were not continuously monitored during the measurement run.

## AI-use declaration

Perplexity was used to help clarify the research design, interpret the experimental results, draft and revise text, and organise the reproducibility package. The researcher independently checked all sources, ran and verified the benchmark code, checked the raw data and calculations.
