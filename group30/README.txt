Solstice Continental -- group 30

Synthetic log extracts for the Enterprise Cyber Security assessment.
Host: db01. Asset: customer data in PostgreSQL orders and its nightly backups.
Capture: 2026-02-02 00:00:00 UTC inclusive to 2026-05-03 00:00:00 UTC exclusive.
The files combine 90 days of rotated logs. Timestamps omit the year; use 2026.
All times are UTC, including across daylight-saving changes.

auth.log: SSH authentication, sudo commands and PAM session events.
daemon.log: database, cron, system service and job-wrapper activity.
The exercise assumes a configured logging collector routes these services to
these two files. This is not a claim about a default Linux installation.
backup-orders, orders-report and orders-sync are fictional job wrappers that
write their own operational messages. PostgreSQL connection logging is enabled.

Use the revised assessment specification. Copy the two .log files into your
analysis project's logs/ folder. Derive your own counts, timeline and incident
facts from those files. Addresses are synthetic; do not contact them.
