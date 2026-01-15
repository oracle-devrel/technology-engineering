"""
File name: config.py
Author: Luigi Saetta
Date last modified: 2025-07-02
Python Version: 3.11

Description:
    This module provides general configurations


Usage:
    Import this module into other scripts to use its functions.
    Example:
        import config

License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement a code quality agent.

Warnings:
    This module is in development, may change in future versions.
"""

DEBUG = False
STREAMING = False

# OCI general

# type of OCI auth
AUTH = "API_KEY"
REGION = "eu-frankfurt-1"
SERVICE_ENDPOINT = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com"

# LLM
# this is the default model
LLM_MODEL_ID = "openai.gpt-oss-120b"

TEMPERATURE = 0.0
TOP_P = 1
MAX_TOKENS = 4000

#
# specific configs for the Code Quality Agent
#
# for now, only Python files
FILES_PATTERN = "*.py"

# ---- File exclusions (repo-relative glob patterns) ----
EXCLUDED_PATHS = [
    ".git/**",
    ".venv/**",
    "venv/**",
    "__pycache__/**",
    "*.pyc",
    "build/**",
    "dist/**",
    "node_modules/**",
]

# Accepted license identifiers (you decide the vocabulary)
ACCEPTED_LICENSE_TYPES = [
    "MIT",
    "Apache-2.0",
    "UPL-1.0",
    "BSD-3-Clause",
    "BSD-2-Clause",
]

# set this flag to True if you want to create local docs in md format.
# Not needed to check code quality.
ENABLE_DOC_GENERATION = False

# used for header generation. 
# It is the minimum version accepted.
PYTHON_VERSION = "3.11"

# Licenses you allow for dependencies (use SPDX-ish IDs where possible)
# see docs here: 
# https://confluence.oraclecorp.com/confluence/display/CORPARCH/Licenses+Eligible+for+Pre-Approval+-+Distribution
ACCEPTED_DEP_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-3-Clause",
    "BSD-2-Clause",
    "BSD",
    "ISC",
    # Mozilla Public License
    "MPL-2.0",
    # Python Software Foundation License
    "PSF-2.0",
    "UPL-1.0",
    # Eclipse Public License
    "EPL-2.0",
}

# Policy knobs
FAIL_ON_UNKNOWN_DEP_LICENSE = False  # usually False at first
FAIL_ON_NOT_INSTALLED_DEP = False
