import type { Dispatch, SetStateAction } from 'react'
import { useCallback } from 'react'
import { useEscapeToClose } from './useEscapeToClose'

export type UseAppLayerEscapesParams = {
  attachModalOpen: boolean
  setAttachModalOpen: Dispatch<SetStateAction<boolean>>
  projectCreateOpen: boolean
  projectCreateBusy: boolean
  setProjectCreateOpen: Dispatch<SetStateAction<boolean>>
  setProjectCreateError: Dispatch<SetStateAction<string | null>>
  projectSettingsOpen: boolean
  projectSettingsBusy: boolean
  onCloseProjectSettings: () => void
  teamPrNoticeOpen: boolean
  onCloseTeamPrNotice: () => void
  swarmAgentsConflictOpen: boolean
  setSwarmAgentsConflictOpen: Dispatch<SetStateAction<boolean>>
}

export function useAppLayerEscapes({
  attachModalOpen,
  setAttachModalOpen,
  projectCreateOpen,
  projectCreateBusy,
  setProjectCreateOpen,
  setProjectCreateError,
  projectSettingsOpen,
  projectSettingsBusy,
  onCloseProjectSettings,
  teamPrNoticeOpen,
  onCloseTeamPrNotice,
  swarmAgentsConflictOpen,
  setSwarmAgentsConflictOpen,
}: UseAppLayerEscapesParams) {
  const closeAttachModal = useCallback(() => {
    setAttachModalOpen(false)
  }, [setAttachModalOpen])

  const closeProjectCreateModal = useCallback(() => {
    setProjectCreateOpen(false)
    setProjectCreateError(null)
  }, [setProjectCreateOpen, setProjectCreateError])

  const closeSwarmConflictModal = useCallback(() => {
    setSwarmAgentsConflictOpen(false)
  }, [setSwarmAgentsConflictOpen])

  useEscapeToClose({ open: attachModalOpen, onClose: closeAttachModal })
  useEscapeToClose({
    open: projectCreateOpen,
    enabled: !projectCreateBusy,
    onClose: closeProjectCreateModal,
  })
  useEscapeToClose({
    open: projectSettingsOpen,
    enabled: !projectSettingsBusy,
    onClose: onCloseProjectSettings,
  })
  useEscapeToClose({
    open: teamPrNoticeOpen,
    onClose: onCloseTeamPrNotice,
  })
  useEscapeToClose({
    open: swarmAgentsConflictOpen,
    onClose: closeSwarmConflictModal,
  })

  return { closeProjectCreateModal }
}
