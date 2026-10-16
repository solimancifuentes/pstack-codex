import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";

export function ensureDependenciesInstalled(): void {
  const scriptsDirectory = import.meta.dir;
  const key = createHash("sha256")
    .update(readFileSync(join(scriptsDirectory, "package.json")))
    .update("\0")
    .update(readFileSync(join(scriptsDirectory, "bun.lock")))
    .digest("hex");
  const marker = join(scriptsDirectory, "node_modules/.poteto-mode-tools-install-key");
  if (!existsSync(join(scriptsDirectory, "node_modules/commander/package.json")) ||
      !existsSync(marker) || readFileSync(marker, "utf8").trim() !== key) {
    throw new Error("pstack helpers are not prepared. Use the packaged tools/runtime.py tools-setup --yes launcher. No packages were installed.");
  }
}
