# analysis.py 
# Job A: who is logging in to the server, and who is failing?
# Job B: what does a chosen address or account appear in?

LOG_FOLDER = "logs"          # the folder holding auth.log and daemon.log
INTERNAL_PREFIX = "10.90."   # Job A: addresses starting like this are inside the office
KEYS = []                    # Job B: the addresses or accounts to follow, in quotes,
                             # separated by commas, for example ["10.1.2.3", "alice"]

# ---------------- Job A: count logins by source address ----------------
failed, accepted = {}, {}
for line in open(LOG_FOLDER + "/auth.log"):
    words = line.split()
    if "Failed password" in line:
        ip = words[words.index("from") + 1]
        failed[ip] = failed.get(ip, 0) + 1
    elif "Accepted password" in line:
        ip = words[words.index("from") + 1]
        accepted[ip] = accepted.get(ip, 0) + 1

everyone = set(failed) | set(accepted)
table = sorted(everyone, key=lambda ip: failed.get(ip, 0), reverse=True)

out = open("source_summary.csv", "w")
out.write("source,where,failed,accepted\n")
for ip in table:
    where = "internal" if ip.startswith(INTERNAL_PREFIX) else "external"
    row = f"{ip},{where},{failed.get(ip, 0)},{accepted.get(ip, 0)}"
    out.write(row + "\n")
    print(row)
out.close()

# ---------------- Job B: find every line that mentions a key ----------------
for key in KEYS:
    out = open("evidence_" + key + ".txt", "w")
    count = 0
    for name in ["auth.log", "daemon.log"]:
        for line in open(LOG_FOLDER + "/" + name):
            if key in line:
                out.write(line)
                count += 1
    out.close()
    print("Job B:", count, "lines mentioning", key, "written to evidence_" + key + ".txt")
