##########################################################################
# Copyright (c) 2026, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
##########################################################################
#
# nist_reports.py
#
# Helpers for enriching OCI CIS report output with NIST SP 800-53 mappings.
#
##########################################################################

from __future__ import print_function

import argparse
import ast
import csv
import glob
import html
import json
import os
import re
import shutil
import tempfile
import zipfile
from decimal import Decimal, InvalidOperation


class NISTMappings:
    DEFAULT_MAPPING_FILE = "nist_mappings.json"
    DEFAULT_CIS_FIELD = "CIS v8"
    DEFAULT_NIST_FIELD = "NIST Controls"

    def __init__(self, mapping_file=None):
        if mapping_file is None:
            mapping_file = os.path.join(os.path.dirname(__file__), self.DEFAULT_MAPPING_FILE)

        self.mapping_file = mapping_file
        with open(self.mapping_file, mode="r", encoding="ascii") as mapping_handle:
            mapping_data = json.load(mapping_handle)

        self.metadata = mapping_data.get("metadata", {})
        self.mappings_by_cis_sub_control = mapping_data.get("mappings_by_cis_sub_control", {})

    @staticmethod
    def normalize_cis_value(value):
        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip()

        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return str(value).strip()

        if decimal_value == decimal_value.to_integral():
            return str(decimal_value.quantize(Decimal(1)))
        return format(decimal_value.normalize(), "f")

    @classmethod
    def normalize_cis_values(cls, cis_v8_values):
        if cis_v8_values is None:
            return []

        if isinstance(cis_v8_values, str):
            value = cis_v8_values.strip()
            if not value:
                return []

            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed_value = ast.literal_eval(value)
                    return cls.normalize_cis_values(parsed_value)
                except (SyntaxError, ValueError):
                    pass

            return [cls.normalize_cis_value(item) for item in value.split(",") if cls.normalize_cis_value(item)]

        if isinstance(cis_v8_values, (list, tuple, set)):
            values = []
            for item in cis_v8_values:
                normalized_value = cls.normalize_cis_value(item)
                if normalized_value:
                    values.append(normalized_value)
            return values

        normalized_value = cls.normalize_cis_value(cis_v8_values)
        return [normalized_value] if normalized_value else []

    def get_mappings(self, cis_v8_values):
        mappings = []
        for cis_value in self.normalize_cis_values(cis_v8_values):
            for mapping in self.mappings_by_cis_sub_control.get(cis_value, []):
                # Duplicate NIST identifiers are intentionally retained as
                # distinct source workbook rows for audit evidence.
                mappings.append(dict(mapping))
        return mappings

    def get_control_identifiers(self, cis_v8_values, deduplicate=False):
        identifiers = [
            mapping["nist_control_identifier"]
            for mapping in self.get_mappings(cis_v8_values)
            if mapping.get("nist_control_identifier")
        ]

        if not deduplicate:
            return identifiers

        unique_identifiers = []
        seen_identifiers = set()
        for identifier in identifiers:
            if identifier in seen_identifiers:
                continue
            unique_identifiers.append(identifier)
            seen_identifiers.add(identifier)
        return unique_identifiers

    def format_control_identifiers(self, cis_v8_values, deduplicate=False):
        return ", ".join(self.get_control_identifiers(cis_v8_values, deduplicate=deduplicate))

    def enrich_compliance_mapping(self, compliance_mapping, cis_field=None, nist_field=None):
        cis_field = cis_field or self.DEFAULT_CIS_FIELD
        nist_field = nist_field or self.DEFAULT_NIST_FIELD

        enriched_mapping = dict(compliance_mapping)
        enriched_mapping[nist_field] = self.get_control_identifiers(enriched_mapping.get(cis_field, []))
        return enriched_mapping


class NISTOverlayReport:
    CIS_FIELD = "CIS v8"
    CCCS_FIELD = "CCCS Guard Rail"
    NIST_FIELD = "NIST Controls"
    SUMMARY_SUFFIX = "_cis_summary_report"
    MODES = ("nist", "combined")

    BASE_FIELDS = [
        "Recommendation #",
        "Section",
        "Level",
        "Compliant",
        "Findings",
        "Compliant Items",
        "Total",
        "Compliance Percentage Per Recommendation",
        "Title",
    ]
    TAIL_FIELDS = ["Filename", "Remediation"]

    def __init__(self, mappings=None):
        self.mappings = mappings or NISTMappings()

    def apply(self, input_path, mode="nist", output_path=None, force=False):
        mode = self._normalize_mode(mode)
        input_path = os.path.abspath(input_path)
        if not os.path.exists(input_path):
            raise FileNotFoundError("Input report path does not exist: " + input_path)

        if zipfile.is_zipfile(input_path):
            return self._apply_to_zip(input_path, mode, output_path, force)

        if os.path.isdir(input_path):
            return self._apply_to_directory(input_path, mode, output_path, force)

        raise ValueError("Input must be an existing report directory or .zip package: " + input_path)

    def _apply_to_directory(self, input_dir, mode, output_path=None, force=False):
        report_root = os.path.abspath(input_dir)
        if output_path:
            output_path = os.path.abspath(output_path)
            if os.path.exists(output_path):
                if not force:
                    raise FileExistsError("Output directory already exists. Use --force to replace it: " + output_path)
                shutil.rmtree(output_path)
            shutil.copytree(report_root, output_path)
            report_root = output_path

        report_dir = self._locate_report_directory(report_root)
        result = self._write_overlay_artifacts(report_dir, mode)
        result["input"] = input_dir
        result["report_directory"] = report_dir
        return result

    def _apply_to_zip(self, input_zip, mode, output_path=None, force=False):
        if output_path is None:
            base, ext = os.path.splitext(input_zip)
            output_path = f"{base}_{mode}_overlay{ext}"
        output_path = os.path.abspath(output_path)
        if os.path.exists(output_path):
            if not force:
                raise FileExistsError("Output zip already exists. Use --force to replace it: " + output_path)
            os.remove(output_path)

        workspace = tempfile.mkdtemp(prefix="nist-overlay-")
        extract_root = os.path.join(workspace, "extracted")
        os.makedirs(extract_root)
        try:
            self._safe_extract_zip(input_zip, extract_root)
            report_dir = self._locate_report_directory(extract_root)
            result = self._write_overlay_artifacts(report_dir, mode)
            self._create_zip_from_directory(extract_root, output_path)
            result["input"] = input_zip
            for key in ("source_summary", "csv", "json", "html", "workbook", "report_directory"):
                if result.get(key):
                    result[key] = os.path.relpath(result[key], extract_root)
            if result.get("charts"):
                result["charts"] = [os.path.relpath(chart_path, extract_root) for chart_path in result["charts"]]
            result["output_zip"] = output_path
            return result
        finally:
            shutil.rmtree(workspace)

    def _write_overlay_artifacts(self, report_dir, mode):
        summary_path = self._find_source_summary(report_dir)
        prefix = self._summary_prefix(summary_path)
        source_rows, source_fields = self._read_summary(summary_path)
        overlay_rows = self._build_overlay_rows(source_rows, mode)
        csv_fields = self._field_order(source_fields, mode, include_extract_date=("extract_date" in source_fields))
        json_fields = [field for field in csv_fields if field != "extract_date"]

        csv_path = os.path.join(report_dir, f"{prefix}_{mode}_summary_report.csv")
        json_path = os.path.join(report_dir, f"{prefix}_{mode}_summary_report.json")
        html_path = os.path.join(report_dir, f"{prefix}_{mode}_summary_report.html")

        self._write_csv(csv_path, overlay_rows, csv_fields)
        self._write_json(json_path, overlay_rows, json_fields)
        chart_paths = self._copy_chart_artifacts(report_dir, prefix, mode)
        self._write_html(html_path, overlay_rows, mode, prefix, os.path.basename(summary_path), chart_paths)
        workbook_path = self._write_workbook(report_dir, prefix, mode, csv_path)

        result = {
            "mode": mode,
            "source_summary": summary_path,
            "csv": csv_path,
            "json": json_path,
            "html": html_path,
            "charts": chart_paths,
            "workbook": workbook_path,
        }
        return result

    def _build_overlay_rows(self, source_rows, mode):
        overlay_rows = []
        for row in source_rows:
            cis_values = self._parse_list_field(row.get(self.CIS_FIELD, []))
            cccs_values = self._parse_list_field(row.get(self.CCCS_FIELD, []))
            nist_values = self.mappings.get_control_identifiers(cis_values)

            overlay_row = {}
            for field in self.BASE_FIELDS:
                if field in row:
                    overlay_row[field] = row.get(field, "")

            if mode == "combined":
                overlay_row[self.CIS_FIELD] = cis_values
                overlay_row[self.NIST_FIELD] = nist_values
                overlay_row[self.CCCS_FIELD] = cccs_values
            else:
                overlay_row[self.NIST_FIELD] = nist_values

            for field in self.TAIL_FIELDS:
                if field in row:
                    overlay_row[field] = row.get(field, "")
            if "extract_date" in row:
                overlay_row["extract_date"] = row.get("extract_date", "")

            overlay_rows.append(overlay_row)

        return overlay_rows

    def _field_order(self, source_fields, mode, include_extract_date=False):
        fields = [field for field in self.BASE_FIELDS if field in source_fields]
        if not fields:
            fields = list(self.BASE_FIELDS)

        if mode == "combined":
            fields.extend([self.CIS_FIELD, self.NIST_FIELD, self.CCCS_FIELD])
        else:
            fields.append(self.NIST_FIELD)

        fields.extend([field for field in self.TAIL_FIELDS if field in source_fields])
        if include_extract_date:
            fields.append("extract_date")

        return fields

    def _read_summary(self, summary_path):
        if summary_path.endswith(".csv"):
            with open(summary_path, mode="r", newline="", encoding="unicode_escape") as summary_handle:
                reader = csv.DictReader(summary_handle)
                rows = list(reader)
                fields = list(reader.fieldnames or [])
        else:
            with open(summary_path, mode="r", encoding="utf-8") as summary_handle:
                rows = json.load(summary_handle)
            if not isinstance(rows, list):
                raise ValueError("Summary JSON must contain a list of recommendation records: " + summary_path)
            fields = list(rows[0].keys()) if rows else []

        if not rows:
            raise ValueError("Source CIS summary has no rows: " + summary_path)
        return rows, fields

    def _write_csv(self, output_path, rows, fields):
        with open(output_path, mode="w", newline="", encoding="unicode_escape") as output_handle:
            writer = csv.DictWriter(output_handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def _write_json(self, output_path, rows, fields):
        json_rows = []
        for row in rows:
            json_rows.append({field: row.get(field, "") for field in fields})

        with open(output_path, mode="w", encoding="utf-8") as output_handle:
            json.dump(json_rows, output_handle, indent=4)

    def _write_html(self, output_path, rows, mode, prefix, source_summary_name, chart_paths=None):
        title = self._html_title(mode)
        mapping_columns = self._mapping_columns(mode)
        extract_date = next((row.get("extract_date") for row in rows if row.get("extract_date")), "")
        chart_names = [os.path.basename(chart_path) for chart_path in chart_paths or []]

        with open(output_path, mode="w", encoding="utf-8") as output_handle:
            output_handle.write("<!doctype html>\n<html lang=\"en\">\n<head>\n")
            output_handle.write("<meta charset=\"utf-8\">\n")
            output_handle.write(f"<title>{self._escape(title)}</title>\n")
            output_handle.write("""
<style>
body { font-family: Arial, Helvetica, sans-serif; margin: 32px; color: #161513; background: #fcfbfa; }
h1 { font-size: 26px; margin-bottom: 8px; }
h2 { font-size: 20px; margin-top: 34px; }
.meta { color: #5f5a55; margin-bottom: 24px; }
table { width: 100%; border-collapse: collapse; margin: 14px 0 24px; background: #fff; }
th, td { border: 1px solid #d8d5d1; padding: 10px 12px; text-align: left; vertical-align: top; }
th { background: #f4f1ee; font-weight: 700; }
.summary th:nth-child(1) { width: 12%; }
.summary th:nth-child(2) { width: 12%; }
.summary th:nth-child(3) { width: 18%; }
.status-no { color: #c74634; font-weight: 700; }
.status-yes { color: #3a7d44; font-weight: 700; }
.charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin: 24px 0 30px; }
.charts img { width: 100%; max-width: 620px; background: #fff; border: 1px solid #d8d5d1; }
.details-table { margin: 0; }
.details-table th { width: 16%; }
a { color: #00688c; }
</style>
""")
            output_handle.write("</head>\n<body>\n")
            output_handle.write(f"<h1>{self._escape(title)}</h1>\n")
            output_handle.write("<div class=\"meta\">")
            output_handle.write(f"Source CIS summary: {self._escape(source_summary_name)}")
            if extract_date:
                output_handle.write(f"<br>Extract date: {self._escape(str(extract_date).replace('T', ' '))} UTC")
            output_handle.write("</div>\n")

            if chart_names:
                output_handle.write("<div class=\"charts\">\n")
                for chart_name in chart_names:
                    output_handle.write(f"<img src=\"{self._escape(chart_name)}\" alt=\"{self._escape(chart_name)}\">\n")
                output_handle.write("</div>\n")

            self._write_html_section(output_handle, "Non-compliant Recommendations", rows, mapping_columns, lambda row: row.get("Compliant") == "No")
            self._write_html_section(output_handle, "Compliant Recommendations", rows, mapping_columns, lambda row: row.get("Compliant") == "Yes")
            self._write_html_section(output_handle, "Other Recommendations", rows, mapping_columns, lambda row: row.get("Compliant") not in ("No", "Yes"))

            output_handle.write("</body>\n</html>\n")

    def _write_html_section(self, output_handle, heading, rows, mapping_columns, predicate):
        section_rows = [row for row in rows if predicate(row)]
        if not section_rows:
            return

        output_handle.write(f"<h2>{self._escape(heading)}</h2>\n")
        output_handle.write("<table class=\"summary\">\n<thead><tr>")
        for header in ("Recommendation #", "Compliant", "Section", "Details"):
            output_handle.write(f"<th>{self._escape(header)}</th>")
        output_handle.write("</tr></thead>\n<tbody>\n")

        for row in section_rows:
            recommendation = self._escape(row.get("Recommendation #", ""))
            compliant = self._escape(row.get("Compliant", ""))
            status_class = "status-no" if row.get("Compliant") == "No" else "status-yes" if row.get("Compliant") == "Yes" else ""
            output_handle.write("<tr>")
            output_handle.write(f"<td>{recommendation}</td>")
            output_handle.write(f"<td><span class=\"{status_class}\">{compliant}</span></td>")
            output_handle.write(f"<td>{self._escape(row.get('Section', ''))}</td>")
            output_handle.write("<td>")
            self._write_html_details(output_handle, row, mapping_columns)
            output_handle.write("</td>")
            output_handle.write("</tr>\n")

        output_handle.write("</tbody>\n</table>\n")

    def _write_html_details(self, output_handle, row, mapping_columns):
        output_handle.write("<table class=\"details-table\">")
        output_handle.write("<tr><th>Title</th>")
        output_handle.write(f"<td colspan=\"{len(mapping_columns) + 2}\">{self._escape(row.get('Title', ''))}</td></tr>")
        output_handle.write("<tr><th>Remediation</th>")
        output_handle.write(f"<td colspan=\"{len(mapping_columns) + 2}\">{self._escape(row.get('Remediation', ''))}</td></tr>")
        output_handle.write("<tr><th>Level</th>")
        for _, label in mapping_columns:
            output_handle.write(f"<th>{self._escape(label)}</th>")
        output_handle.write("<th>File</th></tr>")
        output_handle.write(f"<tr><td>{self._escape(row.get('Level', ''))}</td>")
        for field, _ in mapping_columns:
            output_handle.write(f"<td>{self._escape(self._format_list_value(row.get(field, [])))}</td>")
        filename = str(row.get("Filename", "")).strip()
        if filename:
            output_handle.write(f"<td><a href=\"{self._escape(filename)}\">{self._escape(filename)}</a></td>")
        else:
            output_handle.write("<td></td>")
        output_handle.write("</tr></table>")

    def _copy_chart_artifacts(self, report_dir, prefix, mode):
        chart_paths = []
        for chart_subject in ("summary_compliance", "summary_compliance_by_focus_area"):
            source_path = os.path.join(report_dir, f"{prefix}_cis_{chart_subject}.png")
            if not os.path.exists(source_path):
                continue
            destination_path = os.path.join(report_dir, f"{prefix}_{mode}_{chart_subject}.png")
            shutil.copy2(source_path, destination_path)
            chart_paths.append(destination_path)
        return chart_paths

    def _write_workbook(self, report_dir, prefix, mode, overlay_csv_path):
        try:
            from xlsxwriter.workbook import Workbook
        except Exception:
            return None

        workbook_path = os.path.join(report_dir, f"{prefix}_{mode}_Consolidated_Report.xlsx")
        csv_files = [overlay_csv_path]
        detail_pattern = os.path.join(report_dir, f"{prefix}_cis_*.csv")
        for csv_path in sorted(glob.glob(detail_pattern)):
            if csv_path.endswith("_cis_summary_report.csv"):
                continue
            csv_files.append(csv_path)

        workbook = Workbook(workbook_path, {"in_memory": True})
        seen_worksheet_names = set()
        try:
            for csv_path in csv_files:
                worksheet_name = self._build_worksheet_name(csv_path, prefix + "_", seen_worksheet_names)
                if not worksheet_name:
                    continue

                worksheet = workbook.add_worksheet(worksheet_name)
                with open(csv_path, mode="r", newline="", encoding="unicode_escape") as csv_handle:
                    reader = csv.reader(csv_handle)
                    last_row = 0
                    last_col = 0
                    has_data = False
                    for row_index, row in enumerate(reader):
                        has_data = True
                        last_row = row_index
                        for col_index, value in enumerate(row):
                            last_col = col_index
                            worksheet.write(row_index, col_index, value)
                    if has_data:
                        worksheet.autofilter(0, 0, last_row, last_col)
                    if hasattr(worksheet, "autofit"):
                        worksheet.autofit()
        finally:
            workbook.close()

        return workbook_path

    @staticmethod
    def _build_worksheet_name(csv_path, report_prefix, seen_names):
        base_name = os.path.basename(csv_path)
        if report_prefix:
            base_name = base_name.replace(report_prefix, "")

        name = (base_name
                .replace(".csv", "")
                .replace("raw_data_", "raw_")
                .replace("Findings", "fds")
                .replace("Best_Practices", "OBP"))

        replacement_rules = (
            ("Identity_and_Access_Management", "IAM"),
            ("Storage_Object_Storage", "Object_Storage"),
            ("raw_identity_groups_and_membership", "raw_iam_groups_and_membership"),
            ("Cost_Tracking_Budgets_Best_Practices", "Budgets_Best_Practices"),
            ("Cost_Tracking", "Cost"),
            ("Storage_File_Storage_Service", "FSS"),
            ("Networking_IPSec_connections", "Networking_IPSec"),
            ("IAM_Stmt_Comp_Hierarchy_Count", "IAM_Stmt_Comp_Count"),
            ("compartment_hierarchy_policy_count", "compartment_policy_cnt"),
        )

        for pattern, replacement in replacement_rules:
            if pattern in name:
                name = name.replace(pattern, replacement)
                break

        name = re.sub(r"_+", "_", name).strip("_") or "worksheet"
        if len(name) > 31:
            name = name.replace("_", "")
        if len(name) > 31:
            name = name[:28]

        candidate = name
        counter = 1
        while candidate in seen_names or len(candidate) > 31:
            suffix = f"_{counter}"
            candidate = f"{name[:31 - len(suffix)]}{suffix}" if len(name) + len(suffix) > 31 else f"{name}{suffix}"
            counter += 1

        seen_names.add(candidate)
        return candidate

    def _locate_report_directory(self, root_dir):
        summary_candidates = []
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.endswith("_cis_summary_report.csv") or filename.endswith("_cis_summary_report.json"):
                    summary_candidates.append(os.path.join(dirpath, filename))

        if not summary_candidates:
            raise FileNotFoundError("No *_cis_summary_report.csv or JSON file found under: " + root_dir)

        directories = sorted(set(os.path.dirname(path) for path in summary_candidates))
        if len(directories) > 1:
            raise ValueError("Multiple CIS report directories found. Point --input to one report directory instead.")

        return directories[0]

    def _find_source_summary(self, report_dir):
        csv_candidates = sorted(glob.glob(os.path.join(report_dir, "*_cis_summary_report.csv")))
        if csv_candidates:
            if len(csv_candidates) > 1:
                raise ValueError("Multiple CIS summary CSV files found in: " + report_dir)
            return csv_candidates[0]

        json_candidates = sorted(glob.glob(os.path.join(report_dir, "*_cis_summary_report.json")))
        if json_candidates:
            if len(json_candidates) > 1:
                raise ValueError("Multiple CIS summary JSON files found in: " + report_dir)
            return json_candidates[0]

        raise FileNotFoundError("No CIS summary report found in: " + report_dir)

    def _summary_prefix(self, summary_path):
        name = os.path.basename(summary_path)
        for suffix in ("_cis_summary_report.csv", "_cis_summary_report.json"):
            if name.endswith(suffix):
                return name[:-len(suffix)]
        raise ValueError("Unsupported CIS summary filename: " + name)

    @staticmethod
    def _parse_list_field(value):
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, tuple):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            clean_value = value.strip()
            if not clean_value:
                return []
            if clean_value.startswith("[") and clean_value.endswith("]"):
                try:
                    parsed_value = ast.literal_eval(clean_value)
                    return NISTOverlayReport._parse_list_field(parsed_value)
                except (SyntaxError, ValueError):
                    pass
            return [item.strip() for item in clean_value.split(",") if item.strip()]
        clean_value = str(value).strip()
        return [clean_value] if clean_value else []

    @staticmethod
    def _format_list_value(value):
        parsed_value = NISTOverlayReport._parse_list_field(value)
        if parsed_value:
            return ", ".join(parsed_value)
        return str(value).strip() if value is not None else ""

    @staticmethod
    def _safe_extract_zip(zip_path, destination):
        destination = os.path.abspath(destination)
        with zipfile.ZipFile(zip_path, mode="r") as zip_handle:
            for member in zip_handle.infolist():
                member_path = os.path.abspath(os.path.join(destination, member.filename))
                if not member_path.startswith(destination + os.sep) and member_path != destination:
                    raise ValueError("Unsafe zip member path: " + member.filename)
            zip_handle.extractall(destination)

    @staticmethod
    def _create_zip_from_directory(source_dir, output_zip):
        output_parent = os.path.dirname(output_zip)
        if output_parent:
            os.makedirs(output_parent, exist_ok=True)
        with zipfile.ZipFile(output_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_handle:
            for dirpath, _, filenames in os.walk(source_dir):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    archive_name = os.path.relpath(file_path, source_dir)
                    zip_handle.write(file_path, archive_name)

    @classmethod
    def _normalize_mode(cls, mode):
        if mode not in cls.MODES:
            raise ValueError("Mode must be one of: " + ", ".join(cls.MODES))
        return mode

    @staticmethod
    def _mapping_columns(mode):
        if mode == "combined":
            return [
                (NISTOverlayReport.CIS_FIELD, NISTOverlayReport.CIS_FIELD),
                (NISTOverlayReport.NIST_FIELD, NISTOverlayReport.NIST_FIELD),
                (NISTOverlayReport.CCCS_FIELD, NISTOverlayReport.CCCS_FIELD),
            ]
        return [(NISTOverlayReport.NIST_FIELD, NISTOverlayReport.NIST_FIELD)]

    @staticmethod
    def _html_title(mode):
        if mode == "combined":
            return "Combined Mapping for CIS OCI Foundations Benchmark 3.0.0 - Compliance Report"
        return "NIST SP 800-53 Mapping for CIS OCI Foundations Benchmark 3.0.0 - Compliance Report"

    @staticmethod
    def _escape(value):
        return html.escape(str(value), quote=True)


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Build NIST SP 800-53 overlay artifacts from an existing OCI CIS report package."
    )
    subparsers = parser.add_subparsers(dest="command")

    overlay_parser = subparsers.add_parser(
        "overlay",
        help="Add NIST or combined mapping summary artifacts to an existing report directory or zip.",
    )
    overlay_parser.add_argument(
        "--input",
        required=True,
        dest="input_path",
        help="Existing OCI CIS report directory or .zip package.",
    )
    mode_group = overlay_parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--nist-mappings",
        action="store_const",
        const="nist",
        dest="mode",
        help="Create NIST-only overlay summary artifacts.",
    )
    mode_group.add_argument(
        "--all-mappings",
        action="store_const",
        const="combined",
        dest="mode",
        help="Create verbose CIS, NIST, and CCCS combined summary artifacts.",
    )
    overlay_parser.add_argument(
        "--output",
        default=None,
        dest="output_path",
        help="Output zip path for zip input, or output directory path for directory input.",
    )
    overlay_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace the requested output path if it already exists.",
    )

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        raise SystemExit(2)
    return args


def main():
    args = _parse_args()
    overlay = NISTOverlayReport()
    result = overlay.apply(args.input_path, mode=args.mode, output_path=args.output_path, force=args.force)

    print("NIST overlay generated")
    print("Mode: " + result["mode"])
    print("Source summary: " + result["source_summary"])
    print("CSV: " + result["csv"])
    print("JSON: " + result["json"])
    print("HTML: " + result["html"])
    if result.get("workbook"):
        print("Workbook: " + result["workbook"])
    else:
        print("Workbook: skipped because xlsxwriter is not available")
    if result.get("charts"):
        for chart_path in result["charts"]:
            print("Chart: " + chart_path)
    else:
        print("Charts: skipped because source CIS chart PNGs were not found")
    if result.get("output_zip"):
        print("Output zip: " + result["output_zip"])


if __name__ == "__main__":
    main()
