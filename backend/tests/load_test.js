import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '10s',
};

const BASE_URL = 'http://127.0.0.1:8000';

export default function () {
  const loginRes = http.post(`${BASE_URL}/api/v1/login`, {
    username: 'admin@hr.local',
    password: 'admin123',
  });

  check(loginRes, {
    'login is status 200': (r) => r.status === 200,
  });

  const token = loginRes.json('access_token');
  
  const payload = JSON.stringify({
    attendance: 95,
    experience_years: 5,
    training_hours: 100,
    projects_completed: 10,
    weekly_hours: 40,
    prev_score: 4,
    department: 'Engineering',
    job_level: 'Mid',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  };

  const predictRes = http.post(`${BASE_URL}/api/v1/predict`, payload, params);

  check(predictRes, {
    'predict is status 200': (r) => r.status === 200,
  });

  sleep(1);
}
