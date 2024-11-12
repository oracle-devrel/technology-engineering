##########################################################################
# Copyright (c) 2024, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.
#
# email_security_check.py
# @author base: Jacco Steur
#
# Supports Python 3 and above
#
# coding: utf-8
##########################################################################
# This Python tool checks the email security settings of a domain by verifying its SPF, DKIM, and DMARC records. It
# extracts relevant information from a domain or an `.eml` file, performs validation, and outputs a summary of findings, 
# including policies and IP addresses associated with SPF records. It can also analyze the alignment of sender information
# for SPF, DKIM and DMARC and resolve IP locations of the email servers included in the SPF includes.
##########################################################################
import dns.resolver
import sys
import re
import argparse
import email
from email import policy
from email.parser import BytesParser
from tabulate import tabulate 
import spf  
import dkim  
import socket
import email.utils  # Ensure this import is present
import ipaddress
import requests 

##########################################################################
# Retrieves all TXT records for a domain.
# Uses DNS resolver to get TXT records and decodes them into strings.
##########################################################################
def get_txt_records(domain):
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        records = []
        for rdata in answers:
            txt_record = ''.join([txt.decode('utf-8') for txt in rdata.strings])
            records.append(txt_record)
        return records
    except Exception as e:
        return []

##########################################################################
# Retrieves the SPF record for a domain.
# Extracts the SPF record from the domain's TXT records.
##########################################################################
def get_spf_record(domain):
    print(f"Retrieving SPF record for domain: {domain}")
    txt_records = get_txt_records(domain)
    for txt_record in txt_records:
        if txt_record.startswith('v=spf1'):
            print(f"Found SPF record: {txt_record}\n")
            return txt_record
    print("No SPF record found.\n")
    return None

##########################################################################
# Validates the SPF record syntax and extracts the policy.
# Checks if the SPF record follows the correct format and identifies its policy.
##########################################################################
def validate_spf_record(spf_record):
    print("Validating SPF record syntax...")
    if not spf_record.startswith('v=spf1'):
        return False, "SPF record does not start with 'v=spf1'.", None
    mechanisms = spf_record.strip().split()
    valid_mechanisms = ['v=spf1', 'ip4', 'ip6', 'a', 'mx', 'ptr', 'exists', 'include', 'all', '+all', '-all', '~all', '?all', 'redirect']
    policy = None
    for mech in mechanisms[1:]:
        mech_name = mech.split(':')[0].split('=')[0].lstrip('+-~?')
        if mech_name == 'all':
            qualifier = mech[0] if mech[0] in ['+', '-', '~', '?'] else '+'
            policy = qualifier + 'all'
        if mech_name not in valid_mechanisms:
            return False, f"Invalid mechanism found in SPF record: {mech_name}", policy
    return True, "SPF record syntax appears valid.", policy

##########################################################################
# Provides an explanation for the SPF policy.
# Maps SPF policy tags to descriptive explanations like Pass, Fail, etc.
##########################################################################
def explain_spf_policy(policy):
    explanations = {
        '-all': 'Fail',
        '~all': 'SoftFail',
        '?all': 'Neutral',
        '+all': 'Pass',
    }
    return explanations.get(policy, 'Unknown policy')

##########################################################################
# Retrieves the DMARC record for a domain.
# Looks for the DMARC record in the _dmarc subdomain's TXT records.
##########################################################################
def get_dmarc_record(domain):
    print(f"Retrieving DMARC record for domain: {domain}")
    dmarc_domain = f"_dmarc.{domain}"
    txt_records = get_txt_records(dmarc_domain)
    for txt_record in txt_records:
        if txt_record.startswith('v=DMARC1'):
            print(f"Found DMARC record: {txt_record}\n")
            return txt_record
    print("No DMARC record found.\n")
    return None

##########################################################################
# Validates the DMARC record syntax and extracts the policy.
# Checks if the DMARC record follows the correct format and identifies its policy.
##########################################################################
def validate_dmarc_record(dmarc_record):
    print("Validating DMARC record syntax...")
    if not dmarc_record.startswith('v=DMARC1'):
        return False, "DMARC record does not start with 'v=DMARC1'.", None, {}
    tags = dict(tag.strip().split('=', 1) for tag in dmarc_record.strip().split(';') if '=' in tag)
    required_tags = ['p']
    for tag in required_tags:
        if tag not in tags:
            return False, f"Missing required DMARC tag: {tag}", None, tags
    policy = tags.get('p', None)
    return True, "DMARC record syntax appears valid.", policy, tags

##########################################################################
# Provides an explanation for the DMARC policy.
# Maps DMARC policy tags to descriptive explanations like None, Quarantine, etc.
##########################################################################
def explain_dmarc_policy(policy):
    explanations = {
        'none': 'None',
        'quarantine': 'Quarantine',
        'reject': 'Reject',
    }
    return explanations.get(policy, 'Unknown policy')

##########################################################################
# Retrieves the DKIM record for a domain and selector.
# Queries DNS for a DKIM record using the domain and DKIM selector.
##########################################################################
def get_dkim_record(domain, selector):
    dkim_domain = f"{selector}._domainkey.{domain}"
    txt_records = get_txt_records(dkim_domain)
    for txt_record in txt_records:
        if 'v=DKIM1' in txt_record:
            return txt_record
    return None

##########################################################################
# Retrieves MX records for a domain.
# Uses DNS resolver to retrieve the MX records and display them.
##########################################################################
def get_mx_records(domain):
    print(f"Retrieving MX records for domain: {domain}")
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        mx_records = []
        for rdata in answers:
            mx_records.append((rdata.preference, str(rdata.exchange).rstrip('.')))
        return sorted(mx_records, key=lambda x: x[0])
    except Exception as e:
        print(f"Error retrieving MX records for {domain}: {e}\n")
        return []

##########################################################################
# Extracts the domain from a hostname.
# Breaks down the hostname and returns the domain part.
##########################################################################
def extract_domain_from_hostname(hostname):
    parts = hostname.split('.')
    return '.'.join(parts[-2:]) if len(parts) >= 2 else hostname

##########################################################################
# Extracts sender domain, DKIM selector, and other info from an .eml file.
# Parses the email file to extract relevant DKIM, SPF, and sender information.
##########################################################################
def extract_info_from_eml(eml_file):
    try:
        with open(eml_file, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
    except Exception as e:
        print(f"Error reading .eml file: {e}")
        return None, None, None, None, None

    sender_domain = None
    dkim_selector = None
    dkim_domain = None
    envelope_from_domain = None
    sending_ip = None

    sender_email = msg.get('From')
    if sender_email:
        realname, email_address = email.utils.parseaddr(sender_email)
        if email_address:
            sender_domain = email_address.split('@')[-1]

    dkim_header = msg.get('DKIM-Signature')
    if dkim_header:
        m_selector = re.search(r's=([^;]+)', dkim_header)
        m_domain = re.search(r'd=([^;]+)', dkim_header)
        if m_selector:
            dkim_selector = m_selector.group(1)
        if m_domain:
            dkim_domain = m_domain.group(1)

    return_path = msg.get('Return-Path')
    if return_path:
        realname, email_address = email.utils.parseaddr(return_path)
        if email_address:
            envelope_from_domain = email_address.split('@')[-1]

    received_headers = msg.get_all('Received')
    if received_headers:
        for header in received_headers:
            m = re.search(r'\[([0-9\.]+)\]', header)
            if m:
                sending_ip = m.group(1)
                break

    return sender_domain, dkim_selector, envelope_from_domain, sending_ip, dkim_domain

##########################################################################
# Recursively expands an SPF record to get all IP addresses.
# Follows 'include' and other directives to resolve all IP addresses in the SPF record.
##########################################################################
def expand_spf_record(spf_record, domain, visited=None):
    if visited is None:
        visited = set()
    visited.add(domain)

    mechanisms = spf_record.strip().split()
    ip_addresses = []
    for mech in mechanisms[1:]:
        mech = mech.strip()
        qualifier = mech[0] if mech[0] in ['+', '-', '~', '?'] else ''
        if ':' in mech:
            mech_name, mech_value = mech.split(':', 1)
        else:
            mech_name, mech_value = mech, ''

        if mech_name == 'include':
            if mech_value and mech_value not in visited:
                included_spf = get_spf_record(mech_value)
                if included_spf:
                    ips = expand_spf_record(included_spf, mech_value, visited)
                    ip_addresses.extend(ips)
        elif mech_name == 'a':
            a_domain = mech_value if mech_value else domain
            try:
                answers = dns.resolver.resolve(a_domain, 'A')
                for rdata in answers:
                    ip_addresses.append(str(rdata))
            except Exception as e:
                pass
        elif mech_name == 'mx':
            mx_domain = mech_value if mech_value else domain
            mx_records = get_mx_records(mx_domain)
            for _, mx_host in mx_records:
                try:
                    answers = dns.resolver.resolve(mx_host, 'A')
                    for rdata in answers:
                        ip_addresses.append(str(rdata))
                except Exception as e:
                    pass
        elif mech_name == 'ip4' and mech_value:
            ip_addresses.append(mech_value)
        elif mech_name == 'ip6' and mech_value:
            ip_addresses.append(mech_value)

    return ip_addresses

##########################################################################
# Gets the physical location of an IP address using ip-api.com.
# Makes an API request to get the geolocation of an IP address.
##########################################################################
def get_ip_location(ip_address):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        data = response.json()
        if data['status'] == 'success':
            country = data.get('country', '')
            city = data.get('city', '')
            return f"{city}, {country}" if city else country
        return "Unknown"
    except Exception as e:
        return "Unknown"

##########################################################################
# Resolves all IP addresses from an SPF record and gets their locations.
# Recursively fetches IP addresses from the SPF record and resolves their geolocation.
##########################################################################
def resolve_spf_ips(domain, spf_record):
    print(f"Resolving IP addresses from SPF record for {domain}")
    ip_addresses = expand_spf_record(spf_record, domain)
    ip_addresses = list(set(ip_addresses))
    resolved_ips = []

    for ip in ip_addresses:
        try:
            reverse_dns = socket.gethostbyaddr(ip)[0]
        except Exception:
            reverse_dns = 'Unknown'
        location = get_ip_location(ip)
        resolved_ips.append({'IP Address': ip, 'Reverse DNS': reverse_dns, 'Location': location})
    return resolved_ips

##########################################################################
# Checks SPF, DMARC, and DKIM records for a given domain.
# Verifies the domain's email security configuration, including SPF, DMARC, and DKIM.
##########################################################################
def check_domain_security(domain, selectors, dump_txt=False, resolve_spf=False):
    print(f"=== Checking Domain: {domain} ===\n")

    valid_spf = False
    spf_policy_display = "Not Found"
    valid_dmarc = False
    dmarc_policy_display = "Not Found"
    dkim_found = False
    dmarc_tags = {}
    found_selectors = []
    spf_ips = []
    spf_record = get_spf_record(domain)

    if spf_record:
        valid_spf, spf_message, spf_policy = validate_spf_record(spf_record)
        if spf_policy:
            spf_policy_display = f"{explain_spf_policy(spf_policy)} ({spf_policy})"
        if resolve_spf:
            spf_ips = resolve_spf_ips(domain, spf_record)

    dmarc_record = get_dmarc_record(domain)
    if dmarc_record:
        valid_dmarc, dmarc_message, dmarc_policy, dmarc_tags = validate_dmarc_record(dmarc_record)
        if dmarc_policy:
            dmarc_policy_display = f"{explain_dmarc_policy(dmarc_policy)} ({dmarc_policy})"

    for selector in selectors:
        dkim_record = get_dkim_record(domain, selector)
        if dkim_record:
            dkim_found = True
            found_selectors.append(selector)

    if dump_txt:
        txt_records = get_txt_records(domain)
        if txt_records:
            print(f"\nTXT records for domain: {domain}\n")
            for record in txt_records:
                print(f"- {record}")
        else:
            print(f"No TXT records found for domain: {domain}\n")

    return {
        'Domain': domain,
        'SPF Record': spf_record if spf_record else 'Not Found',
        'SPF Valid': 'Yes' if valid_spf else 'No',
        'SPF Policy': spf_policy_display,
        'DKIM Valid': 'Yes' if dkim_found else 'No',
        'DKIM Selectors': ', '.join(found_selectors) if found_selectors else 'None Found',
        'DMARC Valid': 'Yes' if valid_dmarc else 'No',
        'DMARC Policy': dmarc_policy_display,
        'DMARC RUA': dmarc_tags.get('rua', 'Not Specified'),
        'DMARC RUF': dmarc_tags.get('ruf', 'Not Specified'),
        'SPF IPs': spf_ips
    }

##########################################################################
# Checks DKIM records for domains extracted from MX records.
# Verifies email security settings of domains found in MX records.
##########################################################################
def check_mx_domains(mx_records, selectors, resolve_spf=False):
    mx_results = []
    processed_domains = set()
    for preference, mx_host in mx_records:
        mx_domain = extract_domain_from_hostname(mx_host)
        if mx_domain in processed_domains:
            continue
        processed_domains.add(mx_domain)
        result = check_domain_security(mx_domain, selectors, resolve_spf=resolve_spf)
        mx_results.append(result)
    return mx_results

##########################################################################
# Analyzes SPF and DKIM alignment.
# Checks if the sender domain aligns with the DKIM and SPF domains.
##########################################################################
def analyze_alignment(sender_domain, envelope_from_domain, dkim_domain):
    alignment_results = {}
    spf_aligned = False
    if envelope_from_domain and (sender_domain == envelope_from_domain or sender_domain.endswith('.' + envelope_from_domain)):
        spf_aligned = True
    alignment_results['SPF Aligned'] = 'Yes' if spf_aligned else 'No'

    dkim_aligned = False
    if dkim_domain and (sender_domain == dkim_domain or sender_domain.endswith('.' + dkim_domain)):
        dkim_aligned = True
    alignment_results['DKIM Aligned'] = 'Yes' if dkim_aligned else 'No'

    return alignment_results

##########################################################################
# Performs SPF check using the spf module.
# Validates the SPF result for a given domain and IP address.
##########################################################################
def perform_spf_check(envelope_from_domain, sending_ip):
    if not envelope_from_domain or not sending_ip:
        return 'Fail', 'Missing envelope_from_domain or sending_ip'
    try:
        result, explanation = spf.check2(sending_ip, envelope_from_domain, envelope_from_domain)
        return result, explanation
    except Exception as e:
        return 'PermError', str(e)

##########################################################################
# Performs DKIM verification using the dkim module.
# Validates the DKIM signature of the email.
##########################################################################
def perform_dkim_check(eml_file):
    try:
        with open(eml_file, 'rb') as f:
            email_bytes = f.read()
        result = dkim.verify(email_bytes)
        return 'Pass' if result else 'Fail'
    except Exception as e:
        return 'PermError'

##########################################################################
# Displays the summary results in a row format.
# Outputs the domain security settings in a row-based table format.
##########################################################################
def display_summary_results_row_format(summary_results):
    for result in summary_results:
        rows = [
            ["Domain", result['Domain']],
            ["SPF Record", result['SPF Record']],
            ["SPF Valid", result['SPF Valid']],
            ["SPF Policy", result['SPF Policy']],
            ["DKIM Valid", result['DKIM Valid']],
            ["DKIM Selectors", result['DKIM Selectors']],
            ["DMARC Valid", result['DMARC Valid']],
            ["DMARC Policy", result['DMARC Policy']],
            ["DMARC RUA", result['DMARC RUA']],
            ["DMARC RUF", result['DMARC RUF']],
        ]
        print(tabulate(rows, tablefmt="grid"))

##########################################################################
# Displays the MX summary results in a row format.
# Outputs the MX domain security settings in a row-based table format.
##########################################################################
def display_mx_summary_results_row_format(mx_summary_results):
    for result in mx_summary_results:
        rows = [
            ["Domain", result['Domain']],
            ["SPF Record", result['SPF Record']],
            ["SPF Valid", result['SPF Valid']],
            ["SPF Policy", result['SPF Policy']],
            ["DKIM Valid", result['DKIM Valid']],
            ["DKIM Selectors", result['DKIM Selectors']],
            ["DMARC Valid", result['DMARC Valid']],
            ["DMARC Policy", result['DMARC Policy']],
            ["DMARC RUA", result['DMARC RUA']],
            ["DMARC RUF", result['DMARC RUF']],
        ]
        print(tabulate(rows, tablefmt="grid"))

##########################################################################
# Displays the alignment results in a row format.
# Outputs the SPF and DKIM alignment results in a row-based table format.
##########################################################################
def display_alignment_results_row_format(alignment_results, spf_result, dkim_result):
    rows = [
        ["SPF Aligned", alignment_results.get('SPF Aligned', 'N/A')],
        ["DKIM Aligned", alignment_results.get('DKIM Aligned', 'N/A')],
        ["SPF Authentication Result", spf_result],
        ["DKIM Authentication Result", dkim_result],
    ]
    print(tabulate(rows, tablefmt="grid"))

##########################################################################
# Main function to check email security settings for a domain.
# Parses input arguments and performs domain security checks for SPF, DKIM, and DMARC.
##########################################################################
def main():
    parser = argparse.ArgumentParser(description='Check email security settings (SPF, DKIM, DMARC) for the sending domain.')

    # Input methods
    parser.add_argument('-f', '--eml-file', help='Path to the .eml file to extract information from')
    parser.add_argument('-s', '--sender-domain', help='Sender domain (the domain where the email comes from)')
    parser.add_argument('--selector', help='DKIM selector for sender domain (if known)', default=None)
    parser.add_argument('--mx-selector', help='DKIM selector for MX domains (if known)', default=None)
    parser.add_argument('-t', '--txt', help='Dump all TXT records for domains being checked', action='store_true')
    parser.add_argument('--resolve-spf', help='Resolve all IP addresses in SPF records and get their locations', action='store_true')
    args = parser.parse_args()

    sender_domain = None
    alignment_results = {}
    sender_selectors = []

    if args.eml_file:
        sender_domain, dkim_selector, envelope_from_domain, sending_ip, dkim_domain = extract_info_from_eml(args.eml_file)
        if not sender_domain:
            print("Could not extract sender domain from the .eml file.")
            sys.exit(1)
        if dkim_selector:
            sender_selectors.append(dkim_selector)
        else:
            sender_selectors = ['default', 'selector1', 'selector2', 'smtp', 'dkim', 'mail', 'email']
        spf_result, spf_explanation = perform_spf_check(envelope_from_domain, sending_ip)
        dkim_result = perform_dkim_check(args.eml_file)
        alignment_results = analyze_alignment(sender_domain, envelope_from_domain, dkim_domain)
    elif args.sender_domain:
        sender_domain = args.sender_domain
        if args.selector:
            sender_selectors.append(args.selector)
        else:
            sender_selectors = ['default', 'selector1', 'selector2', 'smtp', 'dkim', 'mail', 'email']
    else:
        print("Please provide the sender domain using -s or --sender-domain, or provide an .eml file using -f or --eml-file.")
        sys.exit(1)

    mx_selectors = [args.mx_selector] if args.mx_selector else ['default', 'selector1', 'selector2', 'smtp', 'dkim', 'mail', 'email']

    summary_results = []
    mx_summary_results = []

    sender_result = check_domain_security(sender_domain, sender_selectors, dump_txt=args.txt, resolve_spf=args.resolve_spf)
    summary_results.append(sender_result)

    sender_mx_records = get_mx_records(sender_domain)
    if sender_mx_records:
        sender_mx_results = check_mx_domains(sender_mx_records, mx_selectors, resolve_spf=args.resolve_spf)
        mx_summary_results.extend(sender_mx_results)

    display_summary_results_row_format(summary_results)
    display_mx_summary_results_row_format(mx_summary_results)

    if args.resolve_spf:
        for result in summary_results + mx_summary_results:
            if result['SPF IPs']:
                print(f"\nDomain: {result['Domain']}\nSPF Record: {result['SPF Record']}")
                headers = ['IP Address', 'Reverse DNS', 'Location']
                ip_table_data = [[ip_info['IP Address'], ip_info['Reverse DNS'], ip_info['Location']] for ip_info in result['SPF IPs']]
                print(tabulate(ip_table_data, headers=headers, tablefmt="grid"))

    if args.eml_file:
        display_alignment_results_row_format(alignment_results, spf_result, dkim_result)

if __name__ == '__main__':
    main()
