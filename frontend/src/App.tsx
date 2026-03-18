import { useEffect } from 'react'
import {
  BarVisualizer,
  SessionProvider,
  useAgent,
  useSession,
} from '@livekit/components-react'
import { TokenSource } from 'livekit-client'

import '@livekit/components-styles'

const sandboxId = import.meta.env.VITE_LIVEKIT_SANDBOX_ID ?? 'REPLACE_WITH_SANDBOX_ID'
const agentName = import.meta.env.VITE_LIVEKIT_AGENT_NAME ?? 'brainstorm-ai-agent'
const tokenSource = TokenSource.sandboxTokenServer(sandboxId)

export default function App() {
  const session = useSession(tokenSource, { agentName })

  useEffect(() => {
    session.start()

    return () => {
      session.end()
    }
  }, [session])

  return (
    <SessionProvider session={session}>
      <main className="page" data-lk-theme="default">
        <AgentAudioPanel />
      </main>
    </SessionProvider>
  )
}

function AgentAudioPanel() {
  const agent = useAgent()

  if (!agent.microphoneTrack) {
    return null
  }

  return (
    <div className="viz-wrap neon-border">
      <BarVisualizer
        track={agent.microphoneTrack}
        state={agent.state}
        barCount={18}
        options={{ minHeight: 8 }}
      />
    </div>
  )
}
