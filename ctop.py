#!/usr/bin/env python3
import os
import shutil
import subprocess
import time
from datetime import datetime

# Cores ANSI
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
BLUE_BG = "\033[44;97m"

def parse_pct(val_str):
    try:
        return float(val_str.replace(',', '.'))
    except ValueError:
        return 0.0

def get_processes():
    try:
        # ps -c -e -o pid,user,pcpu,pmem,rss,comm -m
        result = subprocess.run(
            ["ps", "-c", "-e", "-o", "pid,user,pcpu,pmem,rss,comm", "-m"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return []
        
        lines = result.stdout.strip().split('\n')
        procs = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 5)
            if len(parts) == 6:
                pid, user, cpu, mem, rss, comm = parts
                
                try:
                    rss_kb = float(rss)
                    mem_mb = rss_kb / 1024.0
                    mem_mb_str = f"{mem_mb:.1f}MB"
                except ValueError:
                    mem_mb_str = "0.0MB"

                procs.append({
                    "pid": pid,
                    "user": user,
                    "cpu": cpu,
                    "mem": mem,
                    "mem_mb": mem_mb_str,
                    "cpu_val": parse_pct(cpu),
                    "mem_val": parse_pct(mem),
                    "comm": comm
                })
        
        # Ordenação por maior consumo de memória
        procs.sort(key=lambda p: p["mem_val"], reverse=True)
        return procs
    except Exception:
        return []

def make_bar(val, length):
    filled = int(round((val / 100.0) * length))
    filled = max(0, min(length, filled))
    empty = length - filled
    return "■" * filled + "·" * empty

def render_frame():
    size = shutil.get_terminal_size((80, 24))
    width = size.columns
    height = size.lines

    procs = get_processes()
    now_str = datetime.now().strftime("%H:%M:%S")

    output = []

    # Top Bar
    top_bar = f" CTOP | Ordem: MEMÓRIA (Maior) | {now_str} | Total: {len(procs)} procs | [Ctrl+C] Sair"
    output.append(f"{BLUE_BG}{top_bar.ljust(width)[:width]}{RESET}")

    # Colunas dinâmicas
    bar_len = 10 if width < 120 else 14
    col_pid = 9
    col_user = 14
    col_mem = bar_len + 20
    col_cpu = bar_len + 11
    col_comm = max(10, width - (col_pid + col_user + col_mem + col_cpu) - 1)

    # Header
    header = f"{'PID':<{col_pid}}{'USER':<{col_user}}{'MEM (Uso / MB)':<{col_mem}}{'CPU':<{col_cpu}}{'COMMAND':<{col_comm}}"
    output.append(f"{BOLD}{UNDERLINE}{header.ljust(width)[:width]}{RESET}")

    # Limite de linhas visíveis
    max_rows = max(1, height - 3)

    for p in procs[:max_rows]:
        cpu_bar = make_bar(p["cpu_val"], bar_len)
        mem_bar = make_bar(p["mem_val"], bar_len)

        # Cor do CPU
        if p["cpu_val"] > 70:
            cpu_color = f"{RED}{BOLD}"
        elif p["cpu_val"] > 25:
            cpu_color = YELLOW
        else:
            cpu_color = GREEN

        # Cor da Memória
        if p["mem_val"] > 20:
            mem_color = f"{RED}{BOLD}"
        elif p["mem_val"] > 5:
            mem_color = f"{YELLOW}{BOLD}"
        else:
            mem_color = MAGENTA

        pid_txt = f"{p['pid']:<{col_pid}}"
        user_txt = f"{CYAN}{p['user'][:col_user-1]:<{col_user}}{RESET}"
        mem_txt = f"{mem_color}[{mem_bar}] {p['mem']:>5}% {p['mem_mb']:>8}{RESET} "
        cpu_txt = f"{cpu_color}[{cpu_bar}] {p['cpu']:>5}%{RESET} "
        comm_txt = f"{BOLD}{p['comm'][:col_comm]}{RESET}"

        row = f"{pid_txt}{user_txt}{mem_txt}{cpu_txt}{comm_txt}"
        output.append(row)

    # Limpa a tela e imprime snapshot
    os.system('clear')
    print("\n".join(output), flush=True)

def main():
    while True:
        render_frame()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        os.system('clear')
        print("ctop finalizado.")
