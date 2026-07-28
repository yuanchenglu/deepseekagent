/**
 * DeepAgent 版本发布日志
 * 每条记录包含版本号、发布日期和变更列表（i18n key）
 */

export interface ChangelogEntry {
  version: string;
  date: string;
  changes: string[];
}

export const changelog: ChangelogEntry[] = [
  {
    version: "0.9.0",
    date: "2026-07-27",
    changes: [
      "sidebar.changelog.initial",
      "sidebar.changelog.auth",
      "sidebar.changelog.electron",
    ],
  },
];
