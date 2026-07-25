# Milestone 29: Dependency advisory remediation

## Outcome

Nova's locked development toolchain was compared with the OSV vulnerability
database on 25 July 2026 and upgraded to supported patched lines.

## Changes

- pytest is constrained to 9.0.3 or newer within major version 9.
- Vitest is constrained to 3.2.6 or newer within major version 3.
- ESLint and its first-party rules are upgraded to major version 10 so the
  resolved minimatch branch no longer retains an affected brace-expansion 1.x
  dependency.
- The pnpm lockfile is regenerated with pnpm 9.15.5.
- The resolved frontend set includes Vitest 3.2.7, Vite 6.4.3, esbuild 0.25.12,
  ESLint 10.8.0, and brace-expansion 5.0.8.

These packages are development and verification tools rather than code shipped
inside Nova's Python or Nginx runtime images. Updating them still matters
because tests run on the Windows development PC and in CI.

## Verification

The full Python and frontend quality suites pass with the new tools. A final
OSV batch scan of 357 exact PyPI and npm package versions reported no advisory
findings before publication.

The review addressed:

- [pytest advisory GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g)
- [Vitest advisory GHSA-5xrq-8626-4rwp](https://github.com/advisories/GHSA-5xrq-8626-4rwp)
- [esbuild advisory GHSA-67mh-4wv8-2f99](https://github.com/advisories/GHSA-67mh-4wv8-2f99)
- [brace-expansion advisory GHSA-mh99-v99m-4gvg](https://github.com/advisories/GHSA-mh99-v99m-4gvg)
