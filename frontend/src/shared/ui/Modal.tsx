import { X } from 'lucide-react';
import type { ReactNode } from 'react';
import styles from './ui.module.css';
import { Button } from './Button';

export function Modal({
  open,
  title,
  children,
  onClose,
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  if (!open) return null;
  return (
    <div className={styles.modalBackdrop} role="presentation" onClick={onClose}>
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.modalHeader}>
          <h2>{title}</h2>
          <Button type="button" variant="ghost" size="sm" onClick={onClose} aria-label="Закрыть">
            <X size={18} strokeWidth={1.75} />
          </Button>
        </div>
        {children}
      </div>
    </div>
  );
}
