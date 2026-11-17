#!/usr/bin/env bash
# Comparative COLOCATION_TAG workload test for ADB-D. Uses SQLcl (sql).
set -euo pipefail
umask 077
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${1:-$SCRIPT_DIR/config.env}"
[[ -r "$CONFIG_FILE" ]] || { echo "Missing config: $CONFIG_FILE" >&2; exit 2; }
# shellcheck disable=SC1090
source "$CONFIG_FILE"
: "${DB_USER:?}"; : "${DB_PASSWORD:?}"; : "${BASE_CONNECT_STRING:?}"
: "${SESSION_COUNT:=32}"
: "${WORKLOAD_SECONDS:=60}"; : "${COMMIT_EVERY:=10}"
: "${MAX_PARALLEL:=16}"; : "${RUNS:=4}"; : "${SQL_BIN:=sql}"
: "${AWR:=n}"
for n in SESSION_COUNT WORKLOAD_SECONDS COMMIT_EVERY MAX_PARALLEL RUNS; do
  [[ ${!n} =~ ^[1-9][0-9]*$ ]] || { echo "$n must be a positive integer" >&2; exit 2; }
done
TAGGED_TAG='C_TAGGED'
AWR="${AWR,,}"
[[ $AWR == y || $AWR == n ]] || { echo 'AWR must be y or n' >&2; exit 2; }
[[ $BASE_CONNECT_STRING =~ \(CONNECT_DATA[[:space:]]*= ]] || { echo 'BASE_CONNECT_STRING needs CONNECT_DATA' >&2; exit 2; }
[[ ! $BASE_CONNECT_STRING =~ COLOCATION_TAG[[:space:]]*= ]] || { echo 'Remove existing COLOCATION_TAG from BASE_CONNECT_STRING' >&2; exit 2; }
command -v "$SQL_BIN" >/dev/null || { echo "SQLcl executable not found: $SQL_BIN" >&2; exit 2; }

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)_$$"; OUT="$SCRIPT_DIR/results/$RUN_ID"; mkdir -p "$OUT/raw"
WORKERS="$OUT/workers.psv"; SNAPSHOTS="$OUT/metrics_snapshots.psv"; FAILURES="$OUT/failures.log"
printf 'run|phase|tag|ordinal|instance_number|instance_name|ops|elapsed_cs\n' > "$WORKERS"
printf 'run|phase|point|metric_type|instance_number|metric_name|metric_value\n' > "$SNAPSHOTS"
if [[ $AWR == y ]]; then
  AWR_DIR="$OUT/awr"; AWR_SNAPSHOTS="$AWR_DIR/snapshots.psv"; AWR_PAIRS="$AWR_DIR/report_pairs.psv"; mkdir -p "$AWR_DIR"
  printf 'run|phase|point|dbid|snap_id|end_interval_utc\n' > "$AWR_SNAPSHOTS"
fi

descriptor() { # $1 is tag, blank means untagged control
  [[ -z $1 ]] && { printf '%s' "$BASE_CONNECT_STRING"; return; }
  BASE_DESCRIPTOR="$BASE_CONNECT_STRING" COLOCATION_TAG_VALUE="$1" perl -0777 -e '
    $d=$ENV{BASE_DESCRIPTOR}; $t=$ENV{COLOCATION_TAG_VALUE};
    $d =~ s/(\(CONNECT_DATA\s*=)/$1(COLOCATION_TAG=$t)/i or die "CONNECT_DATA not found\n"; print $d;'
}
sqlcl() { "$SQL_BIN" -s /nolog; }

# Descriptors are printed for reproducibility. They intentionally exclude the
# database user and password, which are never part of an Oracle Net descriptor.
echo "CONTROL connect descriptor: $BASE_CONNECT_STRING"
echo "TAGGED connect descriptor (${TAGGED_TAG}): $(descriptor "$TAGGED_TAG")"
echo "AWR add-on: $AWR"

# Captures RAC-wide counters. This intentionally fails fast: a comparison without
# GC counters demonstrates routing, but cannot demonstrate reduced interconnect work.
capture() {
  local run=$1 phase=$2 point=$3 output rc
  set +e
  output="$(sqlcl <<SQL
whenever oserror exit 9
whenever sqlerror exit sql.sqlcode
connect ${DB_USER}/"${DB_PASSWORD}"@${BASE_CONNECT_STRING}
set pages 0 feedback off heading off verify off echo off trims on lines 1000
select '${run}|${phase}|${point}|EVENT_WAIT_US|'||inst_id||'|'||replace(event,'|','/')||'|'||time_waited_micro
  from gv\$system_event where wait_class='Cluster' or event like 'gc %';
select '${run}|${phase}|${point}|EVENT_WAITS|'||inst_id||'|'||replace(event,'|','/')||'|'||total_waits
  from gv\$system_event where wait_class='Cluster' or event like 'gc %';
select '${run}|${phase}|${point}|STAT|'||inst_id||'|'||replace(name,'|','/')||'|'||value
  from gv\$sysstat where name in ('gc cr blocks received','gc current blocks received',
                                 'gc cr blocks served','gc current blocks served');
exit
SQL
)"; rc=$?; set -e
  ((rc==0)) || { printf 'metric capture %s/%s/%s failed:\n%s\n' "$run" "$phase" "$point" "$output" >> "$FAILURES"; return "$rc"; }
  printf '%s\n' "$output" | awk -F'|' 'NF==7 {gsub(/^[[:space:]]+|[[:space:]]+$/,""); print}' >> "$SNAPSHOTS"
}

# Creates an explicit AWR snapshot and records the ID returned by CREATE_SNAPSHOT.
# This avoids accidentally selecting an automatic or concurrent snapshot.
capture_awr_snapshot() {
  local run=$1 phase=$2 point=$3 output rc
  [[ $AWR == y ]] || return 0
  echo "Creating AWR snapshot: run $run phase $phase $point"
  set +e
  output="$(sqlcl <<SQL
whenever oserror exit 9
whenever sqlerror exit sql.sqlcode
connect ${DB_USER}/"${DB_PASSWORD}"@${BASE_CONNECT_STRING}
variable awr_snap_id number
begin :awr_snap_id := dbms_workload_repository.create_snapshot; end;
/
set pages 0 feedback off heading off verify off echo off trims on lines 1000
select '${run}|${phase}|${point}|'||dbms_workload_repository.local_awr_dbid()||'|'||
       :awr_snap_id||'|'||to_char(systimestamp at time zone 'UTC','YYYY-MM-DD"T"HH24:MI:SS.FF3"Z"')
  from dual;
exit
SQL
)"; rc=$?; set -e
  ((rc==0)) || { printf 'AWR snapshot run=%s phase=%s point=%s failed:\n%s\n' "$run" "$phase" "$point" "$output" >> "$FAILURES"; return "$rc"; }
  output="$(printf '%s\n' "$output" | awk -F'|' 'NF == 6 {gsub(/^[[:space:]]+|[[:space:]]+$/, ""); print; exit}')"
  [[ -n $output ]] || { printf 'AWR snapshot run=%s phase=%s point=%s returned no snapshot row\n' "$run" "$phase" "$point" >> "$FAILURES"; return 92; }
  printf '%s\n' "$output" >> "$AWR_SNAPSHOTS"
}

worker() {
  local run=$1 phase=$2 ordinal=$3 tag='' out rc desc
  [[ $phase == TAGGED ]] && tag="$TAGGED_TAG"
  desc="$(descriptor "$tag")"
  set +e
  out="$(sqlcl <<SQL
whenever oserror exit 9
whenever sqlerror exit sql.sqlcode
connect ${DB_USER}/"${DB_PASSWORD}"@${desc}
set serveroutput on size unlimited pages 0 feedback off heading off verify off echo off
begin ct_colocation_workload.run_worker(${WORKLOAD_SECONDS}, ${COMMIT_EVERY}); end;
/
exit
SQL
)"; rc=$?; set -e
  ((rc==0)) || { printf 'worker run=%s phase=%s ordinal=%s rc=%s\n%s\n' "$run" "$phase" "$ordinal" "$rc" "$out" >> "$FAILURES"; return "$rc"; }
  out="$(printf '%s\n' "$out" | awk -F'|' '/^RESULT\|/ {print; exit}')"
  [[ -n $out ]] || { printf 'worker emitted no RESULT: run=%s phase=%s ordinal=%s\n%s\n' "$run" "$phase" "$ordinal" "$out" >> "$FAILURES"; return 91; }
  # RESULT|instance#|instance_name|operations|elapsed_centiseconds
  IFS='|' read -r _ inst ino ops elapsed <<< "$out"
  printf '%s|%s|%s|%s|%s|%s|%s|%s\n' "$run" "$phase" "${tag:-UNTAGGED}" "$ordinal" "$inst" "$ino" "$ops" "$elapsed" >> "$WORKERS"
}
wait_slot() { while (( $(jobs -rp | wc -l | tr -d ' ') >= MAX_PARALLEL )); do wait -n || true; done; }
phase() {
  local run=$1 name=$2 i
  echo "Starting run $run phase $name"
  capture_awr_snapshot "$run" "$name" BEFORE
  capture "$run" "$name" BEFORE
  for ((i=1; i<=SESSION_COUNT; i++)); do
    wait_slot; worker "$run" "$name" "$i" >"$OUT/raw/${run}_${name}_${i}.log" 2>&1 &
  done
  wait || true
  capture "$run" "$name" AFTER
  capture_awr_snapshot "$run" "$name" AFTER
}

# Reset the base table only between complete runs, never between CONTROL and
# TAGGED phases. Keeping the sequence intact preserves unique increasing keys.
truncate_base_table() {
  local run=$1 output rc
  echo "Truncating CT_COLOCATION_INSERT_LOG after run $run"
  set +e
  output="$(sqlcl <<SQL
whenever oserror exit 9
whenever sqlerror exit sql.sqlcode
connect ${DB_USER}/"${DB_PASSWORD}"@${BASE_CONNECT_STRING}
truncate table ct_colocation_insert_log drop storage;
exit
SQL
)"; rc=$?; set -e
  ((rc==0)) || { printf 'truncate after run=%s failed:\n%s\n' "$run" "$output" >> "$FAILURES"; return "$rc"; }
}

for ((run=1; run<=RUNS; run++)); do
  # Alternate ordering to reduce cache warm-up/order bias.
  if (( run % 2 )); then phase "$run" CONTROL; phase "$run" TAGGED; else phase "$run" TAGGED; phase "$run" CONTROL; fi
  if (( run < RUNS )); then truncate_base_table "$run"; fi
done

generate_awr_reports() {
  local run phase dbid begin_snap end_snap report output rc report_count=0 expected_reports
  [[ $AWR == y ]] || return 0
  printf 'run|phase|dbid|begin_snap_id|end_snap_id\n' > "$AWR_PAIRS"
  awk -F'|' '
    NR == 1 {next}
    $3 == "BEFORE" {dbid[$1 FS $2] = $4; begin[$1 FS $2] = $5}
    $3 == "AFTER" {k = $1 FS $2; if (k in begin && dbid[k] == $4 && begin[k] != $5) print $1 FS $2 FS $4 FS begin[k] FS $5}
  ' "$AWR_SNAPSHOTS" | sort -t'|' -k1,1n -k2,2 >> "$AWR_PAIRS"
  while IFS='|' read -r run phase dbid begin_snap end_snap; do
    [[ -n $run ]] || continue
    report="$AWR_DIR/awr_global_run${run}_${phase}_snap${begin_snap}-${end_snap}.html"
    echo "Generating AWR global report: $(basename "$report")"
    set +e
    output="$(sqlcl <<SQL
whenever oserror exit 9
whenever sqlerror exit sql.sqlcode
connect ${DB_USER}/"${DB_PASSWORD}"@${BASE_CONNECT_STRING}
set pages 0 feedback off heading off verify off echo off trims on lines 32767 long 1000000000 longchunksize 32767
spool $report
select output
  from table(dbms_workload_repository.awr_global_report_html(
    ${dbid}, cast(null as varchar2(1)), ${begin_snap}, ${end_snap}, 0));
spool off
exit
SQL
)"; rc=$?; set -e
    ((rc==0)) || { printf 'AWR report run=%s phase=%s snaps=%s-%s failed:\n%s\n' "$run" "$phase" "$begin_snap" "$end_snap" "$output" >> "$FAILURES"; return "$rc"; }
    ((++report_count))
  done < <(awk -F'|' 'NR > 1 {print}' "$AWR_PAIRS")
  expected_reports=$(( RUNS * 2 ))
  (( report_count == expected_reports )) || { printf 'AWR report pairing incomplete: generated=%s expected=%s\n' "$report_count" "$expected_reports" >> "$FAILURES"; return 93; }
  echo "Generated $report_count AWR global report(s) in $AWR_DIR"
}

generate_awr_reports

awk -F'|' '
  NR==1 {next} {k=$1 FS $2; n[k]++; ops[k]+=$7; inst[k FS $5]=1}
  END {print "run|phase|successful_workers|operations|distinct_instances|ops_per_worker";
       for(k in n){c=0; for(i in inst) if(index(i,k FS)==1)c++; printf "%s|%d|%.0f|%d|%.1f\n",k,n[k],ops[k],c,ops[k]/n[k]}}
' "$WORKERS" | sort -t'|' -k1,1n -k2,2 > "$OUT/workload_summary.psv"
awk -F'|' '
  NR==1{next} {k=$1 FS $2 FS $4 FS $5 FS $6; if($3=="BEFORE") b[k]=$7; else if($3=="AFTER" && k in b) d[k]=$7-b[k]}
  END {print "run|phase|metric_type|metric_name|delta"; for(k in d){split(k,a,FS); print a[1] FS a[2] FS a[3] FS a[5] FS d[k]}}
' "$SNAPSHOTS" | sort -t'|' -k1,1n -k2,2 -k3,3 -k4,4 > "$OUT/metric_deltas.psv"
awk -F'|' 'NR==FNR {if(NR>1) ops[$1 FS $2]=$4; next} NR>1 && $3=="EVENT_WAIT_US" && $4 ~ /^gc / {k=$1 FS $2; if(ops[k]>0) print $1"|"$2"|"$4"|"$5"|"ops[k]"|"($5/ops[k])}' "$OUT/workload_summary.psv" "$OUT/metric_deltas.psv" > "$OUT/gc_event_per_operation.psv"
awk -F'|' '
  NR==FNR {if(NR>1) ops[$1 FS $2]=$4; next}
  NR>1 && $4 ~ /^gc / {k=$1 FS $2; if($3=="EVENT_WAIT_US") time_us[k]+=$5; else if($3=="EVENT_WAITS") waits[k]+=$5}
  END {print "run|phase|gc_waits|gc_wait_time_us|average_gc_wait_us|average_gc_wait_ms|gc_wait_us_per_operation";
       for(k in time_us) {split(k,a,FS); avg=(waits[k] ? time_us[k]/waits[k] : 0); per_op=(ops[k] ? time_us[k]/ops[k] : 0);
         printf "%s|%.0f|%.0f|%.3f|%.6f|%.3f\n",k,waits[k],time_us[k],avg,avg/1000,per_op}}
' "$OUT/workload_summary.psv" "$OUT/metric_deltas.psv" | sort -t'|' -k1,1n -k2,2 > "$OUT/gc_wait_summary.psv"

echo "Results: $OUT"
column -t -s '|' "$OUT/workload_summary.psv" 2>/dev/null || cat "$OUT/workload_summary.psv"
echo "Average wait across all gc% events (delta during each phase):"
column -t -s '|' "$OUT/gc_wait_summary.psv" 2>/dev/null || cat "$OUT/gc_wait_summary.psv"
echo "Compare CONTROL vs TAGGED in $OUT/gc_event_per_operation.psv (lower tagged GC wait microseconds/op is the target)."
[[ ! -s $FAILURES ]]
