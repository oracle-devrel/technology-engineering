/**
 * Widgets 2.0 — Streaming XML Parser
 *
 * Parses @@widget...@@ blocks containing XML-like widget syntax.
 * Supports character-by-character streaming (for real-time chat) and batch parsing (for saved conversations).
 *
 * Tree node structure:
 * { tag: string, attrs: {}, children: (Node|string)[], isComplete: boolean, parent: Node|null }
 */

const V2_OPEN_MARKER = '@@widget';
const V2_CLOSE_MARKER = '@@';

// Parser state machine modes
const MODE = {
  TEXT: 'text',
  TAG_OPEN: 'tag_open',       // saw <
  TAG_NAME: 'tag_name',       // reading tag name
  ATTR_SPACE: 'attr_space',   // between attrs
  ATTR_NAME: 'attr_name',     // reading attr name
  ATTR_EQ: 'attr_eq',         // saw =, expecting quote
  ATTR_VALUE: 'attr_value',   // inside "..."
  SELF_CLOSE: 'self_close',   // saw / after attrs
  CLOSE_TAG_START: 'close_tag_start', // saw </
  CLOSE_TAG_NAME: 'close_tag_name',   // reading closing tag name
};

function createNode(tag, parent = null) {
  return { tag, attrs: {}, children: [], isComplete: false, parent };
}

/**
 * Streaming char-by-char XML parser for v2 widgets.
 * Interface mirrors v1: processChar(), getState(), reset()
 */
export function createWidgetV2StreamParser() {
  let mode = MODE.TEXT;
  let root = createNode('root');
  let current = root;  // current node we're adding children to
  let textBuffer = '';
  let tagName = '';
  let attrName = '';
  let attrValue = '';
  let attrQuote = '';
  let pendingAttrs = {};
  let isClosingTag = false;

  function flushText() {
    if (textBuffer.trim()) {
      current.children.push(textBuffer);
    }
    textBuffer = '';
  }

  function openTag(name, attrs, selfClose) {
    flushText();
    const node = createNode(name, current);
    node.attrs = { ...attrs };
    if (selfClose) {
      node.isComplete = true;
    }
    current.children.push(node);
    if (!selfClose) {
      current = node;
    }
    return node;
  }

  function closeTag(name) {
    flushText();
    // Walk up to find matching open tag
    let target = current;
    while (target && target.tag !== name && target.parent) {
      target.isComplete = true;
      target = target.parent;
    }
    if (target && target.tag === name) {
      target.isComplete = true;
      current = target.parent || root;
    }
    // If no match found, just ignore the close tag (lenient parsing)
  }

  function getTreeSnapshot() {
    return cloneTree(root);
  }

  return {
    processChar(char) {
      switch (mode) {
        case MODE.TEXT: {
          if (char === '<') {
            mode = MODE.TAG_OPEN;
            tagName = '';
            pendingAttrs = {};
            isClosingTag = false;
            return { action: 'none' };
          }
          textBuffer += char;
          return { action: 'text', tree: getTreeSnapshot() };
        }

        case MODE.TAG_OPEN: {
          if (char === '/') {
            isClosingTag = true;
            mode = MODE.CLOSE_TAG_NAME;
            tagName = '';
            return { action: 'none' };
          }
          if (char === ' ' || char === '\n' || char === '\t') {
            // Stray < followed by whitespace — treat as text
            textBuffer += '<' + char;
            mode = MODE.TEXT;
            return { action: 'text', tree: getTreeSnapshot() };
          }
          tagName = char;
          mode = MODE.TAG_NAME;
          return { action: 'none' };
        }

        case MODE.TAG_NAME: {
          if (char === ' ' || char === '\t' || char === '\n') {
            mode = MODE.ATTR_SPACE;
            return { action: 'none' };
          }
          if (char === '/') {
            mode = MODE.SELF_CLOSE;
            return { action: 'none' };
          }
          if (char === '>') {
            const node = openTag(tagName, pendingAttrs, false);
            mode = MODE.TEXT;
            return { action: 'node_open', tag: tagName, tree: getTreeSnapshot() };
          }
          tagName += char;
          return { action: 'none' };
        }

        case MODE.ATTR_SPACE: {
          if (char === '/') {
            mode = MODE.SELF_CLOSE;
            return { action: 'none' };
          }
          if (char === '>') {
            const node = openTag(tagName, pendingAttrs, false);
            mode = MODE.TEXT;
            return { action: 'node_open', tag: tagName, tree: getTreeSnapshot() };
          }
          if (char !== ' ' && char !== '\t' && char !== '\n') {
            attrName = char;
            mode = MODE.ATTR_NAME;
          }
          return { action: 'none' };
        }

        case MODE.ATTR_NAME: {
          if (char === '=') {
            mode = MODE.ATTR_EQ;
            return { action: 'none' };
          }
          if (char === ' ' || char === '\t' || char === '\n') {
            // Boolean attribute (no =)
            pendingAttrs[attrName] = 'true';
            attrName = '';
            mode = MODE.ATTR_SPACE;
            return { action: 'none' };
          }
          if (char === '/') {
            if (attrName) pendingAttrs[attrName] = 'true';
            attrName = '';
            mode = MODE.SELF_CLOSE;
            return { action: 'none' };
          }
          if (char === '>') {
            if (attrName) pendingAttrs[attrName] = 'true';
            attrName = '';
            const node = openTag(tagName, pendingAttrs, false);
            mode = MODE.TEXT;
            return { action: 'node_open', tag: tagName, tree: getTreeSnapshot() };
          }
          attrName += char;
          return { action: 'none' };
        }

        case MODE.ATTR_EQ: {
          if (char === '"' || char === "'") {
            attrQuote = char;
            attrValue = '';
            mode = MODE.ATTR_VALUE;
            return { action: 'none' };
          }
          // Unquoted value — read until whitespace or > or /
          if (char !== ' ' && char !== '>' && char !== '/') {
            attrQuote = '';
            attrValue = char;
            mode = MODE.ATTR_VALUE;
            return { action: 'none' };
          }
          // Malformed — treat = as part of attr name, restart
          pendingAttrs[attrName] = '';
          attrName = '';
          mode = MODE.ATTR_SPACE;
          return { action: 'none' };
        }

        case MODE.ATTR_VALUE: {
          if (attrQuote) {
            if (char === attrQuote) {
              pendingAttrs[attrName] = attrValue;
              attrName = '';
              attrValue = '';
              attrQuote = '';
              mode = MODE.ATTR_SPACE;
              return { action: 'none' };
            }
            attrValue += char;
            return { action: 'none' };
          }
          // Unquoted value
          if (char === ' ' || char === '\t' || char === '\n') {
            pendingAttrs[attrName] = attrValue;
            attrName = '';
            attrValue = '';
            mode = MODE.ATTR_SPACE;
            return { action: 'none' };
          }
          if (char === '>') {
            pendingAttrs[attrName] = attrValue;
            attrName = '';
            attrValue = '';
            const node = openTag(tagName, pendingAttrs, false);
            mode = MODE.TEXT;
            return { action: 'node_open', tag: tagName, tree: getTreeSnapshot() };
          }
          if (char === '/') {
            pendingAttrs[attrName] = attrValue;
            attrName = '';
            attrValue = '';
            mode = MODE.SELF_CLOSE;
            return { action: 'none' };
          }
          attrValue += char;
          return { action: 'none' };
        }

        case MODE.SELF_CLOSE: {
          if (char === '>') {
            const node = openTag(tagName, pendingAttrs, true);
            mode = MODE.TEXT;
            return { action: 'node_self_close', tag: tagName, tree: getTreeSnapshot() };
          }
          // Not really a self-close, treat / as part of something
          mode = MODE.ATTR_SPACE;
          return { action: 'none' };
        }

        case MODE.CLOSE_TAG_NAME: {
          if (char === '>') {
            closeTag(tagName);
            mode = MODE.TEXT;
            return { action: 'node_close', tag: tagName, tree: getTreeSnapshot() };
          }
          if (char !== ' ' && char !== '\t' && char !== '\n') {
            tagName += char;
          }
          return { action: 'none' };
        }
      }

      return { action: 'none' };
    },

    getTree() {
      return getTreeSnapshot();
    },

    getState() {
      return { mode, current: current?.tag };
    },

    reset() {
      mode = MODE.TEXT;
      root = createNode('root');
      current = root;
      textBuffer = '';
      tagName = '';
      attrName = '';
      attrValue = '';
      attrQuote = '';
      pendingAttrs = {};
      isClosingTag = false;
    },

    finalize() {
      flushText();
      // Auto-close all unclosed tags
      while (current !== root) {
        current.isComplete = true;
        current = current.parent || root;
      }
      root.isComplete = true;
      return getTreeSnapshot();
    }
  };
}

/**
 * Clone a tree (strip parent references to avoid circular refs)
 */
function cloneTree(node) {
  if (typeof node === 'string') return node;
  return {
    tag: node.tag,
    attrs: { ...node.attrs },
    children: node.children.map(c => cloneTree(c)),
    isComplete: node.isComplete,
  };
}

/**
 * Batch-parse a complete v2 widget XML string (for saved conversations).
 * Returns a tree (root node with children).
 */
export function parseWidgetV2Complete(xmlString) {
  const parser = createWidgetV2StreamParser();
  for (const char of xmlString) {
    parser.processChar(char);
  }
  return parser.finalize();
}

/**
 * Serialize a v2 tree back to XML (for copy/export).
 */
export function serializeWidgetV2Tree(node, indent = 0) {
  if (typeof node === 'string') return node.trim();

  const pad = '  '.repeat(indent);

  if (node.tag === 'root') {
    return node.children
      .map(c => serializeWidgetV2Tree(c, indent))
      .filter(Boolean)
      .join('\n');
  }

  const attrStr = Object.entries(node.attrs)
    .map(([k, v]) => `${k}="${v}"`)
    .join(' ');
  const openTag = attrStr ? `<${node.tag} ${attrStr}` : `<${node.tag}`;

  if (node.children.length === 0) {
    return `${pad}${openTag} />`;
  }

  // Check if only text children
  const hasOnlyText = node.children.every(c => typeof c === 'string');
  if (hasOnlyText) {
    const text = node.children.join('').trim();
    return `${pad}${openTag}>${text}</${node.tag}>`;
  }

  const childrenStr = node.children
    .map(c => serializeWidgetV2Tree(c, indent + 1))
    .filter(Boolean)
    .join('\n');

  return `${pad}${openTag}>\n${childrenStr}\n${pad}</${node.tag}>`;
}

/**
 * Detect and extract v2 widget blocks from full text content.
 * Returns array of { type: 'text'|'widget_v2', content?, tree?, isComplete? }
 */
export function parseTextWithV2Widgets(content) {
  if (!content || typeof content !== 'string') return [];

  const segments = [];
  const v2Regex = /@@widget[ \t]*\n([\s\S]*?)@@/g;
  let lastIndex = 0;
  let match;

  while ((match = v2Regex.exec(content)) !== null) {
    const textBefore = content.slice(lastIndex, match.index).trim();
    if (textBefore) {
      segments.push({ type: 'text', content: textBefore, isStreaming: false });
    }

    const xmlContent = match[1];
    const tree = parseWidgetV2Complete(xmlContent);
    segments.push({
      type: 'widget_v2',
      tree,
      isComplete: true,
    });

    lastIndex = match.index + match[0].length;
  }

  const textAfter = content.slice(lastIndex).trim();
  if (textAfter) {
    segments.push({ type: 'text', content: textAfter, isStreaming: false });
  }

  return segments;
}
