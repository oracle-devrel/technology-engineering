"use client"

import Image from "next/image"
import { ChevronsLeft, ChevronsRight, Github, LayoutGrid } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { useSidebar } from "@/components/ui/sidebar"
import { publicAssetPath } from "@/lib/public-assets"

const repositoryUrl = "https://github.com/adibirzu/oci-log-analytics-detections"

export function DashboardHeader() {
  const { toggleSidebar, state } = useSidebar()

  return (
    <header className="sticky top-0 z-10 flex h-[60px] items-center gap-4 border-b border-border bg-surface-sunken/85 px-6 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <Image src={publicAssetPath("/octo-logo.png")} width={34} height={34} alt="OCTO" className="h-9 w-9 object-contain" priority />
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden" onClick={toggleSidebar}>
                <LayoutGrid className="size-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Toggle Sidebar</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="hidden md:inline-flex" onClick={toggleSidebar}>
                {state === "expanded" ? <ChevronsLeft className="size-5" /> : <ChevronsRight className="size-5" />}
              </Button>
            </TooltipTrigger>
            <TooltipContent>{state === "expanded" ? "Collapse Sidebar" : "Expand Sidebar"}</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 items-center gap-3">
          <div className="hidden min-w-0 sm:block">
            <div className="truncate font-display text-sm font-semibold tracking-tight">Forge</div>
            <div className="truncate text-xs text-muted-foreground">Detection conversion console</div>
          </div>
          <span className="hidden h-7 w-px bg-border-strong/60 sm:block" aria-hidden="true" />
          <div className="truncate text-xs font-medium text-muted-foreground">OCI Log Analytics QL</div>
        </div>
      </div>
      <Button asChild variant="outline" size="sm">
        <a href={repositoryUrl} target="_blank" rel="noreferrer">
          <Github className="size-4" />
          Repo
        </a>
      </Button>
    </header>
  )
}
