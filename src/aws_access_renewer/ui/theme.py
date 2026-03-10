from rich.theme import Theme

# --- THEME (Cyber-Stealth: Neon Cyan / Stealth Gray) ---
CYBER_STEALTH = Theme({
    "info": "bold #00FFFF",      # Neon Cyan
    "success": "bold #00FF00",   # Pure Green
    "warning": "bold #FFFF00",   # Pure Yellow
    "danger": "bold #FF0000",    # Pure Red
    "aws.id": "bold #FFFFFF",    # Pure White for critical data
    "aws.region": "bold #00CED1", # Dark Cyan
    "dim": "dim #696969",        # Dim Gray
    "cyber.border": "#2F4F4F",   # Dark Slate Gray
    "highlight": "reverse bold #00FFFF", # Inverse Cyan for selection
})
