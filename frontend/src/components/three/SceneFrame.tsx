import { Component, useEffect, useState } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { Loader } from '@react-three/drei';

// Error Boundary for WebGL context loss or crashes
class ErrorBoundary extends Component<{ children: ReactNode, fallback: ReactNode }, { hasError: boolean }> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("3D Scene Error:", error, errorInfo);
  }
  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

// Memory Disposal hook to clean up renderer counts
const DisposeMemory = () => {
  const { gl, scene } = useThree();
  useEffect(() => {
    return () => {
      scene.traverse((object: any) => {
        if (!object.isMesh) return;
        object.geometry.dispose();
        if (object.material.isMaterial) {
          cleanMaterial(object.material);
        } else {
          for (const material of object.material) cleanMaterial(material);
        }
      });
      gl.dispose();
    };
  }, [gl, scene]);
  return null;
};

const cleanMaterial = (material: any) => {
  material.dispose();
  for (const key of Object.keys(material)) {
    const value = material[key];
    if (value && typeof value === 'object' && 'minFilter' in value) {
      value.dispose();
    }
  }
};

// Check for WebGL capability
const isWebGLAvailable = () => {
  try {
    const canvas = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
  } catch (e) {
    return false;
  }
};

interface SceneFrameProps {
  children: ReactNode;
  fallback: ReactNode;
  tier?: 'high' | 'low' | 'off';
  isPaused?: boolean;
}

export default function SceneFrame({ children, fallback, tier = 'high', isPaused = false }: SceneFrameProps) {
  const [webGL] = useState(isWebGLAvailable());
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mediaQuery.matches);
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  if (!webGL || tier === 'off' || reducedMotion) {
    return <>{fallback}</>;
  }

  return (
    <div style={{ width: '100%', height: '400px', position: 'relative' }}>
      <ErrorBoundary fallback={fallback}>
        <Canvas frameloop={isPaused ? "never" : "always"} dpr={tier === 'high' ? [1, 2] : 1}>
          <DisposeMemory />
          {children}
        </Canvas>
        <Loader />
      </ErrorBoundary>
    </div>
  );
}
