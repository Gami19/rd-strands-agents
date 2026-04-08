import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import './App.css'
import { AppSidebar } from './components/AppSidebar'
import { ApprovalToolModal } from './components/ApprovalToolModal'
import { ChatThread } from './components/ChatThread'
import { ComposerPanel } from './components/ComposerPanel'
import { ProjectCreateModal } from './components/ProjectCreateModal'
import { ProjectSettingsModal } from './components/ProjectSettingsModal'
import { TeamLandingView } from './components/TeamLandingView'
import { TeamPrNoticeModal } from './components/TeamPrNoticeModal'
import { useAppLayerEscapes } from './hooks/useAppLayerEscapes'
import { useChatComposerLayout } from './hooks/useChatComposerLayout'
import { useChatStream } from './hooks/useChatStream'
import { useCopyText } from './hooks/useCopyText'
import { useProjectArtifactsAndAgents } from './hooks/useProjectArtifactsAndAgents'
import { useProjectFileUpload } from './hooks/useProjectFileUpload'
import { useProjectVault } from './hooks/useProjectVault'
import { useToast } from './hooks/useToast'
import { useWorkspaceFolderHelp } from './hooks/useWorkspaceFolderHelp'
import { useWorkspaceQuoteActions } from './hooks/useWorkspaceQuoteActions'
import type { TeamContextId } from './lib/teamContext'
import { workflowEnabled } from './lib/teamContext'

function App() {
  const { toast, showToast } = useToast()

  const [error, setError] = useState<string | null>(null)

  const clearApprovalAndErrorRef = useRef<() => void>(() => {})
  const isProjectDeleteBlockedRef = useRef(false)

  const stableClearApprovalAndError = useCallback(() => {
    clearApprovalAndErrorRef.current()
  }, [])

  const {
    activeProjectId,
    activeProjectListEntry,
    projectListError,
    projectListLoading,
    fetchProjectList,
    projectCreateOpen,
    setProjectCreateOpen,
    projectCreateId,
    setProjectCreateId,
    projectCreateDisplayName,
    setProjectCreateDisplayName,
    projectCreateTeamContext,
    setProjectCreateTeamContext,
    projectCreateBusy,
    projectCreateError,
    setProjectCreateError,
    projectSettingsOpen,
    projectSettingsDisplayName,
    setProjectSettingsDisplayName,
    projectSettingsTeamContext,
    setProjectSettingsTeamContext,
    projectSettingsBusy,
    projectSettingsError,
    openProjectSettings,
    closeProjectSettings,
    submitProjectSettings,
    teamPrNoticeOpen,
    confirmTeamPrNotice,
    closeTeamPrNotice,
    messages,
    setMessages,
    input,
    setInput,
    mode,
    setMode,
    agentId,
    setAgentId,
    uploadedRefs,
    setUploadedRefs,
    workspaceQuotes,
    setWorkspaceQuotes,
    teamLandingOpen,
    setTeamLandingOpen,
    applySwitchProject,
    submitCreateProject,
    deleteActiveProject,
    labelForProjectOption,
    projectOptions,
  } = useProjectVault({
    showToast,
    setError,
    clearApprovalAndError: stableClearApprovalAndError,
    isProjectDeleteBlockedRef,
  })

  const workflowAllowed = useMemo(() => {
    const e = activeProjectListEntry
    if (e?.meta_error) return false
    return workflowEnabled(e?.team_context ?? 'developer')
  }, [activeProjectListEntry])

  useEffect(() => {
    if (!workflowAllowed && mode === 'workflow') {
      setMode('skills')
    }
  }, [workflowAllowed, mode, setMode])

  const activeProjectTeamContextLabel = useMemo(() => {
    if (activeProjectListEntry?.meta_error) return null
    const l = activeProjectListEntry?.team_context_label
    return typeof l === 'string' && l ? l : null
  }, [activeProjectListEntry])

  const activeTeamContextForUi = useMemo((): TeamContextId => {
    if (activeProjectListEntry?.meta_error) return 'developer'
    const tc = activeProjectListEntry?.team_context
    const ids: TeamContextId[] = [
      'developer',
      'marketing',
      'hr',
      'pmo',
      'engineering',
    ]
    if (tc && ids.includes(tc as TeamContextId)) return tc as TeamContextId
    return 'developer'
  }, [activeProjectListEntry])

  useEffect(() => {
    const tc = activeTeamContextForUi
    if (tc === 'developer') {
      document.documentElement.removeAttribute('data-team-context')
    } else {
      document.documentElement.setAttribute('data-team-context', tc)
    }
    return () => {
      document.documentElement.removeAttribute('data-team-context')
    }
  }, [activeTeamContextForUi])

  const {
    agents,
    agentsLoading,
    agentsError,
    artifacts,
    artifactsLoading,
    artifactDeletingKey,
    loadArtifacts,
    loadAgents,
    deleteArtifact,
    artifactsByFolder,
  } = useProjectArtifactsAndAgents({
    activeProjectId,
    mode,
    agentId,
    setAgentId,
    setUploadedRefs,
    setError,
  })

  const {
    uploadBusy,
    attachModalOpen,
    setAttachModalOpen,
    uploadFiles,
  } = useProjectFileUpload({
    activeProjectId,
    setError,
    setUploadedRefs,
    loadArtifacts,
  })

  const [swarmAgentsConflictOpen, setSwarmAgentsConflictOpen] = useState(false)
  const {
    wrapRef: workspaceFolderHelpWrapRef,
    open: workspaceFolderHelpOpen,
    setOpen: setWorkspaceFolderHelpOpen,
    openHelp: openWorkspaceFolderHelp,
    scheduleClose: scheduleCloseWorkspaceFolderHelp,
    clearCloseTimer: clearWorkspaceFolderHelpTimer,
  } = useWorkspaceFolderHelp()

  const {
    listRef,
    fileInputRef,
    composerTextareaRef,
    scrollToBottom,
    autoResizeComposer,
  } = useChatComposerLayout(input)

  const {
    streaming,
    streamAssistantId,
    approvalSessionId,
    setApprovalSessionId,
    approvalInterrupts,
    approvalBusy,
    stopStreaming,
    send,
    resumeWithApproval,
    clearApprovalAndError,
  } = useChatStream({
    setError,
    messages,
    setMessages,
    input,
    setInput,
    workspaceQuotes,
    setWorkspaceQuotes,
    uploadedRefs,
    mode,
    agentId,
    activeProjectId,
    loadArtifacts,
    loadAgents,
    scrollToBottom,
    autoResizeComposer,
    setSwarmAgentsConflictOpen,
  })

  useLayoutEffect(() => {
    clearApprovalAndErrorRef.current = clearApprovalAndError
    isProjectDeleteBlockedRef.current =
      streaming || approvalInterrupts.length > 0 || approvalBusy
  }, [
    clearApprovalAndError,
    streaming,
    approvalInterrupts,
    approvalBusy,
  ])

  const { closeProjectCreateModal } = useAppLayerEscapes({
    attachModalOpen,
    setAttachModalOpen,
    projectCreateOpen,
    projectCreateBusy,
    setProjectCreateOpen,
    setProjectCreateError,
    projectSettingsOpen,
    projectSettingsBusy,
    onCloseProjectSettings: closeProjectSettings,
    teamPrNoticeOpen,
    onCloseTeamPrNotice: closeTeamPrNotice,
    swarmAgentsConflictOpen,
    setSwarmAgentsConflictOpen,
  })

  const { copyText } = useCopyText(showToast)

  const { insertWorkspaceTarget, removeWorkspaceQuote } =
    useWorkspaceQuoteActions(setWorkspaceQuotes, composerTextareaRef)

  const projectSelectDisabled =
    streaming || approvalInterrupts.length > 0 || approvalBusy

  const resetConversation = useCallback(() => {
    setMessages([])
    setError(null)
    setUploadedRefs([])
    setWorkspaceQuotes([])
  }, [setMessages, setUploadedRefs, setWorkspaceQuotes])

  const showTeamLanding = activeTeamContextForUi !== 'developer' && teamLandingOpen

  return (
    <div className="app" data-team-context={activeTeamContextForUi}>
      <AppSidebar
        activeProjectId={activeProjectId}
        projectOptions={projectOptions}
        labelForProjectOption={labelForProjectOption}
        activeProjectTeamContextLabel={activeProjectTeamContextLabel}
        activeProjectMetaError={activeProjectListEntry?.meta_error === true}
        activeProjectMetaDetail={
          typeof activeProjectListEntry?.detail === 'string'
            ? activeProjectListEntry.detail
            : null
        }
        projectListError={projectListError}
        projectListLoading={projectListLoading}
        onRetryProjectList={fetchProjectList}
        projectSelectDisabled={projectSelectDisabled}
        onSwitchProject={applySwitchProject}
        onOpenCreateProject={() => {
          setProjectCreateError(null)
          setProjectCreateId('')
          setProjectCreateDisplayName('')
          setProjectCreateTeamContext('developer')
          setProjectCreateOpen(true)
        }}
        onOpenProjectSettings={openProjectSettings}
        onDeleteProject={() => void deleteActiveProject()}
        projectCreateBusy={projectCreateBusy}
        projectSettingsBusy={projectSettingsBusy}
        onNewChat={resetConversation}
        workspaceFolderHelpWrapRef={workspaceFolderHelpWrapRef}
        workspaceFolderHelpOpen={workspaceFolderHelpOpen}
        openWorkspaceFolderHelp={openWorkspaceFolderHelp}
        scheduleCloseWorkspaceFolderHelp={scheduleCloseWorkspaceFolderHelp}
        clearWorkspaceFolderHelpTimer={clearWorkspaceFolderHelpTimer}
        setWorkspaceFolderHelpOpen={setWorkspaceFolderHelpOpen}
        onRefreshArtifacts={loadArtifacts}
        artifactsLoading={artifactsLoading}
        artifacts={artifacts}
        artifactsByFolder={artifactsByFolder}
        agents={agents}
        artifactDeletingKey={artifactDeletingKey}
        onInsertWorkspaceTarget={insertWorkspaceTarget}
        onDeleteArtifact={deleteArtifact}
      />
      <main className="main">
        {showTeamLanding ? (
          <TeamLandingView
            teamContext={activeTeamContextForUi}
            agents={agents}
            agentsLoading={agentsLoading}
            agentsError={agentsError}
            onStartChat={() => setTeamLandingOpen(false)}
            onRequestAgent={(nextAgentId) => {
              setMode('skills')
              setAgentId(nextAgentId)
              setTeamLandingOpen(false)
            }}
          />
        ) : (
          <>
            {activeTeamContextForUi !== 'developer' ? (
              <div className="team-back-row">
                <button
                  type="button"
                  className="team-back-btn"
                  onClick={() => setTeamLandingOpen(true)}
                >
                  Teamsに戻る
                </button>
              </div>
            ) : null}
            <ChatThread
              listRef={listRef}
              messages={messages}
              agents={agents}
              streaming={streaming}
              streamAssistantId={streamAssistantId}
              onCopyMessage={copyText}
            />
          </>
        )}
        {error ? <div className="banner-error">{error}</div> : null}
        {toast ? (
          <div className="toast" role="status" aria-live="polite">
            {toast}
          </div>
        ) : null}
        <ApprovalToolModal
          approvalSessionId={approvalSessionId}
          approvalBusy={approvalBusy}
          approvalInterrupts={approvalInterrupts}
          onDismiss={() => setApprovalSessionId(null)}
          onResume={resumeWithApproval}
        />
        <ProjectSettingsModal
          open={projectSettingsOpen}
          busy={projectSettingsBusy}
          projectId={activeProjectId}
          displayName={projectSettingsDisplayName}
          teamContext={projectSettingsTeamContext}
          error={projectSettingsError}
          onClose={closeProjectSettings}
          onChangeDisplayName={setProjectSettingsDisplayName}
          onChangeTeamContext={setProjectSettingsTeamContext}
          onSubmit={submitProjectSettings}
        />
        <ProjectCreateModal
          open={projectCreateOpen}
          projectCreateBusy={projectCreateBusy}
          projectCreateId={projectCreateId}
          projectCreateDisplayName={projectCreateDisplayName}
          projectCreateTeamContext={projectCreateTeamContext}
          projectCreateError={projectCreateError}
          onClose={closeProjectCreateModal}
          onChangeId={setProjectCreateId}
          onChangeDisplayName={setProjectCreateDisplayName}
          onChangeTeamContext={setProjectCreateTeamContext}
          onSubmit={submitCreateProject}
        />
        <TeamPrNoticeModal
          open={teamPrNoticeOpen}
          busy={false}
          onClose={closeTeamPrNotice}
          onConfirm={confirmTeamPrNotice}
        />
        {!showTeamLanding ? (
          <ComposerPanel
            streaming={streaming}
            workflowAllowed={workflowAllowed}
            activeTeamContext={activeTeamContextForUi}
            mode={mode}
            setMode={setMode}
            agentId={agentId}
            setAgentId={setAgentId}
            agents={agents}
            agentsLoading={agentsLoading}
            agentsError={agentsError}
            uploadedRefs={uploadedRefs}
            workspaceQuotes={workspaceQuotes}
            removeWorkspaceQuote={removeWorkspaceQuote}
            input={input}
            setInput={setInput}
            composerTextareaRef={composerTextareaRef}
            fileInputRef={fileInputRef}
            attachModalOpen={attachModalOpen}
            setAttachModalOpen={setAttachModalOpen}
            uploadBusy={uploadBusy}
            uploadFiles={uploadFiles}
            swarmAgentsConflictOpen={swarmAgentsConflictOpen}
            setSwarmAgentsConflictOpen={setSwarmAgentsConflictOpen}
            send={send}
            stopStreaming={stopStreaming}
            setWorkspaceQuotes={setWorkspaceQuotes}
          />
        ) : null}
      </main>
    </div>
  )
}

export default App
