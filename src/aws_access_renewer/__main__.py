#!/usr/bin/env python3
import asyncio
import sys
import os
import json
from rich.live import Live

# Adjust path for local run and packaging
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
if os.path.exists(src_path):
    sys.path.insert(0, src_path)

from aws_access_renewer.cli import parse_args
from aws_access_renewer.core.network import fetch_public_ip
from aws_access_renewer.core.aws import EC2Service, SecurityGroupService, AWSAuthError, AWSConfigError
from aws_access_renewer.core.updater import SSHRuleUpdater
from aws_access_renewer.ui.orchestrator import OrchestratorUI

async def run_orchestrator(args, ui):
    try:
        # 1. Environment Discovery
        src_ip = args.source_ip or await fetch_public_ip()
        
        regions = [None]
        if args.regions:
            if args.regions.lower() == "all":
                regions = await EC2Service(profile=args.profile).list_regions()
            else: 
                regions = [r.strip() for r in args.regions.split(",")]
        
        if not args.batch:
            ui.show_env(src_ip, len(regions))

        # 2. Resource Scanning
        instances_by_region = {}
        all_instances = []
        
        if not args.batch:
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
                    except (AWSAuthError, AWSConfigError):
                        raise # Bubble up to main retry loop
                    except Exception as e:
                        ui.console.print(f"[danger]✘[/] REGION_ERROR [{r or 'default'}]: {e}")
        else:
            for r in regions:
                try:
                    svc = EC2Service(profile=args.profile, region=r)
                    insts = await svc.list_instances()
                    matches = [i for i in insts if not (args.instance_id or args.instance_name) or 
                               (i["InstanceId"] == args.instance_id or 
                                 EC2Service.instance_name(i) == args.instance_name)]
                    if matches:
                        for m in matches: m["_region"] = r
                        all_instances.extend(matches)
                except (AWSAuthError, AWSConfigError):
                    raise
                except Exception: pass

        if not all_instances:
            if not args.batch:
                ui.console.print("\n[warning]  NO_TARGETS_FOUND [/]\n")
            else:
                print(json.dumps({"error": "no_targets_found", "status": "failed"}))
            return True

        if not args.batch:
            ui.show_discovery_tree(instances_by_region)

        # 3. Interactive Selection
        if args.batch:
            selected = all_instances
            ports = [int(p.strip()) for p in args.ssh_port.split(",")] if args.ssh_port else [22]
        else:
            selected = await ui.interactive_multiselect(all_instances, item_type="RESOURCE")
            if not selected:
                ui.console.print("\n[warning]  ABORTED: NO_RESOURCES_SELECTED [/]\n")
                return True

            if args.ssh_port:
                ports = [int(p.strip()) for p in args.ssh_port.split(",")]
            else:
                with ui.console.status("[info]DISCOVERING_PORTS...[/]"):
                    discovered_ports = set()
                    for inst in selected:
                        sg_service = SecurityGroupService(args.profile, inst["_region"])
                        rules = await sg_service.list_rules()
                        sg_ids = {sg["GroupId"] for sg in inst["SecurityGroups"]}
                        for r in rules:
                            if (r["GroupId"] in sg_ids and not r["IsEgress"] and 
                                r["IpProtocol"] == "tcp" and "FromPort" in r):
                                discovered_ports.add(r["FromPort"])
                if not discovered_ports: discovered_ports = {22}
                ports = await ui.interactive_multiselect(sorted(list(discovered_ports)), item_type="PORT")
                if not ports:
                    ui.console.print("\n[warning]  ABORTED: NO_PORTS_SELECTED [/]\n")
                    return True

        # 4. Execution
        if not args.batch:
            ui.console.print("[bold info]  EXECUTION_START [/]")
        
        tasks = {inst["InstanceId"]: {
            "id": inst["InstanceId"], 
            "name": EC2Service.instance_name(inst), 
            "status": "pending", 
            "msg": "Waiting..."
        } for inst in selected}
        
        stats = {"success": 0, "skipped": 0, "error": 0}
        batch_results = []

        async def execute(live_ctx=None):
            for inst in selected:
                tid = inst["InstanceId"]
                tasks[tid]["status"] = "running"
                tasks[tid]["msg"] = "Synchronizing..."
                if live_ctx: live_ctx.update(ui.create_task_group(tasks))

                res_obj = {"instance_id": inst["InstanceId"], "name": EC2Service.instance_name(inst), "region": inst["_region"] or "default", "status": "pending", "details": ""}

                try:
                    region = inst["_region"]
                    updater = SSHRuleUpdater(inst, ports, src_ip, args.profile, region, args.dry_run, args.cleanup)
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
                    res_obj["status"] = tasks[tid]["status"]
                    res_obj["details"] = tasks[tid]["msg"]
                except Exception as e:
                    tasks[tid]["status"] = "error"
                    tasks[tid]["msg"] = str(e)
                    stats["error"] += 1
                    res_obj["status"] = "error"
                    res_obj["details"] = str(e)
                
                batch_results.append(res_obj)
                if live_ctx: live_ctx.update(ui.create_task_group(tasks))

        if not args.batch:
            with Live(ui.create_task_group(tasks), console=ui.console, refresh_per_second=10) as live:
                await execute(live)
        else:
            await execute()

        # 5. Final Report
        if not args.batch:
            ui.show_summary(stats)
        else:
            print(json.dumps({"source_ip": src_ip, "summary": stats, "results": batch_results}, indent=2))
        
        return True

    except (AWSAuthError, AWSConfigError) as e:
        if args.batch:
            print(json.dumps({"error": str(e), "status": "auth_failure"}))
            return True
        else:
            # Return False to trigger credential prompt and retry
            return False

async def main_async():
    args = parse_args()
    ui = OrchestratorUI(version="1.8.0")
    
    if not args.batch:
        ui.show_header()

    while True:
        success = await run_orchestrator(args, ui)
        if success:
            break
        
        # If we got here, it's an auth/config failure in interactive mode
        creds = await ui.prompt_for_credentials()
        if not creds:
            ui.console.print("\n[warning]  ABORTED: NO_CREDENTIALS_PROVIDED [/]\n")
            break
        
        # Apply credentials to environment
        os.environ['AWS_ACCESS_KEY_ID'] = creds['aws_access_key_id']
        os.environ['AWS_SECRET_ACCESS_KEY'] = creds['aws_secret_access_key']
        os.environ['AWS_DEFAULT_REGION'] = creds['region']
        
        ui.console.print("\n[success] ✔ CREDENTIALS_APPLIED [/] [dim]Retrying operation...[/]\n")

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        if sys.stdin.isatty():
            print("\n[warning]Operation cancelled.[/]")
        sys.exit(130)

if __name__ == "__main__":
    main()
