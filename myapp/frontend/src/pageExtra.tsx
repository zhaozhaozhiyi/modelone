import React, { createContext, useContext } from 'react';
import { ICustomDialog } from './api/interface/kubeflowInterface';

export const PageExtraContext = createContext<ICustomDialog | undefined>(undefined);

export function PageExtraSection() {
  const info = useContext(PageExtraContext);
  if (!info?.content || !info.hit) return null;
  return (
    <section className="mo-page-extra">
      <h3 className="mo-page-extra-title">{info.title}</h3>
      <div className="mo-page-extra-body" dangerouslySetInnerHTML={{ __html: info.content }} />
    </section>
  );
}
