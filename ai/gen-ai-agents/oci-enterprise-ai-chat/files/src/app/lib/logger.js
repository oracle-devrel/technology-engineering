/**
 * Centralized structured logger.
 *
 * Usage:
 *   import { createLogger } from '../lib/logger';
 *   const log = createLogger('responses-api');
 *   log.info('Stream started', { conversationId, model });
 *   log.error('OCI API error', { status: 500, body: errorText });
 *
 * With request ID (server-side):
 *   const log = createLogger('responses-api', { requestId });
 *   // All subsequent calls include that requestId
 */

const LEVELS = { debug: 0, info: 1, warn: 2, error: 3 };

const LOG_LEVEL = (typeof process !== 'undefined' && process.env?.LOG_LEVEL)
  ? process.env.LOG_LEVEL
  : 'info';

function formatEntry(level, component, message, metadata, requestId) {
  const entry = {
    ts: new Date().toISOString(),
    level,
    component,
    msg: message,
  };
  if (requestId) entry.requestId = requestId;
  if (metadata && Object.keys(metadata).length > 0) entry.meta = metadata;
  return JSON.stringify(entry);
}

export function createLogger(component, opts = {}) {
  const requestId = opts.requestId || null;

  const logger = {};

  for (const [level, priority] of Object.entries(LEVELS)) {
    logger[level] = (message, metadata) => {
      if (priority < LEVELS[LOG_LEVEL]) return;

      const line = formatEntry(level, component, message, metadata, requestId);
      if (level === 'error') console.error(line);
      else if (level === 'warn') console.warn(line);
      else console.log(line);
    };
  }

  logger.child = (childOpts) => {
    return createLogger(component, {
      requestId: childOpts.requestId || requestId,
    });
  };

  return logger;
}
