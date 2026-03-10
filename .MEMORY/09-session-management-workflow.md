# Memory Card: Session Management Workflow

Goal: keep the operational context of why session files matter after they are collected.

System stance:

- the product is for one user only
- the default surface is private and password-protected
- public sharing is a separate explicit action, not the default mode

Core workflow:

- find the correct session across many providers
- verify the exact source file path
- identify the session through first user message, last user message, and short intent bullets
- decide whether the session should be continued, inspected, or handed off to another agent

Card requirements:

- show full path or a path that can be expanded to the full source file
- show first user message
- show last user message
- show short intent progression built from user messages

Future direction:

- allow deeper drill-down into a session file
- run operations over selected JSON or JSONL files
- generate dedicated landing pages from chosen session artifacts
