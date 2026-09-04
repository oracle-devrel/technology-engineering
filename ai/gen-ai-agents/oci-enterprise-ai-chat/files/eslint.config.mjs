// eslint-config-next v16 ships a native flat config — the old FlatCompat bridge
// crashes on it (circular structure error). `next lint` itself was removed in
// Next 16, so `npm run lint` invokes eslint directly against this config.
import coreWebVitals from "eslint-config-next/core-web-vitals";

const eslintConfig = [
  { ignores: [".next/**", "node_modules/**", "public/**", "tests/manual/**", ".claude/**"] },
  ...coreWebVitals,
  {
    rules: {
      // React Compiler advisories introduced with the v16 ruleset. The codebase
      // predates them (localStorage hydration via setState-in-effect everywhere);
      // they flag working patterns, not defects. Kept visible as warnings so new
      // code can avoid them — `rules-of-hooks` stays an error.
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/static-components": "warn",
      "react-hooks/purity": "warn",
      "react-hooks/preserve-manual-memoization": "warn",
      "react-hooks/use-memo": "warn",
      "react-hooks/refs": "warn",
      // Cosmetic: unescaped apostrophes/quotes in JSX copy.
      "react/no-unescaped-entities": "warn",
    },
  },
];

export default eslintConfig;
