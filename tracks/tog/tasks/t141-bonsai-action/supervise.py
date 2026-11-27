"""Bound the single dedicated Bonsai browser process tree, retaining its latest committed phase."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter, sleep

HERE=Path(__file__).resolve().parent
LIMIT=480


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    start=perf_counter()
    began=datetime.now(timezone.utc)
    with (out/"host.log").open("w",encoding="utf8") as log:
        proc=subprocess.Popen(["node",str(HERE/"run.mjs"),str(out)],stdout=log,stderr=subprocess.STDOUT,
                              start_new_session=os.name!="nt")
        expired=False
        while proc.poll() is None:
            if perf_counter()-start>=LIMIT:
                expired=True
                if os.name=="nt":
                    subprocess.run(["taskkill","/PID",str(proc.pid),"/T","/F"],stdout=log,stderr=log,check=False)
                else:
                    import signal
                    os.killpg(proc.pid,signal.SIGKILL)
                break
            sleep(.25)
        code=proc.wait()
    receipt=dict(limit_s=LIMIT,started_utc=began.isoformat(),elapsed_s=perf_counter()-start,
                 child_pid=proc.pid,returncode=code,expired=expired)
    (out/"EXIT.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf8")
    print(receipt)
    raise SystemExit(1 if expired or code else 0)
