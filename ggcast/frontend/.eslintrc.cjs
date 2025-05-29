// ggcast/frontend/.eslintrc.cjs
module.exports = {
  root: true,
  env: { browser: true, es2020: true, node: true }, // Added node: true for CJS file itself
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    // 'prettier' // Add this if you have eslint-config-prettier and want its rules to override others
    // For now, we let Prettier handle formatting separately via its own pre-commit hook.
  ],
  ignorePatterns: [
    'dist',
    '.eslintrc.cjs',
    'vite.config.ts',
    'tailwind.config.js',
    'postcss.config.js',
  ], // Added common config files
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': [
      // Example: customize a rule
      'warn',
      { argsIgnorePattern: '^_' },
    ],
  },
};
