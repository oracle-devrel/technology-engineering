const createWebSocketService = ({ userId, onMessage, onStatusChange }) => {
  let ws = null;
  let reconnectTimer = null;
  let pingTimer = null;
  const reconnectInterval = 5000;

  const connect = () => {
    const channelId = process.env.NEXT_PUBLIC_ODA_CHANNEL_ID;
    const uri = process.env.NEXT_PUBLIC_ODA_URI;

    if (!channelId || !uri) {
      console.error("Missing configuration for chat service");
      onStatusChange(3); // 3 = CLOSED
      return;
    }

    if (pingTimer) clearInterval(pingTimer);
    if (reconnectTimer) clearTimeout(reconnectTimer);

    const url = `wss://${uri}/chat/v1/chats/sockets/websdk?channelId=${channelId}&userId=${userId}`;

    try {
      onStatusChange(0); // 0 = CONNECTING

      ws = new WebSocket(url);

      ws.onopen = () => {
        onStatusChange(1); // 1 = OPEN

        pingTimer = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ state: { type: "ping" } }));
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.state && data.state.type === "ping") {
            ws.send(JSON.stringify({ state: { type: "pong" } }));
            return;
          }

          onMessage(data);
        } catch (e) {
          console.error("Error parsing message:", e);
        }
      };

      ws.onclose = () => {
        onStatusChange(3); // 3 = CLOSED

        reconnectTimer = setTimeout(connect, reconnectInterval);
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        onStatusChange(3); // 3 = CLOSED
      };
    } catch (err) {
      console.error("Error setting up WebSocket:", err);
      onStatusChange(3); // 3 = CLOSED

      reconnectTimer = setTimeout(connect, reconnectInterval);
    }

    return ws;
  };

  const disconnect = () => {
    if (ws) {
      ws.close();
      ws = null;
    }

    if (pingTimer) {
      clearInterval(pingTimer);
      pingTimer = null;
    }

    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  const sendMessage = (message) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected");
      return false;
    }

    try {
      ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error("Error sending message", error);
      return false;
    }
  };

  return {
    connect,
    disconnect,
    sendMessage,
    isConnected: () => ws && ws.readyState === WebSocket.OPEN,
  };
};

export default createWebSocketService;
