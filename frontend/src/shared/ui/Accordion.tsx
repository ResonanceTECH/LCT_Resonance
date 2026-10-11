import { ChevronDown } from 'lucide-react';
import { useId, useState, type ReactNode } from 'react';
import styles from './ui.module.css';

export type AccordionItem = {
  id: string;
  title: string;
  content: ReactNode;
};

export function Accordion({
  items,
  defaultOpenId,
  allowMultiple = false,
  columns = 1,
  className,
}: {
  items: AccordionItem[];
  defaultOpenId?: string | null;
  allowMultiple?: boolean;
  /** Desktop column count; stacks to 1 below 768px when > 1. */
  columns?: 1 | 2;
  className?: string;
}) {
  const baseId = useId();
  const [openIds, setOpenIds] = useState<string[]>(() =>
    defaultOpenId ? [defaultOpenId] : items[0] ? [items[0].id] : [],
  );

  function toggle(id: string) {
    setOpenIds((prev) => {
      const isOpen = prev.includes(id);
      if (allowMultiple) {
        return isOpen ? prev.filter((x) => x !== id) : [...prev, id];
      }
      return isOpen ? [] : [id];
    });
  }

  return (
    <div
      className={[
        styles.accordion,
        columns === 2 ? styles.accordionCols2 : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {items.map((item) => {
        const open = openIds.includes(item.id);
        const panelId = `${baseId}-${item.id}-panel`;
        const buttonId = `${baseId}-${item.id}-button`;
        return (
          <div
            key={item.id}
            className={`${styles.accordionItem} ${open ? styles.accordionItemOpen : ''}`}
          >
            <h3 className={styles.accordionHeading}>
              <button
                id={buttonId}
                type="button"
                className={styles.accordionTrigger}
                aria-expanded={open}
                aria-controls={panelId}
                onClick={() => toggle(item.id)}
              >
                <span>{item.title}</span>
                <ChevronDown
                  className={styles.accordionIcon}
                  size={18}
                  strokeWidth={1.75}
                  aria-hidden
                />
              </button>
            </h3>
            <div
              id={panelId}
              role="region"
              aria-labelledby={buttonId}
              hidden={!open}
              className={styles.accordionPanel}
            >
              <div className={styles.accordionPanelInner}>{item.content}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
