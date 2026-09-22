import React, { useEffect, useState } from 'react';
import { Select } from 'antd';
import { ApartmentOutlined } from '@ant-design/icons';
import api from './api';

// 顶栏全局项目切换器：选择结果持久化到本地存储，
// 通用列表页（ADUGTemplate）在元数据包含 project 过滤列时默认按该项目过滤。
const STORAGE_KEY = 'modelone_current_project';

export interface ICurrentProject {
  id: number;
  name: string;
}

export const getCurrentProject = (): ICurrentProject | null => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed.id === 'number' && parsed.name ? parsed : null;
  } catch (error) {
    return null;
  }
};

const listeners = new Set<() => void>();

export const subscribeProjectChange = (listener: () => void): (() => void) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};

const emitProjectChange = () => {
  listeners.forEach((listener) => listener());
};

export const ProjectSwitcher: React.FC = () => {
  const [options, setOptions] = useState<Array<{ label: string; value: number }>>([]);
  const [current, setCurrent] = useState<number>(getCurrentProject()?.id || 0);

  useEffect(() => {
    api
      .get('/project_modelview/api/', {
        params: { form_data: JSON.stringify({ page: 0, page_size: 500, str_related: 1 }) },
        headers: { 'X-Silent-Error': 'true' },
      })
      .then((res) => {
        const rows = res?.data?.result?.data || [];
        setOptions(rows.map((row: any) => ({ label: row.name, value: row.id })));
      })
      .catch(() => setOptions([]));
  }, []);

  return (
    <div className="mo-project-switcher">
      <ApartmentOutlined />
      <Select
        className="mo-project-switcher-select"
        dropdownClassName="mo-project-switcher-dropdown"
        value={current}
        showSearch
        optionFilterProp="label"
        options={[{ label: '全部项目', value: 0 }, ...options]}
        onChange={(value: number) => {
          setCurrent(value);
          const target = options.find((item) => item.value === value);
          if (value && target) {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({ id: value, name: target.label }));
          } else {
            localStorage.removeItem(STORAGE_KEY);
          }
          emitProjectChange();
        }}
      />
    </div>
  );
};
