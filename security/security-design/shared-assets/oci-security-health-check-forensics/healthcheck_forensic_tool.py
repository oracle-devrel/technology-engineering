"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

healthcheck_forensic_tool.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import sys
import os
import glob
import shutil
import requests
import readline
import atexit
import datetime
import tempfile
from pathlib import Path

from classes.config_manager import ConfigManager
from classes.logger import Logger
from classes.csv_loader_duckdb import CSVLoaderDuckDB as CSVLoader
from classes.query_executor_duckdb import QueryExecutorDuckDB as QueryExecutor
from classes.oci_config_selector import OCIConfigSelector
from classes.directory_selector import DirectorySelector
from classes.command_parser import CommandParser
from classes.commands.registry import CommandRegistry
from classes.commands.base_command import ShellContext
from classes.commands.command_history import CommandHistory
from classes.commands.cloudguard_commands import CloudGuardFetchCommand, CloudGuardDeleteCommand
import classes.commands.standard_commands as std
import classes.commands.filter_commands as filt
import classes.commands.control_commands as ctl
import classes.commands.audit_commands as audit

# Pandas display options (if you ever import pandas here)
try:
    import pandas as pd
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    pd.set_option("display.max_colwidth", None)
except ImportError:
    pass

# Global variable to store the combined config file path
_combined_config_file = None

# -----------------------------------------------------------------------------
def is_repo_accessible(url: str) -> bool:
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False

def setup_showoci() -> bool:
    repo_url = "https://github.com/oracle/oci-python-sdk"
    repo_path = "oci-python-sdk"
    showoci_dir = "showoci"
    backup_zip = "showoci_zip/showoci.zip"

    # First, try to clone/update from GitHub
    if is_repo_accessible(repo_url):
        print("✓ Internet connection detected. Attempting to clone/update OCI SDK...")
        try:
            # Clone or pull
            if not os.path.isdir(repo_path):
                print("Cloning OCI SDK from GitHub...")
                import git
                git.Repo.clone_from(repo_url, repo_path)
                print("✓ Successfully cloned OCI SDK repository")
            else:
                print("Updating existing OCI SDK repository...")
                import git
                repo = git.Repo(repo_path)
                repo.remotes.origin.pull()
                print("✓ Successfully updated OCI SDK repository")

            # Create symlink and copy files
            link_target = os.path.join(repo_path, "examples", "showoci")
            if not os.path.exists(showoci_dir):
                os.symlink(link_target, showoci_dir)

            # Copy the .py files into the CWD
            for src in glob.glob(os.path.join(showoci_dir, "*.py")):
                shutil.copy(src, ".")
            
            print("✓ ShowOCI setup completed using GitHub repository")
            return True

        except Exception as e:
            print(f"⚠️  Failed to clone/update from GitHub: {e}")
            print("📦 Falling back to local backup...")
            # Fall through to backup method

    else:
        print("❌ No internet connection detected or GitHub is not accessible")
        print("📦 Using local backup archive...")

    # Fallback: Use local backup zip file
    if not os.path.exists(backup_zip):
        print(f"❌ Error: Backup file '{backup_zip}' not found!")
        print("   Please ensure you have either:")
        print("   1. Internet connection to download from GitHub, OR")
        print("   2. The backup file 'showoci_zip/showoci.zip' in your project directory")
        return False

    try:
        print(f"📦 Extracting ShowOCI from backup archive: {backup_zip}")
        import zipfile
        
        # Extract zip to current directory
        with zipfile.ZipFile(backup_zip, 'r') as zip_ref:
            zip_ref.extractall(".")

        print("✓ Successfully extracted ShowOCI from backup archive")
        print("📋 Note: Using offline backup - some features may be outdated")
        return True

    except Exception as e:
        print(f"❌ Failed to extract from backup archive: {e}")
        print("   Please check that 'showoci_zip/showoci.zip' is a valid archive")
        return False    

def create_combined_config_file(oci_config_selector):
    """
    Creates a temporary combined config file that showoci can use.
    Returns the path to the temporary file.
    """
    global _combined_config_file
    
    # Clean up any existing combined config file
    cleanup_combined_config_file()
    
    # Create a new temporary file that won't be automatically deleted
    temp_fd, temp_path = tempfile.mkstemp(suffix='.config', prefix='combined_oci_')
    
    try:
        with os.fdopen(temp_fd, 'w') as temp_file:
            temp_file.write(oci_config_selector.get_combined_config_content())
        
        _combined_config_file = temp_path
        print(f"Created temporary combined config file: {temp_path}")
        return temp_path
    except Exception as e:
        # Clean up on error
        try:
            os.unlink(temp_path)
        except:
            pass
        raise e

def cleanup_combined_config_file():
    """
    Cleans up the temporary combined config file.
    """
    global _combined_config_file
    
    if _combined_config_file and os.path.exists(_combined_config_file):
        try:
            os.unlink(_combined_config_file)
            print(f"Cleaned up temporary config file: {_combined_config_file}")
        except Exception as e:
            print(f"Warning: Could not clean up temporary config file {_combined_config_file}: {e}")
        finally:
            _combined_config_file = None

def call_showoci(combined_conf_file, profile, tenancy, out_dir, prefix, arg):
    """
    Updated to use the combined config file instead of the original one.
    """
    sys.argv = [
        "main.py",
        "-cf", combined_conf_file,  # Use the combined config file
        "-t", tenancy,
        f"-{arg}",
        "-csv", os.path.join(out_dir, prefix),
        "-jf",  os.path.join(out_dir, "showoci.json")
    ]
    from showoci import execute_extract
    execute_extract()

def new_snapshot(tenancy, base, prefix, combined_conf_file, arg):
    """
    Updated to use the combined config file.
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target = os.path.join(base, f"{tenancy}_{ts}")
    os.makedirs(target, exist_ok=True)
    call_showoci(combined_conf_file, tenancy, tenancy, target, prefix, arg)
    return target

def set_tenancy_data(logger, cfg_mgr):
    csv_dir     = cfg_mgr.get_setting("csv_dir")
    oci_conf    = cfg_mgr.get_setting("oci_config_file")
    tqt_conf    = cfg_mgr.get_setting("tqt_config_file")
    prefix      = cfg_mgr.get_setting("prefix")
    resource_arg= cfg_mgr.get_setting("resource_argument")

    print(f"\nConfig → csv_dir={csv_dir}, oci_config_file={oci_conf}, tqt_config_file={tqt_conf}, prefix={prefix}\n")

    # Create the OCI config selector with both config files
    sel = OCIConfigSelector(oci_conf, tqt_conf, csv_dir)
    tenancy, override_prefix = sel.select_section()
    prefix = override_prefix or prefix

    # Create a temporary combined config file for showoci to use
    combined_conf_file = create_combined_config_file(sel)

    tenancy_dir = os.path.join(csv_dir, tenancy)
    if os.path.isdir(tenancy_dir) and os.listdir(tenancy_dir):
        ds = DirectorySelector(tenancy_dir)
        choice = ds.select_directory()
        if choice == ds.get_new_snapshot():
            choice = new_snapshot(tenancy, tenancy_dir, prefix, combined_conf_file, resource_arg)
    else:
        choice = new_snapshot(tenancy, tenancy_dir, prefix, combined_conf_file, resource_arg)

    print(f"Loading CSVs from → {choice}")
    loader = CSVLoader(
        csv_dir=choice,
        prefix=prefix,
        delimiter=cfg_mgr.get_setting("delimiter"),
        case_insensitive_headers=cfg_mgr.get_setting("case_insensitive_headers") or False
    )
    loader.load_csv_files()
    logger.log("CSV files loaded.")

    tables = loader.conn.execute("SHOW TABLES").fetchall()
    tables = [t[0] for t in tables]
    logger.log(f"Tables: {tables}")

    executor = QueryExecutor(loader.conn)
    executor.current_snapshot_dir = choice
    return executor

def show_startup_help():
    """Display helpful information when the tool starts"""
    print("=" * 80)
    print("OCI QUERY TOOL - Interactive Mode")
    print("=" * 80)
    print("Available commands:")
    print("  show tables                    - List all loaded CSV tables")
    print("  describe <table>               - Show table structure")
    print("  SELECT * FROM <table>          - Run SQL queries on your data")
    print("  history                        - Show command history")
    print("  help [command]                 - Get detailed help")
    print()
    print("Data Fetching Commands:")
    print("  audit_events fetch DD-MM-YYYY <days>    - Fetch audit events")
    print("  audit_events fetch                      - Load existing audit data")
    print("  audit_events delete                     - Delete audit files")
    print("  cloudguard fetch DD-MM-YYYY <days>      - Fetch Cloud Guard problems")
    print("  cloudguard fetch                        - Load existing Cloud Guard data")
    print("  cloudguard delete                       - Delete Cloud Guard files")
    print("    Example: audit_events fetch 15-06-2025 7")
    print("    (Fetches 7 days of data ending on June 15, 2025)")
    print()
    print("Filtering & Analysis:")
    print("  filter age <column> <older|younger> <days>  - Filter by date")
    print("  filter compartment <subcommand>             - Analyze compartments")
    print()
    print("Batch Operations:")
    print("  set queries                    - Load queries from YAML file")
    print("  run queries                    - Execute loaded queries")
    print("  set tenancy                    - Switch to different tenancy")
    print()
    print("Type 'help <command>' for detailed usage or 'exit' to quit.")
    print("=" * 80)

# Register cleanup function to run at exit
def cleanup_at_exit():
    cleanup_combined_config_file()

# -----------------------------------------------------------------------------
def main():
    # Register cleanup function
    atexit.register(cleanup_at_exit)
    
    try:
        # 1) load config & logger
        cfg = ConfigManager()
        log = Logger(level=cfg.get_setting("log_level") or "INFO")

        # 2) initial setup & CLI history
        setup_showoci()
        cmd_history = CommandHistory(".sql_history")

        # 3) build context
        executor = set_tenancy_data(log, cfg)
        ctx = ShellContext(
            query_executor=executor,
            config_manager=cfg,
            logger=log,
            history=cmd_history,
            query_selector=None,
            reload_tenancy_fn=lambda: set_tenancy_data(log, cfg)
        )

        # 4) command registry & parser
        registry = CommandRegistry()
        parser   = CommandParser(registry)
        ctx.registry = registry

        # register commands
        registry.register('show tables', std.ShowTablesCommand)
        registry.register('describe',    std.DescribeCommand)
        registry.register('exit',        std.ExitCommand)
        registry.register('quit',        std.ExitCommand)
        registry.register('history',     std.HistoryCommand)
        registry.register('help',        std.HelpCommand)
        registry.register('filter age',  filt.AgeFilterCommand)
        registry.register('filter compartment', filt.CompartmentFilterCommand)
        registry.register('set queries',       ctl.SetQueriesCommand)
        registry.register('run queries',       ctl.RunQueriesCommand)
        registry.register('set tenancy',       ctl.SetTenancyCommand)
        registry.register('audit_events fetch', audit.AuditEventsFetchCommand)
        registry.register('audit_events delete', audit.AuditEventsDeleteCommand)
        registry.register('cloudguard fetch', CloudGuardFetchCommand)
        registry.register('cloudguard delete', CloudGuardDeleteCommand)
        registry.register('<default>', std.ExecuteSqlCommand)

        # Show startup help
        show_startup_help()

        # 5) REPL
        while True:
            try:
                user_input = input("CMD> ").strip()
                if not user_input:
                    continue

                low = user_input.lower()
                if low in ('exit','quit'):
                    cmd_history.save_history()
                    break
                if low == 'history':
                    cmd_history.show_history()
                    continue
                if user_input.startswith('!'):
                    user_input = cmd_history.get_command(user_input)

                # save it (unless it was a bang-exec)
                if not user_input.startswith('!'):
                    cmd_history.add(user_input)

                cmd_name, args = parser.parse(user_input)
                cmd_cls = registry.get(cmd_name)
                if not cmd_cls:
                    print(f"Unknown command: {cmd_name}")
                    continue

                cmd = cmd_cls(ctx)
                cmd.execute(args)

            except EOFError:
                cmd_history.save_history()
                break
            except KeyboardInterrupt:
                print("\nCancelled.")
            except Exception as e:
                log.log(f"Error: {e}", level="ERROR")

    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        # Ensure cleanup happens
        cleanup_combined_config_file()

if __name__ == "__main__":
    main()