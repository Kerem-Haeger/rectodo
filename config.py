"""
Configuration constants for the RecToDo application.
"""

# Recruiter configuration
CURRENT_OWNER = "Kerem"  # change to your own name when running locally

# Stage options shown in the add / update dialog
STAGE_OPTIONS = [
    "sent",
    "feedback requested",
    "interview",
    "offer",
    "rejected",
    "on hold",
]

# Column headers for the pipeline table
TABLE_COLUMNS = [
    "Candidate",
    "Client",
    "Role",
    "Stage",
    "Last action",
    "Next check",
    "Due in (days)",
    "Priority",
]
