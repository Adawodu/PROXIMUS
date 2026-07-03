import { afterEach, describe, expect, it, vi } from 'vitest';
import { listResumes, createPhoneLink, updateResumeVoice } from './api';

afterEach(() => {
  vi.restoreAllMocks();
});

function mockFetch(status: number, body: unknown) {
  return vi.spyOn(globalThis, 'fetch').mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: 'Error',
    json: async () => body,
  } as Response);
}

describe('api request()', () => {
  it('calls the resumes endpoint and returns parsed data', async () => {
    const fetchSpy = mockFetch(200, { resumes: [], total: 0 });
    const result = await listResumes();
    expect(result).toEqual({ resumes: [], total: 0 });
    expect(fetchSpy).toHaveBeenCalledWith('/api/resumes', undefined);
  });

  it('throws with the API detail message on error responses', async () => {
    mockFetch(404, { detail: 'Resume not found' });
    await expect(listResumes()).rejects.toThrow('Resume not found');
  });

  it('POSTs phone links with a JSON body', async () => {
    const fetchSpy = mockFetch(200, { phone: '+14155550100', resume_id: 'r1', candidate_name: 'Jane' });
    await createPhoneLink({ phone: '+14155550100', resume_id: 'r1' });
    const [url, options] = fetchSpy.mock.calls[0];
    expect(url).toBe('/api/phone-links');
    expect(options?.method).toBe('POST');
    expect(JSON.parse(options?.body as string)).toEqual({ phone: '+14155550100', resume_id: 'r1' });
  });

  it('PATCHes a resume voice', async () => {
    const fetchSpy = mockFetch(200, { id: 'r1', voice: 'v-1' });
    await updateResumeVoice('r1', 'v-1');
    const [url, options] = fetchSpy.mock.calls[0];
    expect(url).toBe('/api/resumes/r1');
    expect(options?.method).toBe('PATCH');
    expect(JSON.parse(options?.body as string)).toEqual({ voice: 'v-1' });
  });
});
