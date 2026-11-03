import '@angular/compiler';
import { ChangeDetectorRef, NgZone } from '@angular/core';
import type { Router } from '@angular/router';
import axios from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DashboardComponent } from './dashboard.component';
import { createAxiosResponse, stubLocalStorage } from '../../testing/test-helpers';

vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}));

function createDashboard(navigate = vi.fn().mockResolvedValue(true)) {
  const changeDetector = { detectChanges: vi.fn() } as unknown as ChangeDetectorRef;
  const zone = { run: (callback: () => void) => callback() } as unknown as NgZone;
  const component = new DashboardComponent({ navigate } as unknown as Router, changeDetector, zone);
  return { component, navigate, changeDetector };
}

describe('DashboardComponent HTTP behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('loads tasks with the session token and excludes archived tasks', async () => {
    stubLocalStorage({
      workshop_token: 'test-token',
      workshop_user: JSON.stringify({ username: 'student' })
    });
    const tasks = [
      { id: 1, title: 'Active task', description: 'Details', status: 'TODO', owner: 'student', priority: 'HIGH' },
      { id: 2, title: 'Archived task', description: '', status: 'ARCHIVED', owner: 'student', priority: 'LOW' }
    ];
    vi.mocked(axios.get).mockResolvedValueOnce(createAxiosResponse(tasks));
    const { component, changeDetector } = createDashboard();

    await component.ngOnInit();

    expect(axios.get).toHaveBeenCalledWith('http://localhost:8000/api/tasks?owner=student', {
      headers: { Authorization: 'Bearer test-token' }
    });
    expect(component.tasks).toEqual(tasks);
    expect(component.visibleTasks).toHaveLength(1);
    expect(component.visibleTasks[0].label).toBe('HIGH · STUDENT');
    expect(component.loading).toBe(false);
    expect(changeDetector.detectChanges).toHaveBeenCalled();
  });

  it('redirects to login when there is no session token', async () => {
    stubLocalStorage({ workshop_user: JSON.stringify({ username: 'student' }) });
    const { component, navigate } = createDashboard();

    await component.ngOnInit();

    expect(navigate).toHaveBeenCalledWith(['/login']);
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('shows the task request error and clears the loading state', async () => {
    stubLocalStorage({
      workshop_token: 'test-token',
      workshop_user: JSON.stringify({ username: 'student' })
    });
    vi.mocked(axios.get).mockRejectedValueOnce({ message: 'Network unavailable' });
    const { component } = createDashboard();

    await component.ngOnInit();

    expect(component.error).toBe('Network unavailable');
    expect(component.loading).toBe(false);
  });
});
