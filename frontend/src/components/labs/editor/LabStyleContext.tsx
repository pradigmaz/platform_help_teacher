'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface LabStyleState {
  fontSize: string;
  lineHeight: string;
}

interface LabStyleContextValue {
  style: LabStyleState;
  setFontSize: (size: string) => void;
  setLineHeight: (height: string) => void;
}

const defaultStyle: LabStyleState = {
  fontSize: '16',
  lineHeight: '1.5',
};

const LabStyleContext = createContext<LabStyleContextValue | null>(null);

export function LabStyleProvider({ children }: { children: ReactNode }) {
  const [style, setStyle] = useState<LabStyleState>(defaultStyle);

  const setFontSize = useCallback((size: string) => {
    setStyle(prev => ({ ...prev, fontSize: size }));
  }, []);

  const setLineHeight = useCallback((height: string) => {
    setStyle(prev => ({ ...prev, lineHeight: height }));
  }, []);

  return (
    <LabStyleContext.Provider value={{ style, setFontSize, setLineHeight }}>
      {children}
    </LabStyleContext.Provider>
  );
}

export function useLabStyle() {
  const ctx = useContext(LabStyleContext);
  if (!ctx) {
    // Fallback если вне провайдера
    return { style: defaultStyle, setFontSize: () => {}, setLineHeight: () => {} };
  }
  return ctx;
}
