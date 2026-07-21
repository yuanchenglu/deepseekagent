#!/usr/bin/env python3
"""
powerlog — RAPL + NVML host power consumption daemon.

Reads Intel RAPL energy counters (CPU package + DRAM) and estimates
GPU power via NVML utilization × power limit. Logs cumulative kWh
every N seconds with crash recovery (resumes from last log line).

Deploy as a systemd service running as root (energy_uj is root-only).
See SKILL.md §1 for RAPL permission details.

Usage: powerlog [-i INTERVAL_SECONDS] [-l LOGFILE_PATH]
Defaults: interval=600 (10 min), log=/var/log/powerlog.txt

Log format: "YYYY-MM-DD HH:MM:SS | cpu_kwh | gpu_kwh | total_kwh"
"""

import os, sys, time, signal, argparse, ctypes

RAPL_BASE = "/sys/class/powercap"
RAPL_DOMAINS = [
    ("pkg",  "intel-rapl:0"),
    ("dram", "intel-rapl:0:1"),
]
KWH_PER_UJ = 1.0 / 3.6e12


def read_uj(path):
    with open(path) as f:
        return int(f.read())


class NVMLPower:
    """Estimate GPU power from power limit and utilization."""

    def __init__(self):
        self.lib = None
        self.handle = None
        self.limit_mw = 0
        self.avail = False
        try:
            self.lib = ctypes.CDLL("libnvidia-ml.so.1", use_errno=True)
            if self.lib.nvmlInit() != 0:
                return
            h = ctypes.c_uint64()
            if self.lib.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(h)) != 0:
                self.lib.nvmlShutdown()
                return
            self.handle = h
            pl = ctypes.c_uint()
            if self.lib.nvmlDeviceGetPowerManagementLimit(h, ctypes.byref(pl)) == 0:
                self.limit_mw = pl.value
            self.avail = True
        except Exception:
            pass

    def estimate_mw(self):
        if not self.avail:
            return 0
        util = (ctypes.c_uint * 2)()
        if self.lib.nvmlDeviceGetUtilizationRates(self.handle, ctypes.byref(util)) != 0:
            return self.limit_mw * 40 // 100
        load = max(util[0], util[1])
        idle_mw = self.limit_mw * 40 // 100
        return idle_mw + (self.limit_mw - idle_mw) * load // 100

    def close(self):
        if self.lib and self.avail:
            try:
                self.lib.nvmlShutdown()
            except Exception:
                pass


class Daemon:
    def __init__(self, logfile, interval):
        self.logfile = logfile
        self.interval = interval
        self.domains = [(n, os.path.join(RAPL_BASE, p))
                        for n, p in RAPL_DOMAINS
                        if os.path.exists(os.path.join(RAPL_BASE, p, "energy_uj"))]
        if not self.domains:
            print("FATAL: no RAPL energy domains", file=sys.stderr)
            sys.exit(1)
        self.cpu_prev = {}
        self.cpu_maxv = {}
        self.cpu_uj = 0
        self.gpu_uj = 0
        self.nvml = NVMLPower()
        self._running = True

    def _load(self):
        if not os.path.exists(self.logfile):
            return
        try:
            with open(self.logfile) as f:
                last = None
                for line in f:
                    last = line
            if last is None:
                return
            parts = [p.strip() for p in last.split("|")]
            if len(parts) >= 4:
                self.cpu_uj = int(float(parts[1]) / KWH_PER_UJ + 0.5)
                self.gpu_uj = int(float(parts[2]) / KWH_PER_UJ + 0.5)
            elif len(parts) >= 2:
                self.cpu_uj = int(float(parts[1]) / KWH_PER_UJ + 0.5)
            print(f"resumed  cpu={self.cpu_uj*KWH_PER_UJ:.6f}  "
                  f"gpu={self.gpu_uj*KWH_PER_UJ:.6f} kWh")
        except Exception as e:
            print(f"load warning: {e}", file=sys.stderr)

    def _save(self, ts):
        cpu_kwh = self.cpu_uj * KWH_PER_UJ
        gpu_kwh = self.gpu_uj * KWH_PER_UJ
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        with open(self.logfile, "a") as f:
            f.write(f"{ts_str} | {cpu_kwh:.9f} | {gpu_kwh:.9f} | "
                    f"{cpu_kwh + gpu_kwh:.9f}\n")
        print(f"LOG {ts_str}  cpu={cpu_kwh:.6f} gpu={gpu_kwh:.6f} "
              f"total={cpu_kwh+gpu_kwh:.6f} kWh")

    def _cpu_delta(self):
        d = 0
        for name, path in self.domains:
            cur = read_uj(f"{path}/energy_uj")
            if name in self.cpu_prev:
                raw = cur - self.cpu_prev[name]
                if raw < 0:
                    raw += self.cpu_maxv[name]
                d += raw
            else:
                try:
                    self.cpu_maxv[name] = read_uj(f"{path}/max_energy_range_uj")
                except Exception:
                    self.cpu_maxv[name] = 0
            self.cpu_prev[name] = cur
        return d

    def run(self):
        self._load()
        self._cpu_delta()
        signal.signal(signal.SIGTERM, lambda *_: setattr(self, '_running', False))
        signal.signal(signal.SIGINT,  lambda *_: setattr(self, '_running', False))
        gpu_prev_mw = self.nvml.estimate_mw()
        last_t = time.time()
        nxt = last_t + self.interval
        while self._running:
            now = time.time()
            dt = now - last_t
            self.cpu_uj += self._cpu_delta()
            if self.nvml.avail:
                mw = self.nvml.estimate_mw()
                if gpu_prev_mw > 0:
                    avg_mw = (gpu_prev_mw + mw) / 2.0
                    self.gpu_uj += int(avg_mw * dt * 1000 + 0.5)
                gpu_prev_mw = mw
            last_t = now
            if now >= nxt:
                self._save(now)
                nxt = now + self.interval
            time.sleep(5)
        print("\nshutting down...")
        self._save(time.time())
        self.nvml.close()


def main():
    ap = argparse.ArgumentParser(description="RAPL + NVML power daemon")
    ap.add_argument("-i", "--interval", type=int, default=600)
    ap.add_argument("-l", "--log", default="/var/log/powerlog.txt")
    args = ap.parse_args()
    Daemon(args.log, args.interval).run()


if __name__ == "__main__":
    main()
