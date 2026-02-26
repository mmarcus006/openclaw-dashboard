/**
 * Custom Monaco theme — matches dashboard bg (#0f1219).
 * Inherits syntax highlighting from vs-dark, only overrides background colors.
 */

import type { editor } from 'monaco-editor';

export const openclawDarkTheme: editor.IStandaloneThemeData = {
  base: 'vs-dark',
  inherit: true,
  rules: [],
  colors: {
    'editor.background': '#0f1219',
    'editorGutter.background': '#0f1219',
    'editor.lineHighlightBackground': '#1a1f2e',
    'editor.selectionBackground': '#264f78',
    'editorLineNumber.foreground': '#4a5568',
    'editorLineNumber.activeForeground': '#a1abbe',
    'editorWidget.background': '#1a1f2e',
    'editorWidget.border': '#2a3040',
    'input.background': '#1a1f2e',
    'dropdown.background': '#1a1f2e',
    'list.hoverBackground': '#1a1f2e',
    'list.activeSelectionBackground': '#264f78',
  },
};

export const OPENCLAW_THEME_NAME = 'openclaw-dark';
