from datetime import datetime
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.console import Console, Group
from .theme import TERMINAL_CLASSIC

console = Console(theme=TERMINAL_CLASSIC)

class Dashboard:
    def __init__(self, version: str = "1.6.0"):
        self.version = version
        self.layout = Layout()
        self.log_entries = []
        self.stats = {"success": 0, "skipped": 0, "error": 0, "total": 0}
        self.current_task = "Initializing..."
        self.ip = "Detecting..."
        self.region_info = "Waiting..."
        self._setup_layout()

    def _setup_layout(self):
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="body", ratio=3),
            Layout(name="side", ratio=1)
        )

    def log(self, msg: str, style: str = "info"):
        t = datetime.now().strftime("%H:%M:%S")
        self.log_entries.append(f"[dim]{t}[/] [{style}]{msg}[/]")
        if len(self.log_entries) > 25: self.log_entries.pop(0)
        self._render_all()

    def update_status(self, task: str = None, ip: str = None, regions: str = None):
        if task: self.current_task = task
        if ip: self.ip = ip
        if regions: self.region_info = regions
        self._render_all()

    def _render_all(self):
        # Header
        h_table = Table.grid(expand=True)
        h_table.add_column(ratio=1)
        h_table.add_column(justify="center", ratio=1)
        h_table.add_column(justify="right", ratio=1)
        h_table.add_row(
            f"[aws.id]AWS ACCESS RENEWER[/] [dim]v{self.version}[/]",
            f"[info]IP:[/] [success]{self.ip}[/]",
            f"[info]Regions:[/] [aws.region]{self.region_info}[/]"
        )
        self.layout["header"].update(Panel(h_table, border_style="border"))

        # Body (Activity Log)
        self.layout["body"].update(Panel("\n".join(self.log_entries), title="[bold info]Live Activity Log[/]", border_style="border"))

        # Side (Stats & Progress)
        s_table = Table.grid(padding=(0, 1))
        s_table.add_row("[success]Success:[/]", str(self.stats["success"]))
        s_table.add_row("[warning]Skipped:[/]", str(self.stats["skipped"]))
        s_table.add_row("[danger]Errors:[/]", str(self.stats["error"]))
        
        progress = Progress(SpinnerColumn("dots"), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), BarColumn(bar_width=12), console=console)
        if self.stats["total"] > 0:
            progress.add_task("", total=self.stats["total"], completed=self.stats["success"] + self.stats["skipped"] + self.stats["error"])

        self.layout["side"].update(Panel(
            Group(Align.center(Text("Session Monitor", style="info")), s_table, Text(""), progress),
            title="[bold info]Stats[/]", border_style="border"
        ))

        # Footer
        self.layout["footer"].update(Panel(Align.center(f"[info]Current Action:[/] [bold]{self.current_task}[/]"), border_style="border"))
