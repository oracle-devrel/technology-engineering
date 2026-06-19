<#
.SYNOPSIS
    Installs and configures Prometheus Monitoring and OCI Management Agent on Windows.
    Now with GCP Multi-Cloud support.

.DESCRIPTION
    This script automates the setup of:
    1. Windows Exporter (for OS metrics).
    2. Prometheus Server (as a Proxy/Aggregator).
    3. OCI Management Agent (to push metrics to Oracle Cloud).
    4. Optional: GCP stackdriver_exporter (to pull metrics from GCP).
    
    It supports two modes:
    - Target: Installs only Windows Exporter.
    - Proxy: Installs Prometheus Server and OCI Management Agent.

.NOTES
    Run as Administrator.
#>

# ---------------------------------------------------------------------------
# GLOBAL VARIABLES & CONSTANTS
# ---------------------------------------------------------------------------

$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir  = Split-Path $ScriptPath
$ConfigFile = Join-Path $ScriptDir "config.json"
$DownloadsDir = Join-Path $ScriptDir "downloads"
$LogsDir = Join-Path $ScriptDir "logs"

# Default Versions
$DefaultWindowsExporterVersion = "0.31.7"
$DefaultPrometheusVersion = "3.12.0"
$DefaultNssmVersion = "2.24"
$DefaultGcpExporterVersion = "0.19.0"
$DefaultOtelVersion = "0.154.0"

# Fallback windows_exporter for legacy OS (pre-Win10 / pre-Server2016).
# 0.31.x requires Win10+/Server2016+; 0.25.1 is the last broadly-compatible build.
$LegacyWindowsExporterVersion = "0.25.1"

# URLs — NSSM is fetched from the official site first, then a durable Internet
# Archive mirror of the same file. nssm.cc intermittently returns HTTP 503, which
# would otherwise abort the whole install, so a mirror removes that single point
# of failure. (NSSM is public domain.) To run fully offline, drop nssm.exe at
# <script dir>\vendor\nssm\win64\nssm.exe and it is used without any download.
$NssmUrls = @(
    "https://nssm.cc/release/nssm-$DefaultNssmVersion.zip",
    "https://web.archive.org/web/2id_/https://nssm.cc/release/nssm-$DefaultNssmVersion.zip"
)

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    $Color = switch ($Level) { "ERROR" { "Red" } "WARN" { "Yellow" } default { "Green" } }
    Write-Host $LogMessage -ForegroundColor $Color
    $LogFile = Join-Path $LogsDir "install.log"
    Add-Content -Path $LogFile -Value $LogMessage
}

function Ensure-Admin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Warning "Script is not running as Administrator. Attempting to elevate..."
        Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" -Verb RunAs
        exit
    }
}

function Load-Config {
    if (Test-Path $ConfigFile) {
        return Get-Content $ConfigFile | ConvertFrom-Json
    }
    return New-Object PSObject
}

function Save-Config {
    param($ConfigObj)
    $ConfigObj | ConvertTo-Json -Depth 5 | Set-Content $ConfigFile
}

function Download-File {
    param([string]$Url, [string]$Dest)
    if (Test-Path $Dest) { return }
    Write-Log "Downloading $Url..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    # Retry transient failures (e.g. nssm.cc has intermittently returned 503).
    for ($i = 1; $i -le 3; $i++) {
        try {
            Invoke-WebRequest -Uri $Url -OutFile $Dest -UseBasicParsing
            if ((Test-Path $Dest) -and (Get-Item $Dest).Length -gt 0) { return }
        } catch {
            Write-Log "Download attempt $i failed for ${Url}: $($_.Exception.Message)" "WARN"
            Start-Sleep -Seconds ($i * 5)
        }
    }
    throw "Failed to download $Url after 3 attempts. Aborting so a half-built install is not left behind."
}

function Expand-Archive-Force {
    param([string]$Path, [string]$Dest)
    Write-Log "Extracting $Path..."
    if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest -ErrorAction SilentlyContinue }
    Expand-Archive -Path $Path -DestinationPath $Dest -Force
}

# ---------------------------------------------------------------------------
# INSTALLATION FUNCTIONS
# ---------------------------------------------------------------------------

function Get-WindowsExporterVersion {
    # windows_exporter 0.31.x requires Windows 10 / Server 2016 (build 10240) or newer.
    # On older OS (Win 8.1 = 6.3, Server 2012 R2), fall back to a compatible build.
    $os = [Environment]::OSVersion.Version
    $isWin10Plus = ($os.Major -gt 10) -or ($os.Major -eq 10)
    if ($isWin10Plus) {
        return $DefaultWindowsExporterVersion
    }
    Write-Log "Detected legacy Windows ($($os.Major).$($os.Minor)). Using windows_exporter v$LegacyWindowsExporterVersion for compatibility." "WARN"
    return $LegacyWindowsExporterVersion
}

function Install-NSSM {
    $ExtractDir = Join-Path $DownloadsDir "nssm"
    $TargetExe  = Join-Path $ExtractDir "nssm-$DefaultNssmVersion\win64\nssm.exe"
    if (Test-Path $TargetExe) { return }

    # 1) Offline/bundled nssm.exe shipped next to the script.
    $Bundled = Join-Path $ScriptDir "vendor\nssm\win64\nssm.exe"
    if (Test-Path $Bundled) {
        Write-Log "Using bundled nssm.exe ($Bundled)"
        New-Item -ItemType Directory -Path (Split-Path $TargetExe) -Force | Out-Null
        Copy-Item $Bundled $TargetExe -Force
        return
    }

    # 2) Download from the first reachable source (official site, then mirror).
    $ZipPath = Join-Path $DownloadsDir "nssm.zip"
    $got = $false
    foreach ($u in $NssmUrls) {
        if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue }
        try { Download-File -Url $u -Dest $ZipPath; $got = $true; break }
        catch { Write-Log "NSSM source unavailable: $u" "WARN" }
    }
    if (-not $got) { throw "Could not obtain NSSM from any source. Ship vendor\nssm\win64\nssm.exe next to the script for offline installs." }
    Expand-Archive-Force -Path $ZipPath -Dest $ExtractDir
    if (-not (Test-Path $TargetExe)) { throw "nssm.exe not found after extraction at $TargetExe" }
}

function Invoke-Msi {
    param([string]$Arguments, [string]$Name = "MSI")
    # msiexec exit codes: 0 = ok, 3010/1641 = ok (reboot), 1618 = another
    # install in progress. At first boot the OS / Oracle Cloud Agent may be
    # running their own installers, so retry on 1618 instead of silently
    # leaving the product uninstalled.
    for ($i = 1; $i -le 10; $i++) {
        $p = Start-Process msiexec.exe -ArgumentList $Arguments -Wait -PassThru
        $code = $p.ExitCode
        if ($code -eq 0 -or $code -eq 3010 -or $code -eq 1641) { return }
        if ($code -eq 1618) {
            Write-Log "$Name install: Windows Installer busy (1618), waiting (attempt $i)..." "WARN"
            Start-Sleep -Seconds 30
            continue
        }
        throw "$Name install failed (msiexec exit code $code)."
    }
    throw "$Name install failed: Windows Installer stayed busy (1618) after 10 attempts."
}

function Install-WindowsExporter {
    param($Version, $Port)
    $Url = "https://github.com/prometheus-community/windows_exporter/releases/download/v$Version/windows_exporter-$Version-amd64.msi"
    $MsiPath = Join-Path $DownloadsDir "windows_exporter.msi"
    Download-File -Url $Url -Dest $MsiPath
    Write-Log "Installing Windows Exporter..."
    # Note: the legacy 'cs' collector was removed in current windows_exporter
    # releases (its data moved to cpu_info/memory). Including it makes the
    # service fail to start with "unknown collector cs".
    $Collectors = "cpu,cpu_info,logical_disk,net,os,service,system,textfile,memory,tcp,udp"
    $Args = "/i `"$MsiPath`" LISTEN_PORT=$Port ENABLED_COLLECTORS=`"$Collectors`" /qn"
    Invoke-Msi -Arguments $Args -Name "windows_exporter"
    # Ensure the service is actually running before moving on.
    Start-Sleep -Seconds 3
    $svc = Get-Service windows_exporter -ErrorAction SilentlyContinue
    if (-not $svc) { throw "windows_exporter service not present after MSI install." }
    if ($svc.Status -ne 'Running') { Start-Service windows_exporter -ErrorAction SilentlyContinue }
    New-NetFirewallRule -DisplayName "Prometheus Windows Exporter" -Direction Inbound -LocalPort $Port -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
}

function Install-GCPExporter {
    param($Version, $ProjectId, $CredentialsPath, $MetricPrefixes)
    
    $Url = "https://github.com/prometheus-community/stackdriver_exporter/releases/download/v$Version/stackdriver_exporter-$Version.windows-amd64.tar.gz"
    $TarPath = Join-Path $DownloadsDir "gcp_exporter.tar.gz"
    $InstallDir = "C:\GCPExporter"
    
    Download-File -Url $Url -Dest $TarPath
    
    $TempExtract = Join-Path $DownloadsDir "gcp_temp"
    if (Test-Path $TempExtract) { Remove-Item -Recurse -Force $TempExtract }
    New-Item -ItemType Directory -Path $TempExtract | Out-Null
    
    Write-Log "Extracting GCP Exporter (tar)..."
    tar -xf $TarPath -C $TempExtract
    
    if (-not (Test-Path $InstallDir)) { New-Item -ItemType Directory -Path $InstallDir | Out-Null }
    $InnerFolder = Get-ChildItem $TempExtract | Where-Object { $_.PSIsContainer } | Select-Object -First 1
    Copy-Item -Path "$($InnerFolder.FullName)\stackdriver_exporter.exe" -Destination $InstallDir -Force
    
    Install-NSSM
    $NssmExe = Join-Path $DownloadsDir "nssm\nssm-$DefaultNssmVersion\win64\nssm.exe"
    $ExePath = Join-Path $InstallDir "stackdriver_exporter.exe"
    
    & $NssmExe stop GCPExporter 2>&1 | Out-Null
    & $NssmExe remove GCPExporter confirm 2>&1 | Out-Null
    
    Write-Log "Installing GCP Exporter Service..."
    $Args = "--google.project-id=`"$ProjectId`""
    if ($MetricPrefixes) { $Args += " --monitoring.metrics-type-prefixes=`"$MetricPrefixes`"" }
    
    & $NssmExe install GCPExporter "$ExePath" "$Args"
    & $NssmExe set GCPExporter AppDirectory "$InstallDir"
    & $NssmExe set GCPExporter AppEnvironmentExtra "GOOGLE_APPLICATION_CREDENTIALS=$CredentialsPath"
    & $NssmExe start GCPExporter
}

function Install-Prometheus {
    param($Version, $Port, $Targets, $GcpEnabled)
    $Url = "https://github.com/prometheus/prometheus/releases/download/v$Version/prometheus-$Version.windows-amd64.zip"
    $ZipPath = Join-Path $DownloadsDir "prometheus.zip"
    $InstallDir = "C:\Prometheus"
    Download-File -Url $Url -Dest $ZipPath
    $TempExtract = Join-Path $DownloadsDir "prometheus_temp"
    Expand-Archive-Force -Path $ZipPath -Dest $TempExtract
    if (-not (Test-Path $InstallDir)) { New-Item -ItemType Directory -Path $InstallDir | Out-Null }
    $InnerFolder = Get-ChildItem $TempExtract | Where-Object { $_.PSIsContainer } | Select-Object -First 1
    Copy-Item -Path "$($InnerFolder.FullName)\*" -Destination $InstallDir -Recurse -Force
    
    $ConfigPath = Join-Path $InstallDir "prometheus.yml"
    $Yaml = "global:`n  scrape_interval: 15s`n`nscrape_configs:`n  - job_name: 'prometheus'`n    static_configs:`n      - targets: ['localhost:$Port']"
    # The proxy also runs windows_exporter; scrape it so the proxy self-monitors.
    $Yaml += "`n`n  - job_name: 'windows_proxy'`n    static_configs:`n      - targets: ['localhost:9182']"
    if ($Targets) {
        $TString = $Targets -join "','"
        $Yaml += "`n`n  - job_name: 'nodes'`n    static_configs:`n      - targets: ['$TString']"
    }
    if ($GcpEnabled) {
        $Yaml += "`n`n  - job_name: 'gcp'`n    scrape_interval: 1m`n    static_configs:`n      - targets: ['localhost:9255']"
    }
    Set-Content -Path $ConfigPath -Value $Yaml

    Install-NSSM
    $NssmExe = Join-Path $DownloadsDir "nssm\nssm-$DefaultNssmVersion\win64\nssm.exe"
    $PromExe = Join-Path $InstallDir "prometheus.exe"
    & $NssmExe stop Prometheus 2>&1 | Out-Null
    & $NssmExe remove Prometheus confirm 2>&1 | Out-Null
    & $NssmExe install Prometheus "$PromExe" "--config.file=$ConfigPath --web.listen-address=0.0.0.0:$Port"
    & $NssmExe start Prometheus
    New-NetFirewallRule -DisplayName "Prometheus Server" -Direction Inbound -LocalPort $Port -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
}

function Install-OTELCollector {
    param($Version, $PrometheusPort, $OtlpEndpoint, $PromRemoteWriteEndpoint, $Headers, $Insecure)
    # Second export path: an OpenTelemetry Collector scrapes the local Prometheus
    # /federate endpoint and forwards everything as OTEL metrics (OTLP/HTTP) and/or
    # Prometheus remote_write to the user's collector / Prometheus / Grafana / 3rd party.
    $Url = "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v$Version/otelcol-contrib_${Version}_windows_amd64.tar.gz"
    $TarPath = Join-Path $DownloadsDir "otelcol.tar.gz"
    $InstallDir = "C:\OTELCollector"
    Download-File -Url $Url -Dest $TarPath
    if (-not (Test-Path $InstallDir)) { New-Item -ItemType Directory -Path $InstallDir | Out-Null }
    Write-Log "Extracting OTEL Collector..."
    tar -xf $TarPath -C $InstallDir
    $ExePath = Join-Path $InstallDir "otelcol-contrib.exe"
    if (-not (Test-Path $ExePath)) { throw "otelcol-contrib.exe not found after extraction." }

    $insecureBool = if ($Insecure) { "true" } else { "false" }
    # Build exporter list + headers block from config.
    $exporters = @()
    $expNames = @()
    if ($OtlpEndpoint) {
        $hdr = ""
        if ($Headers) { $hdr = "`n    headers:`n      $($Headers)" }
        $exporters += "  otlphttp:`n    endpoint: `"$OtlpEndpoint`"`n    tls:`n      insecure: $insecureBool$hdr"
        $expNames += "otlphttp"
    }
    if ($PromRemoteWriteEndpoint) {
        $exporters += "  prometheusremotewrite:`n    endpoint: `"$PromRemoteWriteEndpoint`"`n    tls:`n      insecure: $insecureBool"
        $expNames += "prometheusremotewrite"
    }
    if ($expNames.Count -eq 0) { throw "OTEL enabled but no OtlpEndpoint or OtelPromRemoteWriteEndpoint configured." }
    $expBlock = $exporters -join "`n"
    $expList = $expNames -join ", "

    $ConfigPath = Join-Path $InstallDir "config.yaml"
    $Yaml = @"
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-federate'
          honor_labels: true
          metrics_path: /federate
          params:
            'match[]': ['{job=~".+"}']
          scrape_interval: 30s
          static_configs:
            - targets: ['localhost:$PrometheusPort']
processors:
  batch: {}
exporters:
$expBlock
service:
  pipelines:
    metrics:
      receivers: [prometheus]
      processors: [batch]
      exporters: [$expList]
"@
    Set-Content -Path $ConfigPath -Value $Yaml -Encoding ascii

    Install-NSSM
    $NssmExe = Join-Path $DownloadsDir "nssm\nssm-$DefaultNssmVersion\win64\nssm.exe"
    & $NssmExe stop OTELCollector 2>&1 | Out-Null
    & $NssmExe remove OTELCollector confirm 2>&1 | Out-Null
    & $NssmExe install OTELCollector "$ExePath" "--config=`"$ConfigPath`""
    & $NssmExe set OTELCollector AppDirectory "$InstallDir"
    & $NssmExe start OTELCollector
    Write-Log "OTEL Collector installed; exporting via: $expList"
}

function Install-OCIAgent {
    param($AgentZipPathOrUrl, $RspPath)
    Ensure-Java8
    $LocalZip = Join-Path $DownloadsDir "agent.zip"
    if ($AgentZipPathOrUrl -match "^http") { Download-File -Url $AgentZipPathOrUrl -Dest $LocalZip }
    else { Copy-Item $AgentZipPathOrUrl $LocalZip -Force }
    $ExtDir = Join-Path $DownloadsDir "agent_extract"
    Expand-Archive-Force -Path $LocalZip -Dest $ExtDir
    $Installer = Get-ChildItem -Path $ExtDir -Recurse -Filter "installer.bat" | Select-Object -First 1
    if (-not $Installer) { throw "installer.bat not found in agent zip." }
    # The OCI Management Agent installer.bat takes the response file POSITIONALLY:
    #   installer.bat <Full_Path_To_Input.rsp>
    # (The previous 'Correlation.rspFile=' form is not how this installer parses args.)
    Write-Log "Running agent installer: $($Installer.FullName) `"$RspPath`""
    Start-Process -FilePath $Installer.FullName -ArgumentList "`"$RspPath`"" -Wait -NoNewWindow
}

function Ensure-Java8 {
    # The OCI Management Agent installer requires JAVA_HOME to be set in the
    # environment; an MSI-installed JDK does not propagate it to the current
    # process, so we always (re)resolve and export it.
    $existing = Get-ChildItem 'C:\Program Files\Amazon Corretto' -Directory -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending | Select-Object -First 1
    if (-not $existing) {
        $Url = "https://corretto.aws/downloads/latest/amazon-corretto-8-x64-windows-jdk.msi"
        $Msi = Join-Path $DownloadsDir "java8.msi"
        Download-File -Url $Url -Dest $Msi
        Write-Log "Installing Amazon Corretto 8 (JDK)..."
        Invoke-Msi -Arguments "/i `"$Msi`" /qn" -Name "Amazon Corretto 8"
        $existing = Get-ChildItem 'C:\Program Files\Amazon Corretto' -Directory -ErrorAction SilentlyContinue |
                    Sort-Object Name -Descending | Select-Object -First 1
    }
    if (-not $existing) { throw "Java 8 (Corretto) not found after install; cannot configure the OCI agent." }
    $JavaHome = $existing.FullName
    [Environment]::SetEnvironmentVariable('JAVA_HOME', $JavaHome, 'Machine')
    $env:JAVA_HOME = $JavaHome
    $env:Path = "$JavaHome\bin;$env:Path"
    Write-Log "JAVA_HOME set to $JavaHome"
}

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

Ensure-Admin
New-Item -ItemType Directory -Path $DownloadsDir, $LogsDir -Force | Out-Null
$Config = Load-Config

Write-Host "`nOCI Prometheus Multi-Cloud Installer`n" -ForegroundColor Cyan

if (-not $Config.Mode) { $Config.Mode = Read-Host "Select Mode [Target/Proxy]" }

$WinExporterVersion = Get-WindowsExporterVersion

if ($Config.Mode -eq "Target") {
    if (-not $Config.ExporterPort) { $Config.ExporterPort = "9182" }
    Install-WindowsExporter -Version $WinExporterVersion -Port $Config.ExporterPort
} else {
    # Proxy Mode
    if (-not $Config.PrometheusPort) { $Config.PrometheusPort = "9090" }
    if (-not $Config.TargetNodes) {
        $inp = Read-Host "Enter Target Node IPs (comma separated)"
        if ($inp) { $Config.TargetNodes = $inp -split "," | ForEach-Object { $_.Trim() } }
    }
    
    # GCP Option
    if ($null -eq $Config.GcpEnabled) {
        $Config.GcpEnabled = (Read-Host "Enable GCP Monitoring? [y/n]") -eq 'y'
    }
    if ($Config.GcpEnabled) {
        if (-not $Config.GcpProjectId) { $Config.GcpProjectId = Read-Host "GCP Project ID" }
        if (-not $Config.GcpCredsPath) { $Config.GcpCredsPath = Read-Host "Path to GCP Service Account JSON" }
        if (-not $Config.GcpMetricPrefixes) { 
            Write-Host "Enter GCP Metric Prefixes (comma separated, e.g., 'compute.googleapis.com/instance/cpu')" -ForegroundColor Gray
            $Config.GcpMetricPrefixes = Read-Host "Prefixes (leave empty for all)" 
        }
    }

    # OCI Monitoring option — push the aggregated metrics to OCI Monitoring via the
    # OCI Management Agent. OPTIONAL: leave it disabled to run the proxy purely as an
    # OpenTelemetry/remote_write exporter to a non-OCI backend (Prometheus, Grafana,
    # Datadog, …). Only when enabled do we prompt for the agent zip + response file.
    if ($null -eq $Config.OciMonitoringEnabled) {
        $Config.OciMonitoringEnabled = (Read-Host "Push metrics to OCI Monitoring via the Management Agent? [y/n]") -eq 'y'
    }
    if ($Config.OciMonitoringEnabled) {
        if (-not $Config.AgentZipPathOrUrl) { $Config.AgentZipPathOrUrl = Read-Host "OCI Agent ZIP Path/URL" }
        if (-not $Config.RspFilePath) { $Config.RspFilePath = Read-Host "OCI Agent .rsp File Path" }
    }

    # OTEL export option — forward all metrics as OTEL/remote_write to a user tool.
    if ($null -eq $Config.OtelEnabled) {
        $Config.OtelEnabled = (Read-Host "Export metrics via OpenTelemetry Collector? [y/n]") -eq 'y'
    }
    if ($Config.OtelEnabled) {
        if ($null -eq $Config.OtelOtlpEndpoint) {
            $Config.OtelOtlpEndpoint = Read-Host "OTLP/HTTP endpoint (e.g. http://collector:4318) [empty to skip]"
        }
        if ($null -eq $Config.OtelPromRemoteWriteEndpoint) {
            $Config.OtelPromRemoteWriteEndpoint = Read-Host "Prometheus remote_write endpoint (e.g. http://prom:9090/api/v1/write) [empty to skip]"
        }
    }

    if (-not $Config.ExporterPort) { $Config.ExporterPort = "9182" }
    Install-WindowsExporter -Version $WinExporterVersion -Port $Config.ExporterPort
    if ($Config.GcpEnabled) {
        Install-GCPExporter -Version $DefaultGcpExporterVersion -ProjectId $Config.GcpProjectId -CredentialsPath $Config.GcpCredsPath -MetricPrefixes $Config.GcpMetricPrefixes
    }
    Install-Prometheus -Version $DefaultPrometheusVersion -Port $Config.PrometheusPort -Targets $Config.TargetNodes -GcpEnabled $Config.GcpEnabled
    if ($Config.OtelEnabled) {
        Install-OTELCollector -Version $DefaultOtelVersion -PrometheusPort $Config.PrometheusPort `
            -OtlpEndpoint $Config.OtelOtlpEndpoint -PromRemoteWriteEndpoint $Config.OtelPromRemoteWriteEndpoint `
            -Headers $Config.OtelHeaders -Insecure $true
    }
    if ($Config.OciMonitoringEnabled) {
        Install-OCIAgent -AgentZipPathOrUrl $Config.AgentZipPathOrUrl -RspPath $Config.RspFilePath
    }

    if (-not $Config.OciMonitoringEnabled -and -not $Config.OtelEnabled) {
        Write-Log "No export path is enabled (OCI Monitoring and OTEL both off). The proxy aggregates metrics at /federate but forwards them nowhere. Enable OciMonitoringEnabled and/or OtelEnabled to export." "WARN"
    }

    Write-Host "`nDONE." -ForegroundColor Yellow
    if ($Config.OciMonitoringEnabled) {
        Write-Host "Add a Prometheus data source to the OCI Management Agent that scrapes the FEDERATE" -ForegroundColor Yellow
        Write-Host "endpoint so the aggregated target metrics are forwarded (NOT /metrics, which only" -ForegroundColor Yellow
        Write-Host "exposes Prometheus' own telemetry):" -ForegroundColor Yellow
        Write-Host "  http://localhost:$($Config.PrometheusPort)/federate?match[]={job=~`".+`"}" -ForegroundColor Cyan
        Write-Host "e.g. via OCI CLI:" -ForegroundColor Yellow
        Write-Host "  oci management-agent agent create-prometheus-datasource --management-agent-id <agent> \" -ForegroundColor Cyan
        Write-Host "    --compartment-id <cmpt> --name proxy_prometheus --namespace my_prometheus \" -ForegroundColor Cyan
        Write-Host "    --url 'http://localhost:$($Config.PrometheusPort)/federate?match%5B%5D=%7Bjob%3D~%22.%2B%22%7D' --schedule-mins 1" -ForegroundColor Cyan
        Write-Host "Or use manage-oci-datasource.sh (list / idempotent create / destroy) from a host with the OCI CLI." -ForegroundColor Yellow
    }
    if ($Config.OtelEnabled) {
        Write-Host "OpenTelemetry export is enabled. The OTEL Collector federates from Prometheus" -ForegroundColor Yellow
        Write-Host "(http://localhost:$($Config.PrometheusPort)/federate) and forwards metrics to:" -ForegroundColor Yellow
        if ($Config.OtelOtlpEndpoint) { Write-Host "  OTLP/HTTP    -> $($Config.OtelOtlpEndpoint)" -ForegroundColor Cyan }
        if ($Config.OtelPromRemoteWriteEndpoint) { Write-Host "  remote_write -> $($Config.OtelPromRemoteWriteEndpoint)" -ForegroundColor Cyan }
        Write-Host "Verify the series arrive at your backend (e.g. otel-destination/ test stack)." -ForegroundColor Yellow
    }
}

Save-Config -ConfigObj $Config
# Only pause for a keypress when running interactively (avoids blocking unattended/cloud-init runs).
if ([Environment]::UserInteractive -and $Host.Name -eq 'ConsoleHost') { Read-Host "Press Enter to exit" }