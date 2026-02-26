import { describe, it, expect } from 'vitest';
import { FileText, Braces, Image, FileCode, Terminal, File } from 'lucide-react';
import { getFileIcon } from '../fileIcons';

describe('getFileIcon', () => {
  it('returns FileText for .md files', () => {
    expect(getFileIcon('README.md')).toBe(FileText);
    expect(getFileIcon('AGENTS.md')).toBe(FileText);
  });

  it('returns Braces for .json files', () => {
    expect(getFileIcon('package.json')).toBe(Braces);
    expect(getFileIcon('tsconfig.json')).toBe(Braces);
  });

  it('returns Image for image files', () => {
    expect(getFileIcon('logo.png')).toBe(Image);
    expect(getFileIcon('photo.jpg')).toBe(Image);
    expect(getFileIcon('banner.webp')).toBe(Image);
  });

  it('returns FileCode for source code files', () => {
    expect(getFileIcon('main.py')).toBe(FileCode);
    expect(getFileIcon('index.ts')).toBe(FileCode);
    expect(getFileIcon('App.tsx')).toBe(FileCode);
    expect(getFileIcon('util.js')).toBe(FileCode);
    expect(getFileIcon('Component.jsx')).toBe(FileCode);
  });

  it('returns Terminal for shell scripts', () => {
    expect(getFileIcon('setup.sh')).toBe(Terminal);
    expect(getFileIcon('run.bash')).toBe(Terminal);
  });

  it('returns File as default fallback', () => {
    expect(getFileIcon('data.csv')).toBe(File);
    expect(getFileIcon('archive.zip')).toBe(File);
    expect(getFileIcon('unknownfile')).toBe(File);
  });
});
