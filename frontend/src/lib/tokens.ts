export interface ModelToken {
  key: string;
  name: string;
  family: string;
  color: string;
  marker: string;
  markerShape: 'circle' | 'square' | 'diamond' | 'triangle' | 'triangle-down' | 'star' | 'cross';
  explainTier: 'native' | 'partial' | 'model_agnostic';
  isChampion?: boolean;
}

export const MODEL_TOKENS: Record<string, ModelToken> = {
  linreg: {
    key: 'linreg',
    name: 'Linear Regression (ScoreToBand)',
    family: 'linear',
    color: '#E69F00',
    marker: '●',
    markerShape: 'circle',
    explainTier: 'native',
  },
  logreg: {
    key: 'logreg',
    name: 'Logistic Regression',
    family: 'linear',
    color: '#56B4E9',
    marker: '■',
    markerShape: 'square',
    explainTier: 'native',
  },
  knn: {
    key: 'knn',
    name: 'K-Nearest Neighbours',
    family: 'instance_based',
    color: '#009E73',
    marker: '◆',
    markerShape: 'diamond',
    explainTier: 'native',
  },
  svm: {
    key: 'svm',
    name: 'Support Vector Machine (RBF)',
    family: 'kernel',
    color: '#F0E442',
    marker: '▲',
    markerShape: 'triangle',
    explainTier: 'model_agnostic',
  },
  dt: {
    key: 'dt',
    name: 'Decision Tree (CART)',
    family: 'tree',
    color: '#0072B2',
    marker: '▼',
    markerShape: 'triangle-down',
    explainTier: 'native',
  },
  rf: {
    key: 'rf',
    name: 'Random Forest',
    family: 'ensemble',
    color: '#D55E00',
    marker: '★',
    markerShape: 'star',
    explainTier: 'partial',
  },
  boost: {
    key: 'boost',
    name: 'Histogram Gradient Boosting (Champion)',
    family: 'boosting',
    color: '#CC79A7',
    marker: '✚',
    markerShape: 'cross',
    explainTier: 'partial',
    isChampion: true,
  },
};

export const CLASS_TOKENS = {
  Low: { label: 'Low', color: 'var(--class-low, #dc2626)', bg: 'rgba(220, 38, 38, 0.1)', border: '#f87171' },
  Medium: { label: 'Medium', color: 'var(--class-medium, #d97706)', bg: 'rgba(217, 119, 6, 0.1)', border: '#fbbf24' },
  High: { label: 'High', color: 'var(--class-high, #059669)', bg: 'rgba(5, 150, 105, 0.1)', border: '#34d399' },
} as const;
