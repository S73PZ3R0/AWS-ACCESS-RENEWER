#!/usr/bin/env python3
import sys
import os
import asyncio
from rich.live import Live
from rich.console import Console

# Adjust path for internal modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from aws_access_renewer.cli import parse_args
from aws_access_renewer.core.network import fetch_public_ip
from aws_access_renewer.core.aws import EC2Service, SecurityGroupService
from aws_access_renewer.core.updater import SSHRuleUpdater
from aws_access_renewer.ui.orchestrator import OrchestratorUI

async def main():
    args = parse_args()
    ui = OrchestratorUI(version="1.7.0")
    
    ui.show_header()

    try:
        # 1. Environment Discovery
        src_ip = args.source_ip or await fetch_public_ip()
        
        regions = [None]
        if args.regions:
            if args.regions.lower() == "all":
                regions = await EC2Service(profile=args.profile).list_regions()
            else: 
                regions = [r.strip() for r in args.regions.split(",")]
        
        ui.show_env(src_ip, len(regions))

        # 2. Resource Scanning
        instances_by_region = {}
        all_instances = []
        
        with ui.console.status("[info]SCANNING_INFRASTRUCTURE...[/]"):
            for r in regions:
                try:
                    svc = EC2Service(profile=args.profile, region=r)
                    insts = await svc.list_instances()
                    matches = [i for i in insts if not (args.instance_id or args.instance_name) or 
                               (i["InstanceId"] == args.instance_id or 
                                 EC2Service.instance_name(i) == args.instance_name)]
                    if matches:
                        instances_by_region[r] = matches
                        for m in matches: 
                            m["_region"] = r
                        all_instances.extend(matches)
                except Exception as e:
                    ui.console.print(f"[danger]✘[/] REGION_ERROR [{r or 'default'}]: {e}")

        if not all_instances:
            ui.console.print("\n[warning]  NO_TARGETS_FOUND [/]\n")
            return

        ui.show_discovery_tree(instances_by_region)

        # 3. Interactive Selection
        if args.batch:
            selected = all_instances
        else:
            selected = await ui.interactive_select(all_instances)
            
            if not selected:
                ui.console.print("\n[warning]  ABORTED: NO_RESOURCES_SELECTED [/]\n")
                return

        # 4. Orchestrated Execution
        ui.console.print("[bold info]  EXECUTION_START [/]")
        tasks = {inst["InstanceId"]: {
            "id": inst["InstanceId"], 
            "name": EC2Service.instance_name(inst), 
            "status": "pending", 
            "msg": "Waiting..."
        } for inst in selected}
        
        stats = {"success": 0, "skipped": 0, "error": 0}

        with Live(ui.create_task_group(tasks), console=ui.console, refresh_per_second=10) as live:
            for inst in selected:
                tid = inst["InstanceId"]
                tasks[tid]["status"] = "running"
                tasks[tid]["msg"] = "Synchronizing..."
                live.update(ui.create_task_group(tasks))

                try:
                    region = inst["_region"]
                    updater = SSHRuleUpdater(
                        inst, args.ssh_port, src_ip, args.profile, region, 
                        args.dry_run, args.cleanup
                    )
                    sg_service = SecurityGroupService(args.profile, region)
                    rules = await sg_service.list_rules()
                    res = await updater.update(rules)
                    
                    if res["updated"] > 0:
                        tasks[tid]["status"] = "success"
                        tasks[tid]["msg"] = f"Updated {res['updated']} rule(s)"
                        stats["success"] += 1
                    elif res["skipped"] > 0:
                        tasks[tid]["status"] = "skipped"
                        tasks[tid]["msg"] = "Already up-to-date"
                        stats["skipped"] += 1
                    else:
                        tasks[tid]["status"] = "skipped"
                        tasks[tid]["msg"] = "No matching rules"
                        stats["skipped"] += 1
                except Exception as e:
                    tasks[tid]["status"] = "error"
                    tasks[tid]["msg"] = str(e)
                    stats["error"] += 1
                
                live.update(ui.create_task_group(tasks))

        # 5. Final Report
        ui.show_summary(stats)

    except Exception as e:
        ui.console.print(f"\n[bold danger]FATAL ERROR:[/] {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.ensure_future(main())
        else:
            asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[warning]Operation cancelled.[/]")
        sys.exit(130)
