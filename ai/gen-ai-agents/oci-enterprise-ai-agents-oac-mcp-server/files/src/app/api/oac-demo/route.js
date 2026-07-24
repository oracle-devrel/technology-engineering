// Copyright (c) 2026 Oracle and/or its affiliates.
// Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import { NextResponse } from 'next/server';
import path from 'node:path';
import { existsSync } from 'node:fs';
import { spawn } from 'node:child_process';

export const maxDuration = 300;

// The app root (where package.json, .env, and tokens.json live).
const appRoot = process.cwd();
const bridgeScript = path.join(appRoot, 'scripts', 'oac_react_api.py');

// Resolved at request time; segments joined manually so the bundler does not
// trace .venv (its python symlink points outside the project and breaks the
// production build's module graph scan).
function resolvePythonBin() {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;
  const venvPython = [appRoot, '.venv', 'bin', 'python'].join(path.sep);
  return existsSync(venvPython) ? venvPython : 'python3';
}

export async function GET() {
  return runBridge({ action: 'config' });
}

export async function POST(request) {
  const payload = await request.json();
  return runBridge(payload);
}

async function runBridge(payload) {
  const result = await runPython(payload);
  if (!result.ok) {
    return NextResponse.json(result, { status: 400 });
  }
  return NextResponse.json(result);
}

function runPython(payload) {
  return new Promise((resolve) => {
    const child = spawn(resolvePythonBin(), [bridgeScript], {
      cwd: appRoot,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PYTHONUTF8: '1',
        PYTHONIOENCODING: 'utf-8',
        PYTHONDONTWRITEBYTECODE: '1',
      },
    });

    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString('utf8');
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString('utf8');
    });
    child.on('close', () => {
      const parsed = parseBridgeOutput(stdout);
      if (parsed) {
        resolve(parsed);
        return;
      }
      resolve({
        ok: false,
        error: {
          type: 'BridgeError',
          message: stderr.slice(0, 2000) || 'Python bridge returned no JSON.',
        },
      });
    });

    child.stdin.write(JSON.stringify(payload));
    child.stdin.end();
  });
}

function parseBridgeOutput(stdout) {
  const lines = stdout.trim().split(/\r?\n/).filter(Boolean);
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    try {
      return JSON.parse(lines[i]);
    } catch {
      // Keep looking for the final JSON line.
    }
  }
  return null;
}
