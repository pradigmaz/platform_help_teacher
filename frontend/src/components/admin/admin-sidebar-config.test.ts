import { describe, expect, it } from 'vitest';
import { getAdminSidebarItems } from './admin-sidebar-config';

describe('getAdminSidebarItems', () => {
  it('groups lectures and labs under course navigation', () => {
    const items = getAdminSidebarItems({ hasExams: false });
    const courseItem = items.find((item) => item.title === 'Курс');

    expect(courseItem?.subItems?.map((item) => item.title)).toEqual(['Лекции', 'Лабораторные']);
  });

  it('shows exams subitem only when exam offerings exist', () => {
    const withoutExams = getAdminSidebarItems({ hasExams: false });
    const withExams = getAdminSidebarItems({ hasExams: true });

    expect(withoutExams.some((item) => item.subItems?.some((subItem) => subItem.href === '/admin/exams'))).toBe(false);
    expect(withExams.some((item) => item.subItems?.some((subItem) => subItem.href === '/admin/exams'))).toBe(true);
  });
});
