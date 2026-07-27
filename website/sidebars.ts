import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    'index',
    {
      type: 'category',
      label: 'CLI Alpha',
      items: [
        'getting-started/quickstart',
        'getting-started/installation',
        'getting-started/termux',
        'reference/faq',
      ],
    },
    'developer-guide/contributing',
  ],
};

export default sidebars;
