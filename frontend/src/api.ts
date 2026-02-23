import { API_BASE_URL } from './config';
import type { ChatResponse } from './types';

export async function askResume(question: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Failed to fetch chat response');
  }

  return response.json() as Promise<ChatResponse>;
}
