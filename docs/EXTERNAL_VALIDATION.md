# External dataset validation

Measured 31 October 2026. This checks independently published log data through the unchanged ALIBI API; it does not evaluate incident detection.

## Attribution and selection

- Dataset: Elastic examples, NGINX combined-format sample logs.
- [Original publication](https://github.com/elastic/examples/tree/master/Common%20Data%20Formats/nginx_logs).
- Pinned commit: `6d86454ebb7a850bcd7e80abe86fe683370018a6`.
- [Exact source file](https://raw.githubusercontent.com/elastic/examples/6d86454ebb7a850bcd7e80abe86fe683370018a6/Common%20Data%20Formats/nginx_logs/nginx_logs).
- [Repository license](https://github.com/elastic/examples/blob/6d86454ebb7a850bcd7e80abe86fe683370018a6/LICENSE): Apache License 2.0, retrieved and inspected. Raw logs and downloaded license remain in ignored local output; no external log records are redistributed in this repository.

The downloaded original has **6,991,577 bytes and 51,462 physical records**. It exceeds ALIBI's 50,000-record per-file limit. Selection is the first **1,000 physical lines**, retaining every byte and line ending using `b''.join(original.splitlines(keepends=True)[:1000])`. The resulting **133,423-byte** prefix is not cleaned, rewritten or sampled by parse success. The full download and prefix are both preserved locally. No records inside the selected prefix are discarded.

Full-source SHA-256: `526832433ab552466dc8623390fd92dc052b4f301b2eec94836a5c42a46937df`.

Imported-prefix SHA-256: `787cdbb7452220f81735b46520178bdbb04667b43999a6b91e6371139ca3eebe`.

## Method and results

Three sequential runs each created a fresh investigation in the same running backend/SQLite environment. They are separate imports, not independent machines or cold process restarts. Timings use Python's monotonic `time.perf_counter`. Import time includes local HTTP upload, byte preservation, hashing, parsing and database persistence; it excludes source download, investigation creation, subsequent verification and reporting.

| Run | Input | Normalized | Gaps | Coverage | Import seconds | Records/second | Query milliseconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1,000 | 1,000 | 0 | 100% | 0.453472 | 2,205.21 | 24.171 |
| 2 | 1,000 | 1,000 | 0 | 100% | 0.169648 | 5,894.55 | 22.049 |
| 3 | 1,000 | 1,000 | 0 | 100% | 0.166977 | 5,988.85 | 26.382 |
| Median | 1,000/run | 1,000/run | 0/run | 100% | **0.169648** | **5,894.55** | **24.171** |

Auto detection accepted the combined access records using the existing web parser. Explicit +00:00 timestamps were normalized; no clock correction was applied. The search was `q=GET&limit=50`: each run reported 1,000 matching records and returned a matching 50-record page. Every original download matched the imported bytes exactly, intake hashes matched, and fresh evidence verification returned **verified** for all three imports.

A PDF was generated for the final 1,000-event investigation in **5.598301 seconds**, measured once, including HTTP response transfer. JSON and integrity-manifest exports also succeeded. Full-precision measurements and runtime details are preserved in [external-results.json](external-results.json).

Runtime: Python 3.12.14; Windows 11, build 10.0.26200; Intel64 Family 6 Model 186 Stepping 2; local FastAPI/SQLite backend using the project's locked dependencies. No remote processing service was used.

## Reproduce

Start ALIBI as described in README, then run from the repository root:

~~~powershell
.\.venv\Scripts\python.exe scripts/external_validation.py --commit 6d86454ebb7a850bcd7e80abe86fe683370018a6 --records 1000 --runs 3
.\.venv\Scripts\python.exe scripts/verify_manifest.py output/external/manifest.json
~~~

The first command downloads the pinned original into `output/external/` and performs the measurements. For the recorded run, the original had already been downloaded from that same pinned URL, so the invocation additionally used `--source-file output/external/nginx_logs.original`. Reproduction writes new measured values to `docs/external-results.json`; retain the committed result when comparing runs.

## Limitations and failures

The reproducible prefix is neither random nor representative of all NGINX traffic. Warm caches and shared machine load influence these small timings; the first import was slower. Three runs are insufficient for general performance guarantees. No independently labeled incident ground truth exists here, so 100% parsing coverage is **not** detection accuracy. Processing time is **not** human investigation time. The remainder of the source file was not imported or evaluated.

An initial benchmark-harness request used an incorrect option name (`format`) and was rejected with HTTP 422 before evidence import. The harness was corrected to the existing `log_format` contract; no parser, application code or API contract was changed. The rejected attempt is excluded from successful-run timing and left an empty local investigation. The three measured imports, search checks, preservation checks and exports completed successfully.
