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
This overarching policy is supported by detailed technical standards and procedural manuals:
* Technical Standard TS-01: Remote Access and Multi-Factor Authentication Architecture
* Technical Standard TS-02: Privileged Access Management and Just-In-Time Elevation
* Technical Standard TS-03: Security Logging, SIEM Ingestion, and Audit Retention Standard
* Operational Procedure OP-04: Infrastructure Change Control and File Integrity Monitoring
* Emergency Procedure EP-01: Cyber Incident Response Plan and ICO Breach Notification Protocol

### 6. Exceptions and Compliance
* **Exception Handling:** Any deviation from this policy requires a formal written Exception Request submitted to the Head of Information Security and the Data Owner. Approval will be granted only where compensating security controls are demonstrated, a named risk owner assumes documented liability, and an explicit expiry date not exceeding 90 days is defined.
* **Compliance and Enforcement:** Compliance is subject to periodic automated audits. Employee violations are subject to formal disciplinary action up to and including termination of employment. Supplier violations constitute a material breach of contract, resulting in immediate account revocation, termination of commercial agreements, and potential civil recovery for damages.
