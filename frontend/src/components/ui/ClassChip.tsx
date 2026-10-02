import React from 'react';
import { AlertCircle, CheckCircle, HelpCircle } from 'lucide-react';
import './ClassChip.css';

interface ClassChipProps {
  status: 'High' | 'Medium' | 'Low' | 'Unknown';
}

export const ClassChip: React.FC<ClassChipProps> = ({ status }) => {
  const config = {
    High: { icon: CheckCircle, cls: 'chip-high', label: 'High' },
    Medium: { icon: HelpCircle, cls: 'chip-medium', label: 'Medium' },
    Low: { icon: AlertCircle, cls: 'chip-low', label: 'Low' },
    Unknown: { icon: HelpCircle, cls: 'chip-unknown', label: 'Unknown' },
  };

  const { icon: Icon, cls, label } = config[status] || config.Unknown;

  return (
    <span className={`class-chip ${cls}`} role="status" aria-label={`Status: ${label}`}>
      <Icon size={16} aria-hidden="true" className="chip-icon" />
      <span className="chip-label">{label}</span>
    </span>
  );
};
