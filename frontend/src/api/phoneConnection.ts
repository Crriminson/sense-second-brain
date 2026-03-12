/**
 * Phone WebSocket Connection
 * Connects to the backend's /api/phone endpoint to establish
 * a persistent communication channel for real-time interactions.
 */

type ConnectionListener = (connected: boolean) => void;
type MessageListener = (message: any) => void;

let ws: WebSocket | null = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000; // 2 seconds

const connectionListeners: Set<ConnectionListener> = new Set();
const messageListeners: Set<MessageListener> = new Set();

/**
 * Connect to the backend WebSocket endpoint
 * @param wsUrl - The WebSocket URL (e.g., ws://192.168.1.100:8000/api/phone)
 */
export function connectPhone(wsUrl: string): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      console.log(`[Phone] Connecting to ${wsUrl}`);
      
      ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log("[Phone] Connected to backend!");
        reconnectAttempts = 0;
        
        // Send initial handshake
        sendMessage({
          type: "handshake",
          client: "phone",
          timestamp: new Date().toISOString(),
        });
        
        notifyConnectionListeners(true);
        resolve();
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log("[Phone] Received:", message);
          notifyMessageListeners(message);
        } catch (e) {
          console.error("[Phone] Failed to parse message:", event.data);
        }
      };
      
      ws.onerror = (event) => {
        console.error("[Phone] WebSocket error:", event);
        reject(new Error("WebSocket connection failed"));
      };
      
      ws.onclose = () => {
        console.log("[Phone] Disconnected from backend");
        notifyConnectionListeners(false);
        attemptReconnect(wsUrl);
      };
      
    } catch (error) {
      console.error("[Phone] Connection error:", error);
      reject(error);
    }
  });
}

/**
 * Disconnect from the backend
 */
export function disconnectPhone(): void {
  if (ws) {
    ws.close();
    ws = null;
    reconnectAttempts = MAX_RECONNECT_ATTEMPTS; // Prevent auto-reconnect
  }
}

/**
 * Send a message to the backend via WebSocket
 */
export function sendMessage(message: any): void {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.warn("[Phone] WebSocket not open, cannot send message");
    return;
  }
  
  try {
    ws.send(JSON.stringify(message));
    console.log("[Phone] Sent:", message);
  } catch (error) {
    console.error("[Phone] Failed to send message:", error);
  }
}

/**
 * Send a text input to the backend for processing
 */
export function sendTextInput(text: string): void {
  sendMessage({
    type: "text_input",
    text: text.trim(),
    timestamp: new Date().toISOString(),
  });
}

/**
 * Send a ping to keep the connection alive
 */
export function sendPing(): void {
  sendMessage({ type: "ping" });
}

/**
 * Register a listener for connection state changes
 */
export function onConnectionChange(listener: ConnectionListener): () => void {
  connectionListeners.add(listener);
  return () => connectionListeners.delete(listener);
}

/**
 * Register a listener for incoming messages
 */
export function onMessage(listener: MessageListener): () => void {
  messageListeners.add(listener);
  return () => messageListeners.delete(listener);
}

/**
 * Get current connection status
 */
export function isConnected(): boolean {
  return ws !== null && ws.readyState === WebSocket.OPEN;
}

/**
 * Get the current WebSocket instance (for debugging)
 */
export function getWebSocket(): WebSocket | null {
  return ws;
}

// ─────────────────────────────────────────────────────────

function notifyConnectionListeners(connected: boolean): void {
  connectionListeners.forEach(listener => {
    try {
      listener(connected);
    } catch (error) {
      console.error("[Phone] Error in connection listener:", error);
    }
  });
}

function notifyMessageListeners(message: any): void {
  messageListeners.forEach(listener => {
    try {
      listener(message);
    } catch (error) {
      console.error("[Phone] Error in message listener:", error);
    }
  });
}

async function attemptReconnect(wsUrl: string): Promise<void> {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.log("[Phone] Max reconnection attempts reached");
    return;
  }
  
  reconnectAttempts++;
  const delay = RECONNECT_DELAY * reconnectAttempts;
  
  console.log(`[Phone] Attempting reconnection in ${delay}ms (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
  
  setTimeout(async () => {
    try {
      await connectPhone(wsUrl);
    } catch (error) {
      console.error("[Phone] Reconnection failed:", error);
    }
  }, delay);
}
