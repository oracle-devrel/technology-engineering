import { rename } from "node:fs/promises"
import { spawn } from "node:child_process"
import { join } from "node:path"
import { fileURLToPath } from "node:url"
import { dirname } from "node:path"

const appRoot = dirname(dirname(fileURLToPath(import.meta.url)))
const apiDir = join(appRoot, "app", "api")
const stagedApiDir = join(appRoot, ".next-pages-api-routes")

function runNextBuild() {
  return new Promise((resolve, reject) => {
    const child = spawn("pnpm", ["exec", "next", "build"], {
      cwd: appRoot,
      env: {
        ...process.env,
        NEXT_PUBLIC_FORGE_STATIC_EXPORT: "1",
      },
      stdio: "inherit",
    })

    child.on("error", reject)
    child.on("close", (code) => {
      if (code === 0) {
        resolve()
      } else {
        reject(new Error(`next build exited with ${code}`))
      }
    })
  })
}

async function main() {
  let apiStaged = false
  try {
    await rename(apiDir, stagedApiDir)
    apiStaged = true
    await runNextBuild()
  } finally {
    if (apiStaged) {
      await rename(stagedApiDir, apiDir)
    }
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exit(1)
})
