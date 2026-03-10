import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export type PodcastStatus = 'pending' | 'extracting' | 'generating' | 'converting' | 'completed' | 'failed';

export interface Podcast {
  id: string;
  filename: string;
  status: PodcastStatus;
  progress?: string;
  progress_message?: string;
  audio_url?: string;
  error?: string;
  mode?: string;
  voice_preset?: string;
  created_at: string;
}

export interface UploadResponse {
  podcast_id: string;
  filename: string;
  status: string;
  message: string;
}

export interface StatusResponse {
  podcast_id: string;
  status: string;
  progress?: string;
  progress_message?: string;
  audio_url?: string;
  error?: string;
}

export interface VoicePreset {
  id: string;
  name: string;
  speakers: {
    SPEAKER_A: { voice: string; gender: string };
    SPEAKER_B: { voice: string; gender: string };
  };
}

export interface VoicePresetsResponse {
  presets: VoicePreset[];
}

export const uploadPDF = async (
  file: File,
  title: string,
  description?: string,
  mode: string = 'single',
  voicePreset: string = 'default',
  onProgress?: (progress: number) => void
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  if (description) {
    formData.append('description', description);
  }
  formData.append('mode', mode);
  formData.append('voice_preset', voicePreset);

  const response = await api.post<UploadResponse>('/api/v1/podcasts', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });

  return response.data;
};

export const listPodcasts = async (): Promise<Podcast[]> => {
  const response = await api.get<Podcast[]>('/api/v1/podcasts');
  return response.data;
};

export const getPodcastStatus = async (podcastId: string): Promise<StatusResponse> => {
  const response = await api.get<StatusResponse>(`/api/v1/podcasts/${podcastId}/status`);
  return response.data;
};

export const deletePodcast = async (podcastId: string): Promise<void> => {
  await api.delete(`/api/v1/podcasts/${podcastId}`);
};

export const getAudioUrl = (podcastId: string): string => {
  return `${API_BASE_URL}/api/v1/podcasts/${podcastId}/audio`;
};

export const getVoicePresets = async (): Promise<VoicePresetsResponse> => {
  const response = await api.get<VoicePresetsResponse>('/api/v1/voice-presets');
  return response.data;
};
