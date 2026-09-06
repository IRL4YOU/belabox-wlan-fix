#!/usr/bin/env python3
# Manual hardware test, not run by unittest. Downloads up to 750 MB over wlan0.
# Run as root only on the test box with explicit data-use approval.
# Test definition used 2026-09-03; no driver or network configuration changes.
import socket,urllib.request,time,subprocess,re,json
from pathlib import Path
from datetime import datetime,timezone
def connect(address,timeout=10,source_address=None):
    last=None
    for af,typ,proto,canon,sa in socket.getaddrinfo(address[0],address[1],socket.AF_INET,socket.SOCK_STREAM):
        s=socket.socket(af,typ,proto)
        try:
            s.settimeout(10); s.setsockopt(socket.SOL_SOCKET,socket.SO_BINDTODEVICE,b"wlan0\0"); s.connect(sa)
            print("WLAN_SOCKET_BOUND",flush=True); return s
        except OSError as e: last=e; s.close()
    raise last
def counters():
    return {n:int(Path("/sys/class/net/wlan0/statistics/"+n).read_text()) for n in ("rx_bytes","tx_bytes","rx_errors","tx_errors","rx_dropped","tx_dropped")}
since=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
before=counters(); boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip()
socket.create_connection=connect
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
limit=750000000; rate=2500000
req=urllib.request.Request("https://download.belabox.net/belabox_rock_5b_plus-20250915-a84acea.img.zip",headers={"Range":"bytes=0-"+str(limit-1)})
start=time.monotonic(); total=0; last_time=start; last_bytes=0
with opener.open(req,timeout=10) as r:
    assert r.status==206, "Server ignores bounded range"
    print("HTTP",r.status,"RANGE",r.headers.get("Content-Range"),"START",since,flush=True)
    while total<limit:
        if time.monotonic()-start>320: raise RuntimeError("Test duration exceeded")
        data=r.read(min(262144,limit-total))
        if not data: raise RuntimeError("Unexpected download end")
        total+=len(data)
        time.sleep(max(0,min(0.2,total/rate-(time.monotonic()-start))))
        now=time.monotonic()
        if now-last_time>=30 or total==limit:
            kernel=subprocess.check_output(["journalctl","-k","-b","0","--since",since,"--no-pager","-o","short-monotonic"],text=True,timeout=5)
            bad=[l for l in kernel.splitlines() if re.search(r"BUG:|Oops:|Kernel panic|NETDEV WATCHDOG|Call trace:|Out of memory",l)]
            api=json.loads(subprocess.check_output(["wget","-qO-","-T","3","http://localhost:8080/api/status"],text=True,timeout=5))
            print("PROGRESS",round(now-start,1),"SEC",total,"BYTES",round((total-last_bytes)*8/(now-last_time)/1e6,2),"MBIT_S","TEMP",api.get("temperature"),"CAMERAS",api.get("cameras"),"KERNEL_HITS",len(bad),flush=True)
            if bad: print("\n".join(bad[-5:]),flush=True); raise RuntimeError("Kernel error")
            last_time=now; last_bytes=total
elapsed=time.monotonic()-start
assert Path("/proc/sys/kernel/random/boot_id").read_text().strip()==boot
after=counters()
print("FINISHED_BYTES",total,"SECONDS",round(elapsed,2),"AVERAGE_MBIT_S",round(total*8/elapsed/1e6,2),"COUNTER_DELTA",{k:after[k]-before[k] for k in before},flush=True)
