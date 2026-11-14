import os, subprocess, sys, time, zipfile
os.chdir(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists("hiC.npz"):
    zipfile.ZipFile("traces.zip").extractall(".")
CAM = {"hi.npz": ("7", "-4"), "hiB.npz": ("26", "9"), "hiC.npz": ("2.2", "-11")}
JOBS = [("hi.npz", 1260, 1326), ("hi.npz", 1326, 1392), ("hi.npz", 1392, 1458),
        ("hiB.npz", 1458, 1524), ("hiB.npz", 2106, 2160),
        ("hiC.npz", 2160, 2226), ("hiC.npz", 2520, 2589), ("hiC.npz", 2589, 2658)]
procs = []
for npz, a, b in JOBS:
    env = dict(os.environ, EL=CAM[npz][0], ROLL=CAM[npz][1], OW="1080", OH="1920",
               OMP_NUM_THREADS="3", OPENBLAS_NUM_THREADS="3")
    log = open(f"q_{a}.log", "w")
    procs.append(subprocess.Popen([sys.executable, "shade.py", npz, "video", f"q_{a}.mp4", "50", str(a), str(b)],
                                  env=env, stdout=log, stderr=subprocess.STDOUT))
t0 = time.time()
codes = [p.wait() for p in procs]
print("ALLDONE", codes, round(time.time() - t0), "s", flush=True)
