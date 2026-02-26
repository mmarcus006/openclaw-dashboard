/**
 * File type icon resolver — maps file extensions to Lucide icons.
 */

import { File, FileText, Braces, Image, FileCode, Terminal, FileType, Settings, Lock } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

const ICON_MAP: Record<string, LucideIcon> = {
  md: FileText,
  txt: FileText,
  json: Braces,
  jsonc: Braces,
  json5: Braces,
  yaml: Settings,
  yml: Settings,
  toml: Settings,
  png: Image,
  jpg: Image,
  jpeg: Image,
  gif: Image,
  webp: Image,
  ico: Image,
  svg: Image,
  py: FileCode,
  ts: FileCode,
  tsx: FileCode,
  js: FileCode,
  jsx: FileCode,
  css: FileCode,
  html: FileCode,
  sh: Terminal,
  bash: Terminal,
  zsh: Terminal,
  pdf: FileType,
  env: Lock,
};

export function getFileIcon(filename: string): LucideIcon {
  const ext = filename.split('.').pop()?.toLowerCase() ?? '';
  return ICON_MAP[ext] ?? File;
}
