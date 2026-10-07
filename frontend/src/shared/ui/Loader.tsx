import styles from './ui.module.css';

export function Loader({ label = 'Загрузка...' }: { label?: string }) {
  return (
    <div className={styles.loaderWrap}>
      <div className={styles.loader} aria-hidden />
      <div>{label}</div>
    </div>
  );
}

export function Skeleton({ height = 16, width = '100%' }: { height?: number; width?: string | number }) {
  return <div className={styles.skeleton} style={{ height, width }} />;
}
