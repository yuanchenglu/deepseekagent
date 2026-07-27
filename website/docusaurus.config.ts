import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'DeepAgent',
  tagline: 'CLI Alpha for macOS Apple Silicon',
  favicon: 'img/favicon.ico',

  url: 'https://deepseekagent.starseas.org',
  baseUrl: '/docs/',

  organizationName: '7ColorAI',
  projectName: 'deepagent',

  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
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
          include: [
            'index.md',
            'getting-started/quickstart.md',
            'getting-started/installation.md',
            'getting-started/termux.md',
            'reference/faq.md',
            'developer-guide/contributing.md',
          ],
          editUrl: 'https://github.com/yuanchenglu/deepseekagent/edit/main/website/',
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
      title: 'DeepAgent',
      logo: {
        alt: 'DeepAgent',
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
          href: 'https://github.com/yuanchenglu/deepseekagent',
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
            { label: '安装', to: '/getting-started/installation' },
            { label: 'CLI Alpha FAQ', to: '/reference/faq' },
            { label: '贡献', to: '/developer-guide/contributing' },
          ],
        },
        {
          title: '社区',
          items: [
            { label: 'GitHub', href: 'https://github.com/yuanchenglu/deepseekagent' },
          ],
        },
        {
          title: '更多',
          items: [
            { label: '7ColorAI', href: '#' },
          ],
        },
      ],
      copyright: `由 <a href="#">7ColorAI</a> 构建 · Core MIT / UI BSL-1.1 · ${new Date().getFullYear()}`,
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
