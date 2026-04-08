export const ARTIFACT_FOLDERS = [
  'agents',
  'decision',
  'inbox',
  'notes',
  'proposal',
] as const

export function artifactFilePathUrl(
  projectId: string,
  folder: string,
  filename: string,
) {
  return `/api/files/${projectId}/${folder}/${encodeURIComponent(filename)}`
}
