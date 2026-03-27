import type { Loader } from 'astro/loaders'
import fs from 'node:fs'
import path from 'node:path'

type ExampleEntry = {
  id: string
  title: string
  description: string
  prerequisites: string
  code: string
  category: string
  categoryLabel: string
  order: number
  filename: string
  runCommand: string
}

interface CategoryMeta {
  label: string
  description: string
  slug: string
}

const CATEGORIES: Record<string, CategoryMeta> = {
  abi: {
    label: 'ABI Encoding',
    description: 'ABI type parsing, encoding, and decoding following the ARC-4 specification.',
    slug: 'abi',
  },
  algo25: {
    label: 'Mnemonic Utilities',
    description: 'Mnemonic and seed conversion utilities following the Algorand 25-word mnemonic standard.',
    slug: 'algo25',
  },
  algod_client: {
    label: 'Algod Client',
    description: 'Algorand node operations and queries using the AlgodClient.',
    slug: 'algod-client',
  },
  algorand_client: {
    label: 'Algorand Client',
    description: 'High-level AlgorandClient API for simplified blockchain interactions.',
    slug: 'algorand-client',
  },
  common: {
    label: 'Common Utilities',
    description: 'Utility functions and helpers.',
    slug: 'common',
  },
  indexer_client: {
    label: 'Indexer Client',
    description: 'Blockchain data queries using the IndexerClient.',
    slug: 'indexer-client',
  },
  kmd_client: {
    label: 'KMD Client',
    description: 'Key Management Daemon operations for wallet and key management.',
    slug: 'kmd-client',
  },
  transact: {
    label: 'Transactions',
    description: 'Low-level transaction construction and signing.',
    slug: 'transact',
  },
}

export function lineSeparator(text: string, isBullet: boolean, lastWasBullet: boolean): string {
  if (!text) return ''
  if (isBullet || lastWasBullet) return '\n'
  return ' '
}

export function parseDocstring(content: string): { title: string; description: string; prerequisites: string } {
  const docstringMatch = content.match(/"""([\s\S]*?)"""/)

  if (!docstringMatch) {
    return { title: 'Example', description: '', prerequisites: '' }
  }

  const docstringContent = docstringMatch[1]
  const lines = docstringContent.split('\n').map((line) => line.trim())

  // Extract title from "Example: Title" line
  const titleMatch = docstringContent.match(/Example:\s*(.+)/)
  const title = titleMatch?.[1]?.trim() || 'Example'

  let description = ''
  let prerequisites = ''
  let lastLineWasBullet = false

  for (const line of lines) {
    if (line.startsWith('Example:')) continue

    if (!line) {
      lastLineWasBullet = false
      if (description) {
        description += '\n'
      }
      continue
    }

    // Detect prerequisite lines (last meaningful line(s) about LocalNet)
    if (/^(no )?localnet/i.test(line) || /localnet (required|running)/i.test(line)) {
      prerequisites = line
      continue
    }

    const isBullet = line.startsWith('-') || line.startsWith('•')
    description += lineSeparator(description, isBullet, lastLineWasBullet) + line
    lastLineWasBullet = isBullet
  }

  return {
    title,
    description: description.trim(),
    prerequisites: prerequisites.trim() || 'LocalNet running (`algokit localnet start`)',
  }
}

/**
 * Extract order number from filename (e.g., "01_example.py" -> 1)
 */
export function extractOrder(filename: string): number {
  const match = filename.match(/^(\d+)_/)
  return match ? parseInt(match[1], 10) : 999
}

export function createSlug(filename: string): string {
  return filename.replace(/\.py$/, '').replace(/_/g, '-')
}

export function examplesLoader(): Loader {
  return {
    name: 'examples-loader',
    load: async ({ store, logger }) => {
      const examplesDir = path.resolve(process.cwd(), '..', 'examples')

      logger.info(`Loading examples from ${examplesDir}`)

      if (!fs.existsSync(examplesDir)) {
        logger.error(`Examples directory not found: ${examplesDir}`)
        return
      }

      const entries: ExampleEntry[] = []

      for (const [categoryDir, meta] of Object.entries(CATEGORIES)) {
        const categoryPath = path.join(examplesDir, categoryDir)

        if (!fs.existsSync(categoryPath)) {
          logger.warn(`Category directory not found: ${categoryPath}`)
          continue
        }

        const files = fs.readdirSync(categoryPath).filter((f) => f.endsWith('.py') && !f.startsWith('_'))

        for (const filename of files) {
          const filePath = path.join(categoryPath, filename)
          const content = fs.readFileSync(filePath, 'utf-8')
          const { title, description, prerequisites } = parseDocstring(content)
          const order = extractOrder(filename)
          const slug = createSlug(filename)

          const entry: ExampleEntry = {
            id: `${meta.slug}/${slug}`,
            title,
            description,
            prerequisites,
            code: content,
            category: categoryDir,
            categoryLabel: meta.label,
            order,
            filename,
            runCommand: `uv run python ${categoryDir}/${filename}`,
          }

          entries.push(entry)
        }
      }

      entries.sort((a, b) => {
        if (a.category !== b.category) {
          return a.category.localeCompare(b.category)
        }
        return a.order - b.order
      })

      logger.info(`Found ${entries.length} examples across ${Object.keys(CATEGORIES).length} categories`)

      for (const entry of entries) {
        store.set({
          id: entry.id,
          data: entry,
        })
      }
    },
  }
}

export { CATEGORIES }
export type { ExampleEntry, CategoryMeta }
