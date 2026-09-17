"""Run alternating resident ASR comparisons; stop inactive owned worker pools."""
import argparse, hashlib, json, math, os, pathlib, selectors, signal, statistics, subprocess, time

def receive(process, timeout=60):
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        if not selector.select(timeout):
            raise TimeoutError(f"Worker {process.pid} did not respond within {timeout}s")
        line = process.stdout.readline()
        if not line:
            raise RuntimeError(f"Worker {process.pid} exited: {process.poll()}")
        return json.loads(line)

def cpu_seconds(pid):
    fields = pathlib.Path(f"/proc/{pid}/stat").read_text().split(") ", 1)[1].split()
    return (int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--rounds", type=int, default=20)
    args = parser.parse_args()
    assert not args.output.exists(), "Preserve previous results; use a new output path"
    manifest = json.loads(args.manifest.read_text())
    workers, logs, metadata, rows = {}, [], {}, []
    report = {"method": "Alternating forward/reverse order; two warmups per duration; fixed affinity; inactive owned worker pools SIGSTOP", "rounds": args.rounds, "manifest": manifest, "metadata": metadata, "rows": rows}
    error = None
    try:
        for variant in manifest["variants"]:
            label = variant["label"]
            log = args.output.with_name(args.output.stem + "-" + label + ".stderr.log").open("x")
            logs.append(log)
            process = subprocess.Popen([variant["python"], manifest["worker"], variant["config"], manifest["audio"], "--worker"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True, bufsize=1, env={**os.environ, "PYTHONPATH": ""})
            workers[label] = process
            metadata[label] = receive(process)
            assert metadata[label]["ready"], metadata[label]
            start = time.monotonic(); before = cpu_seconds(process.pid)
            time.sleep(.3)
            metadata[label]["idle_cpu_percent"] = 100 * (cpu_seconds(process.pid)-before)/(time.monotonic()-start)
            os.kill(process.pid, signal.SIGSTOP)
            print(json.dumps({"ready": label, "packages": metadata[label]["packages"], "native_ort": metadata[label].get("native_ort"), "idle_cpu_percent": metadata[label]["idle_cpu_percent"]}), flush=True)
        for round_no in range(args.rounds):
            for seconds in manifest.get("durations", [3, 5]):
                order = list(workers)
                if round_no % 2: order.reverse()
                for label in order:
                    process = workers[label]
                    os.kill(process.pid, signal.SIGCONT)
                    process.stdin.write(json.dumps({"seconds": seconds}) + "\n"); process.stdin.flush()
                    row = receive(process, 20)
                    os.kill(process.pid, signal.SIGSTOP)
                    rows.append({**row, "label": label, "round": round_no, "order": order})
            if (round_no+1) % 5 == 0:
                print(json.dumps({"rounds_complete": round_no+1, "timed_calls": len(rows)}), flush=True)
        summary = {}
        for label in workers:
            summary[label] = {}
            for duration in manifest.get("durations", [3, 5]):
                selected = [r for r in rows if r["label"] == label and r["seconds"] == duration]
                values = sorted(r["ms"] for r in selected)
                texts = sorted({r["text"] for r in selected})
                summary[label][str(duration)] = {"count": len(values), "median_ms": statistics.median(values), "p95_ms": values[math.ceil(.95*len(values))-1], "min_ms": values[0], "max_ms": values[-1], "texts": texts}
        reference = manifest["variants"][0]["label"]
        parity = {label: {str(duration): summary[label][str(duration)]["texts"] == summary[reference][str(duration)]["texts"] for duration in manifest.get("durations", [3, 5])} for label in workers}
        report.update(summary=summary, transcript_parity=parity, completed=True)
        print(json.dumps({"summary": summary, "transcript_parity": parity}), flush=True)
    except BaseException as exc:
        error = exc; report.update(completed=False, error=repr(exc))
    finally:
        for process in workers.values():
            if process.poll() is None:
                try:
                    os.kill(process.pid, signal.SIGCONT)
                    process.stdin.write('{"stop":true}\n'); process.stdin.flush()
                    process.wait(5)
                except (BrokenPipeError, ProcessLookupError, subprocess.TimeoutExpired):
                    if process.poll() is None:
                        process.terminate(); process.wait(5)
        for log in logs: log.close()
        args.output.write_text(json.dumps(report, indent=2))
    if error is not None: raise error

if __name__ == "__main__":
    main()
