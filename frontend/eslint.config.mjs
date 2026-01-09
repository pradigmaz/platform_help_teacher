import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  // Disable React Compiler rules for third-party/complex components
  {
    files: [
      "src/components/molecule-ui/**",
      "src/components/animate-ui/**",
      "src/components/Stack.tsx",
      "src/components/ui/globe.tsx",
      "src/components/ui/dot-pattern.tsx",
      "src/components/ui/animated-theme-toggler.tsx",
      "src/components/schedule/LessonSheet.tsx",
      "src/components/schedule/hooks/useLectureData.ts",
      "src/components/lectures/VisualizationSandbox.tsx",
      "src/components/lectures/public/useLectureReader.ts",
      "src/app/admin/journal/components/GradeCell.tsx",
      "src/app/admin/journal/hooks/useJournalFilters.ts",
      "src/app/admin/attestation/scores/page.tsx",
      "src/app/report/**/page.tsx",
    ],
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/static-components": "off",
      "react-hooks/purity": "off",
      "react-hooks/refs": "off",
      "react-hooks/immutability": "off",
      "react-hooks/preserve-manual-memoization": "off",
    },
  },
]);

export default eslintConfig;
