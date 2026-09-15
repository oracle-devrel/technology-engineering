const WIDGET_MARKER = '§§';
const PROP_SEPARATORS = ['|', '\n'];
const KEY_VALUE_SEPARATOR = ':';

export function createWidgetStreamParser() {
  let mode = 'streaming';
  let buffer = '';
  let widgetData = {};
  let keyCounts = {}; // Track duplicate keys
  let currentKey = '';
  let currentValue = '';
  let parsingKey = true;
  let pendingChar = null; // Buffer for single §

  function getUniqueKey(key) {
    if (widgetData[key] !== undefined) {
      keyCounts[key] = (keyCounts[key] || 1) + 1;
      return `${key}${keyCounts[key]}`;
    }
    return key;
  }

  function emitUpdate() {
    return {
      action: 'update_widget',
      widget: { ...widgetData },
      currentKey,
      currentValue,
      isComplete: false
    };
  }

  return {
    processChar(char) {
      // Handle pending § from previous call
      if (mode === 'streaming') {
        if (pendingChar === '§') {
          if (char === '§') {
            // §§ detected - start widget
            pendingChar = null;
            mode = 'buffering';
            buffer = '';
            widgetData = {};
            keyCounts = {};
            currentKey = '';
            currentValue = '';
            parsingKey = true;
            return { action: 'start_widget' };
          } else {
            // Previous § was just text, emit it + current char
            pendingChar = null;
            return { action: 'append', char: '§' + char };
          }
        }

        if (char === '§') {
          // Hold this § and wait for next char
          pendingChar = '§';
          return { action: 'none' };
        }

        return { action: 'append', char };
      }

      if (mode === 'buffering') {
        // Handle pending § inside widget
        if (pendingChar === '§') {
          if (char === '§') {
            // §§ detected - close widget
            pendingChar = null;
            if (currentKey && currentValue) {
              const uniqueKey = getUniqueKey(currentKey);
              widgetData[uniqueKey] = currentValue;
            }
            mode = 'streaming';
            const finalWidget = { ...widgetData };
            widgetData = {};
            keyCounts = {};
            currentKey = '';
            currentValue = '';
            return { action: 'close_widget', widget: finalWidget };
          } else {
            // Previous § was part of value
            pendingChar = null;
            currentValue += '§' + char;
            return {
              action: 'stream_value',
              key: currentKey,
              value: currentValue,
              widget: currentKey ? { ...widgetData, [currentKey]: currentValue } : { ...widgetData }
            };
          }
        }

        if (char === '§') {
          // Hold this § and wait for next char
          pendingChar = '§';
          return { action: 'none' };
        }

        buffer += char;

        if (PROP_SEPARATORS.includes(char)) {
          // body is greedy: | and \n are part of the value, not field separators
          if (currentKey === 'body') {
            currentValue += '\n';
            return { action: 'stream_value', key: currentKey, value: currentValue, widget: { ...widgetData, body: currentValue } };
          }
          if (currentKey) {
            const uniqueKey = getUniqueKey(currentKey);
            widgetData[uniqueKey] = currentValue;
          }
          currentKey = '';
          currentValue = '';
          parsingKey = true;
          return emitUpdate();
        }

        if (char === KEY_VALUE_SEPARATOR && parsingKey) {
          parsingKey = false;
          return { action: 'new_key', key: currentKey, widget: { ...widgetData } };
        }

        if (parsingKey) {
          currentKey += char;
          return { action: 'none' };
        } else {
          currentValue += char;
          return {
            action: 'stream_value',
            key: currentKey,
            value: currentValue,
            widget: currentKey ? { ...widgetData, [currentKey]: currentValue } : { ...widgetData }
          };
        }
      }

      return { action: 'none' };
    },

    getState() {
      return { mode, buffer, widgetData, currentKey, currentValue, pendingChar };
    },

    reset() {
      mode = 'streaming';
      buffer = '';
      widgetData = {};
      keyCounts = {};
      currentKey = '';
      currentValue = '';
      parsingKey = true;
      pendingChar = null;
    }
  };
}

export function parseWidgetProps(propsString) {
  const props = {};
  const keyCounts = {};
  const pendingListItems = [];

  // body: is a greedy field — it consumes everything after it (may contain | and \n)
  const bodyIdx = propsString.search(/(?:^|\||\n)body:/);
  let mainString = propsString;
  if (bodyIdx !== -1) {
    const bodyStart = propsString.indexOf('body:', bodyIdx);
    const bodyValue = propsString.substring(bodyStart + 'body:'.length);
    props.body = bodyValue.replace(/\|/g, '\n').trim();
    mainString = propsString.substring(0, bodyIdx === 0 ? 0 : bodyIdx + 1);
  }

  const pairs = mainString.split(/[|\n]/);

  for (const pair of pairs) {
    const trimmed = pair.trim();
    const sepIndex = trimmed.indexOf(KEY_VALUE_SEPARATOR);

    // Collect bare list items (lines starting with -) for ls: field
    if (sepIndex <= 0 && trimmed.startsWith('-')) {
      pendingListItems.push(trimmed.replace(/^-\s*/, ''));
      continue;
    }

    if (sepIndex > 0) {
      let key = trimmed.substring(0, sepIndex).trim();
      const value = trimmed.substring(sepIndex + 1).trim();

      // Allow empty values for ls: (items may follow as bare - lines)
      if (key && (value || key === 'ls')) {
        // Auto-number duplicate keys
        if (props[key] !== undefined) {
          keyCounts[key] = (keyCounts[key] || 1) + 1;
          key = `${key}${keyCounts[key]}`;
        }
        props[key] = value;
      }
    }
  }

  // Append collected bare list items to ls: field
  if (pendingListItems.length > 0) {
    const existing = props.ls ? props.ls.split(';').filter(Boolean) : [];
    props.ls = [...existing, ...pendingListItems].join(';');
  }

  return props;
}

export function parseCompleteText(text) {
  const segments = [];
  let currentText = '';
  let i = 0;

  while (i < text.length) {
    if (text.substring(i, i + 2) === WIDGET_MARKER) {
      if (currentText) {
        segments.push({ type: 'text', content: currentText });
        currentText = '';
      }

      const endIndex = text.indexOf(WIDGET_MARKER, i + 2);
      if (endIndex > -1) {
        const widgetContent = text.substring(i + 2, endIndex);
        const props = parseWidgetProps(widgetContent);

        segments.push({
          type: 'widget',
          props
        });

        i = endIndex + 2;
      } else {
        // No closing §§ found - try to parse as unclosed widget
        // Take content up to first double newline or end of text
        const remaining = text.substring(i + 2);
        const breakIndex = remaining.indexOf('\n\n');
        const widgetContent = breakIndex > -1 ? remaining.substring(0, breakIndex) : remaining;
        const props = parseWidgetProps(widgetContent);

        // Only treat as widget if we got meaningful props (at least a type key)
        const hasWidgetType = Object.keys(props).some(k => ['sec', 'risk', 'ck', 'tl', 'tb', 'kpi', 'mail', 'poll'].includes(k));
        if (hasWidgetType) {
          segments.push({ type: 'widget', props });
          i = i + 2 + (breakIndex > -1 ? breakIndex : remaining.length);
        } else {
          currentText += text[i];
          i++;
        }
      }
    } else {
      currentText += text[i];
      i++;
    }
  }

  if (currentText) {
    segments.push({ type: 'text', content: currentText });
  }

  return segments;
}

export const CONTENT_KEYS = {
  t: 'title',
  s: 'subtitle',
  d: 'description',
  i: 'image',
  ic: 'icon',
  n: 'number',
  p: 'progress',
  q: 'quote',
  cd: 'code',
  ls: 'list',
  lk: 'links',
  au: 'audio',
  st: 'status',
  cal: 'calendar',
  dy: 'day',
  ev: 'event',
  // New structured widgets
  tl: 'timeline',
  tb: 'table',
  ck: 'checklist',
  sec: 'section',
  risk: 'risk',
  kpi: 'kpi',
  mail: 'mail',
  poll: 'poll',
  op: 'option',
  subj: 'subject',
  to: 'to',
  from: 'from',
  cc: 'cc',
  body: 'body',
  // Sub-elements for structured widgets
  ph: 'phase',
  h: 'header',
  r: 'row',
  done: 'done',
  todo: 'todo',
  blocked: 'blocked'
};

export const LAYOUT_KEYS = {
  grid: 'grid',
  cols: 'columns'
};

export const CHART_KEYS = {
  ch_ln: 'lineChart',
  ch_br: 'barChart',
  ch_pie: 'pieChart',
  ch_don: 'donutChart'
};

export const INTERACTIVE_KEYS = {
  in: 'input',
  ta: 'textarea',
  bt: 'button',
  sl: 'select',
  cb: 'checkbox',
  rg: 'range',
  rd: 'radio',
  ms: 'multiselect',
  dt: 'date',
  tm: 'time',
  rt: 'rating',
  tg: 'toggle'
};

export const STYLE_KEYS = {
  _c: 'color',
  _bg: 'background',
  _sz: 'size',
  _rd: 'radius',
  _sh: 'shadow',
  _w: 'width',
  _h: 'height',
  _dir: 'direction',
  _al: 'align',
  _g: 'gap',
  _id: 'id',
  _rows: 'rows',
  _dark: 'dark',
  _center: 'center'
};

export const POSITION_MODIFIERS = ['@t', '@b', '@l', '@r', '@bg', '@ov'];

export function parseKey(key) {
  let position = null;
  let baseKey = key;

  for (const mod of POSITION_MODIFIERS) {
    if (key.includes(mod)) {
      position = mod.substring(1);
      baseKey = key.replace(mod, '');
      break;
    }
  }

  // Strip trailing numbers from auto-numbered keys (sl2 -> sl, in3 -> in)
  const baseWithoutNumber = baseKey.replace(/\d+$/, '');

  const isStyle = baseWithoutNumber.startsWith('_');
  const keyName = isStyle ? STYLE_KEYS[baseWithoutNumber] : (CONTENT_KEYS[baseWithoutNumber] || INTERACTIVE_KEYS[baseWithoutNumber] || LAYOUT_KEYS[baseWithoutNumber]);

  return {
    raw: key,
    base: baseWithoutNumber,
    name: keyName || baseWithoutNumber,
    position,
    isStyle
  };
}
