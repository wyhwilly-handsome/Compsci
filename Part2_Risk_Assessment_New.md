# Part 2: Risk Assessment
**Target Asset:** PostgreSQL `orders` database and nightly backups on `db01` | **Assessment Methodology:** ISO 27005 & NIST SP 800-30 Rev 1  
**Group:** Group AD (Log Set: Group 30) | **Core Scope:** Pre-remediation risk baseline

---

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
