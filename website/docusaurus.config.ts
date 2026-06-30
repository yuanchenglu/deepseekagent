import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'DeepSeek Agent',
  tagline: 'AI 智能助手，即装即用',
  favicon: 'img/favicon.ico',

  url: 'https://deepseekagent.starseas.org',
  baseUrl: '/',

  organizationName: '7ColorAI',
  projectName: 'deepagent',

  onBrokenLinks: 'warn',

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  themes: [
    '@docusaurus/theme-mermaid',
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      /** @type {import("@easyops-cn/docusaurus-search-local").PluginOptions} */
      ({
        hashed: true,
        language: ['en'],
        indexBlog: false,
        docsRouteBasePath: '/',
        highlightSearchTermsOnTargetPage: true,
      }),
    ],
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/yuanchenglu/DeepAgent/edit/main/website/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/hermes-agent-banner.png',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    docs: {
      sidebar: {
        hideable: true,
        autoCollapseCategories: true,
      },
    },
    navbar: {
      title: 'DeepSeek Agent',
      logo: {
        alt: 'DeepSeek Agent',
        src: 'img/logo.png',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: '文档',
        },
        {
          to: '/skills',
          label: '技能',
          position: 'left',
        },
        {
          href: 'https://github.com/yuanchenglu/DeepAgent',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: '文档',
          items: [
            { label: '快速开始', to: '/getting-started/quickstart' },
            { label: '用户指南', to: '/user-guide/cli' },
            { label: '开发指南', to: '/developer-guide/architecture' },
            { label: '参考', to: '/reference/cli-commands' },
          ],
        },
        {
          title: '社区',
          items: [
            { label: 'GitHub', href: 'https://github.com/yuanchenglu/DeepAgent' },
          ],
        },
        {
          title: '更多',
          items: [
            { label: '7ColorAI', href: '#' },
          ],
        },
      ],
      copyright: `由 <a href="#">7ColorAI</a> 构建 · MIT License · ${new Date().getFullYear()}`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'yaml', 'json', 'python', 'toml'],
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
