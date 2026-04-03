import { useState, useEffect } from 'react';

interface ModelConfig {
  id: string;
  name: string;
  type: string;
  hemisphere: string;
  weight: number;
  path?: string;
  size?: string;
  params?: string;
  endpoint?: string;
  apiKey?: string;
  modelId?: string;
}

export type MainTab = 'models' | 'chat' | 'lab' | 'journal' | 'settings';
export type ModelSubTab = 'local' | 'external';
export type PersonalityPreset = {
  id: string;
  name: string;
  icon: string;
  description: string;
  leftHemisphere: number;
  rightHemisphere: number;
  creativity: number;
  logic: number;
  empathy: number;
  entropy: number;
  color: string;
};

export type ExternalProvider = {
  id: string;
  name: string;
  icon: string;
  protocol: string;
  defaultEndpoint: string;
  authType: string;
  models?: string[];
};
