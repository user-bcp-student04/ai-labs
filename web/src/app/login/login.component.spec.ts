import '@angular/compiler';
import type { Router } from '@angular/router';
import axios from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { LoginComponent } from './login.component';
import { createAxiosResponse, stubLocalStorage } from '../../testing/test-helpers';

vi.mock('axios', () => ({
  default: {
    post: vi.fn()
  }
}));

describe('LoginComponent HTTP behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('loads preferences, posts login, stores the session, and navigates', async () => {
    const storage = stubLocalStorage({
      workshop_preferences: JSON.stringify({ theme: 'dark' })
    });
    const navigate = vi.fn().mockResolvedValue(true);
    const component = new LoginComponent({ navigate } as unknown as Router);
    vi.mocked(axios.post).mockResolvedValueOnce(
      createAxiosResponse({ token: 'test-token', user: { username: 'student' } })
    );
    component.username = 'student';
    component.password = 'test-password';

    await component.login();

    expect(component.preferences).toEqual({ theme: 'dark', showTips: true, compact: false });
    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'test-password', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(storage.getItem('workshop_token')).toBe('test-token');
    expect(JSON.parse(storage.getItem('workshop_user') ?? '')).toEqual({ username: 'student' });
    expect(navigate).toHaveBeenCalledWith(['/dashboard']);
    expect(component.busy).toBe(false);
  });

  it('shows the backend login error and clears the busy state', async () => {
    stubLocalStorage();
    const component = new LoginComponent({ navigate: vi.fn() } as unknown as Router);
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(axios.post).mockRejectedValueOnce({
      response: { data: { message: 'Invalid credentials' } }
    });
    component.username = 'student';
    component.password = 'wrong-password';

    await component.login();

    expect(component.message).toContain('Invalid credentials');
    expect(component.busy).toBe(false);
    expect(console.error).toHaveBeenCalled();
  });
});
