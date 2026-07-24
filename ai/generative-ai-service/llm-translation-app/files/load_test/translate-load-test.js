import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://92.5.61.234:8000';
const ENDPOINT = `${BASE_URL}/translate`;
const errorCounter = new Counter('errors');

export const options = {
  scenarios: {
    default: {
      executor: 'ramping-vus',
      gracefulRampDown: '90s',
      gracefulStop: '90s',
      stages: [
        { duration: __ENV.RAMP_UP_DURATION || '20s', target: Number(__ENV.TARGET_VUS || 20) },
        { duration: __ENV.STEADY_DURATION || '60s', target: Number(__ENV.TARGET_VUS || 20) },
        { duration: __ENV.RAMP_DOWN_DURATION || '40s', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate==0'],
    http_req_duration: ['p(95)<2000'],
    errors: ['count==0'],
  },
};

const payload = JSON.stringify({
  text: 'Place your wager on the next jackpot draw.',
  source_language: 'english',
  target_language: 'spanish-mx',
});

const params = {
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: __ENV.TIMEOUT || '90s',
};

function truncate(value, maxLength = 500) {
  if (!value) {
    return 'null';
  }

  return value.length > maxLength
    ? `${value.slice(0, maxLength)}...`
    : value;
}

function formatFailure(response) {
  const errorCode = response.error_code || 'n/a';
  const errorMessage = response.error || 'n/a';
  const status = response.status || 0;
  const contentType = response.headers['Content-Type'] || 'n/a';
  const body = truncate(response.body);

  if (status === 0) {
    return `Transport error: status=0 error_code=${errorCode} error=${errorMessage}`;
  }

  return `HTTP error: status=${status} error_code=${errorCode} error=${errorMessage} content_type=${contentType} body=${body}`;
}

export default function () {
  const response = http.post(ENDPOINT, payload, params);

  const ok = check(response, {
    'status is 200': (r) => r.status === 200,
    'response is json': (r) =>
      (r.headers['Content-Type'] || '').includes('application/json'),
    'response body is not empty': (r) => r.body && r.body.length > 0,
  });

  if (!ok) {
    errorCounter.add(1);
    console.log(`[k6-failure] ${formatFailure(response)}`);
  }

  sleep(Number(__ENV.SLEEP_SECONDS || 2));
}
