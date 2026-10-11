import { Link } from 'react-router-dom';
import { legalPages, type LegalBlock } from '@/pages/landing/content';
import styles from './LegalPage.module.css';

type LegalSlug = keyof typeof legalPages;

function LegalBlocks({ blocks }: { blocks: readonly LegalBlock[] }) {
  return (
    <div className={styles.body}>
      {blocks.map((block, index) => {
        const key = `${block.type}-${index}`;
        switch (block.type) {
          case 'h2':
            return (
              <h2 key={key} className={styles.h2}>
                {block.text}
              </h2>
            );
          case 'h3':
            return (
              <h3 key={key} className={styles.h3}>
                {block.text}
              </h3>
            );
          case 'ul':
            return (
              <ul key={key} className={styles.list}>
                {block.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            );
          case 'dl':
            return (
              <dl key={key} className={styles.defs}>
                {block.items.map((item) => (
                  <div key={item.term} className={styles.defItem}>
                    <dt>{item.term}</dt>
                    <dd>{item.description}</dd>
                  </div>
                ))}
              </dl>
            );
          default:
            return (
              <p key={key} className={styles.paragraph}>
                {block.text}
              </p>
            );
        }
      })}
    </div>
  );
}

export function LegalPage({ slug }: { slug: LegalSlug }) {
  const doc = legalPages[slug];
  const privacyHref = slug === 'terms' ? '/privacy' : null;

  return (
    <div className={styles.page} data-testid="legal-page">
      <div className={styles.inner}>
        <Link className={styles.back} to="/">
          ← На лендинг
        </Link>
        <p className={styles.meta}>
          Версия {doc.version} · Вступает в силу {doc.effectiveDate}
        </p>
        <h1 className={styles.title}>{doc.title}</h1>
        {privacyHref ? (
          <p className={styles.crossLink}>
            Обработка персональных данных —{' '}
            <Link to={privacyHref}>Политика конфиденциальности</Link>
          </p>
        ) : null}
        <LegalBlocks blocks={doc.blocks} />
      </div>
    </div>
  );
}
