# Part 4: Implementation and Evaluation
**Scope:** Actionable implementation roadmap and evaluation metrics for risks R1, R2, and R6  
**Host Context:** Solstice Continental production database server `db01` and orders database  
**Framework:** ISO 27005 Treatment & Andrew Jaquith Security Metrics Framework

---

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
