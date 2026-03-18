import { NextResponse } from 'next/server';
import { AgentDispatchClient } from 'livekit-server-sdk';
import { AccessToken, type AccessTokenOptions, type VideoGrant } from 'livekit-server-sdk';
import { RoomConfiguration } from '@livekit/protocol';

type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

// NOTE: you are expected to define the following environment variables in `.env.local`:
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const ALLOWED_SANDBOX_ID = process.env.SANDBOX_ID;
const DEFAULT_AGENT_NAME = process.env.AGENT_NAME;

// don't cache the results
export const revalidate = 0;

export async function POST(req: Request) {
  try {
    if (LIVEKIT_URL === undefined) {
      throw new Error('LIVEKIT_URL is not defined');
    }
    if (API_KEY === undefined) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }
    if (API_SECRET === undefined) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    // Parse room config from request body.
    const body = await req.json();

    // Resolve sandbox ID from header, body, or configured default.
    const headerSandboxId = req.headers.get('x-sandbox-id')?.trim();
    const bodySandboxId = String(body?.sandbox_id ?? '').trim();
    const requestSandboxId = headerSandboxId || bodySandboxId || ALLOWED_SANDBOX_ID || '';

    // Enforce single sandbox usage if configured.
    if (ALLOWED_SANDBOX_ID && requestSandboxId && requestSandboxId !== ALLOWED_SANDBOX_ID) {
      return new NextResponse('Sandbox ID mismatch', { status: 403 });
    }

    const roomConfigJson = body?.room_config ?? {};
    const dispatchAgentName = DEFAULT_AGENT_NAME?.trim();
    if (
      dispatchAgentName &&
      (!Array.isArray(roomConfigJson.agents) || roomConfigJson.agents.length === 0)
    ) {
      roomConfigJson.agents = [{ agent_name: dispatchAgentName }];
    }

    // Recreate the RoomConfiguration object from JSON object.
    const roomConfig = RoomConfiguration.fromJson(roomConfigJson, { ignoreUnknownFields: true });

    // Generate participant token
    const participantName = 'user';
    const participantIdentity = `voice_assistant_user_${Math.floor(Math.random() * 10_000)}`;
    const roomName = `voice_assistant_room_${Math.floor(Math.random() * 10_000)}`;

    const participantToken = await createParticipantToken(
      { identity: participantIdentity, name: participantName },
      roomName,
      roomConfig
    );

    if (dispatchAgentName) {
      await createAgentDispatch(roomName, dispatchAgentName);
    }

    // Return connection details
    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantName,
      participantToken,
    };
    const headers = new Headers({
      'Cache-Control': 'no-store',
    });
    return NextResponse.json(data, { headers });
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}

async function createAgentDispatch(roomName: string, agentName: string): Promise<void> {
  if (!LIVEKIT_URL || !API_KEY || !API_SECRET) {
    return;
  }

  const dispatchHost = LIVEKIT_URL.replace(/^wss:\/\//, 'https://').replace(/^ws:\/\//, 'http://');
  const dispatchClient = new AgentDispatchClient(dispatchHost, API_KEY, API_SECRET);

  try {
    await dispatchClient.createDispatch(roomName, agentName);
  } catch (error) {
    // If dispatch already exists or transient error occurs, let room join continue.
    console.error('Failed to create agent dispatch', error);
  }
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  roomConfig: RoomConfiguration
): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: '15m',
  });
  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  if (roomConfig) {
    at.roomConfig = roomConfig;
  }

  return at.toJwt();
}
