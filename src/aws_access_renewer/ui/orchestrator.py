from rich.console import Console, Group
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from rich.columns import Columns
from rich.live import Live
from rich.table import Table
from .theme import CYBER_STEALTH
import sys
import tty
import termios
import asyncio
import questionary
from ..core.constants import VERSION, DEFAULT_REGION

console = Console(theme=CYBER_STEALTH)

class OrchestratorUI:
    def __init__(self, version: str = VERSION):
        self.version = version
        self.console = console

    def show_header(self):
        header_text = Text.assemble(
            (" ⚡ ", "info"),
            ("SYSTEM.AWS_RENEWER ", "info"),
            (f"v{self.version}", "dim"),
            (" ⚡ ", "info")
        )
        console.print(Panel(header_text, border_style="cyber.border", expand=False))
        console.print("")

    def show_env(self, ip: str, regions: int):
        metrics = [
            Panel(f"[dim]IP_ADDR:[/] [success]{ip}[/]", border_style="cyber.border"),
            Panel(f"[dim]REGIONS:[/] [aws.region]{regions}[/]", border_style="cyber.border")
        ]
        console.print(Columns(metrics))
        console.print("")

    def show_discovery_tree(self, instances_by_region: dict):
        tree = Tree(" [bold info]DATABASE_RESOURCES[/]")
        for region, insts in instances_by_region.items():
            r_node = tree.add(f"[aws.region]» {region or 'default'}[/]")
            for i in insts:
                name = i.get("Tags", [{"Key": "Name", "Value": "N/A"}])[0]["Value"]
                for tag in i.get("Tags", []):
                    if tag["Key"] == "Name":
                        name = tag["Value"]
                        break
                r_node.add(f"[aws.id]{i['InstanceId']}[/] [dim]|[/] [white]{name}[/]")
        console.print(tree)
        console.print("")

    @staticmethod
    def create_task_group(tasks: dict):
        lines = []
        for tid, data in tasks.items():
            status = data["status"]
            color = "info"
            icon = "»" 
            if status == "success": 
                icon, color = "✔", "success"
            elif status == "error": 
                icon, color = "✘", "danger"
            elif status == "skipped": 
                icon, color = "•", "warning"
            elif status == "running":
                icon, color = "⠋", "info"
            
            line = Text.assemble(
                (f" {icon} ", color),
                (f"{data['name']:<18} ", "white"),
                (f"[{data['id']}] ", "dim"),
                (f"» {data['msg']}", color)
            )
            lines.append(line)
        return Panel(Group(*lines), title="[bold info] PROCESS_MONITOR [/]", border_style="cyber.border", expand=False)

    async def interactive_multiselect(self, items: list, item_type: str = "RESOURCE"):
        """Custom keyboard-driven multiselector using Rich and Live."""
        selected_indices = {i for i in range(len(items))}
        cursor_index = 0
        
        def render():
            table = Table.grid(padding=(0, 2))
            table.add_column("State", justify="center", width=4)
            table.add_column("Item")
            
            for idx, item in enumerate(items):
                is_selected = idx in selected_indices
                is_cursor = idx == cursor_index
                
                check = "[bold #00FFFF]●[/]" if is_selected else "[dim]○[/]"
                
                if item_type == "RESOURCE":
                    name = item.get("Tags", [{"Key": "Name", "Value": "N/A"}])[0]["Value"]
                    for tag in item.get("Tags", []):
                        if tag["Key"] == "Name":
                            name = tag["Value"]
                            break
                    label = Text.assemble(
                        (f"{item['InstanceId']} ", "aws.id"),
                        (f"({name})", "dim")
                    )
                else: # PORT
                    label = Text(f"PORT {item}", style="white")
                
                if is_cursor:
                    row_content = Text.assemble(("» ", "info"), label)
                    table.add_row(check, row_content, style="highlight")
                else:
                    table.add_row(f"  {check}", label)
            
            return Panel.fit(
                table, 
                title=f"[bold info] {item_type}_SELECTION [/]", 
                subtitle="[dim] SPACE:Toggle | ENTER:Confirm [/]", 
                border_style="cyber.border",
                padding=(1, 2)
            )

        with Live(render(), console=self.console, refresh_per_second=20, auto_refresh=False) as live:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                while True:
                    live.update(render())
                    live.refresh()
                    
                    char = sys.stdin.read(1)
                    if char == '\r' or char == '\n': # Enter
                        break
                    elif char == ' ': # Space
                        if cursor_index in selected_indices:
                            selected_indices.remove(cursor_index)
                        else:
                            selected_indices.add(cursor_index)
                    elif char == '\x1b': # Escape or Arrow keys
                        next_char = sys.stdin.read(1)
                        if next_char == '[':
                            arrow = sys.stdin.read(1)
                            if arrow == 'A': # Up
                                cursor_index = (cursor_index - 1) % len(items)
                            elif arrow == 'B': # Down
                                cursor_index = (cursor_index + 1) % len(items)
                    elif char == '\x03': # Ctrl+C
                        raise KeyboardInterrupt()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        return [items[i] for i in selected_indices]

    async def prompt_for_credentials(self) -> dict:
        """Interactive prompt for AWS credentials when auth fails."""
        self.console.print("\n[bold danger]  AUTHENTICATION_REQUIRED [/]")
        self.console.print("[dim]Your AWS credentials are missing or invalid.[/]\n")
        
        creds = {}
        creds['aws_access_key_id'] = await questionary.text(
            "AWS Access Key ID:",
            validate=lambda x: True if len(x) > 0 else "Cannot be empty"
        ).ask_async()
        
        if not creds['aws_access_key_id']: return None

        creds['aws_secret_access_key'] = await questionary.password(
            "AWS Secret Access Key:",
            validate=lambda x: True if len(x) > 0 else "Cannot be empty"
        ).ask_async()

        if not creds['aws_secret_access_key']: return None

        creds['region'] = await questionary.text(
            "Default Region (e.g. us-east-1):",
            default=DEFAULT_REGION
        ).ask_async()

        return creds

    def show_summary(self, stats: dict):
        console.print("\n[dim]──────────────────────────────────────────────────[/]")
        summary_table = Table.grid(padding=(0, 1))
        summary_table.add_row(
            Text(" SUCCESS: ", "success"), Text(str(stats['success']), "white"),
            Text(" SKIPPED: ", "warning"), Text(str(stats['skipped']), "white"),
            Text(" ERRORS:  ", "danger"), Text(str(stats['error']), "white")
        )
        console.print(Panel(summary_table, title="[bold info] EXEC_REPORT [/]", border_style="cyber.border", expand=False))
        console.print("\n[bold success] » SESSION_COMPLETE [/]\n")
