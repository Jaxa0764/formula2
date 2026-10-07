export class RealtimeManager {
  constructor(onMessage) {
    this.onMessage = onMessage;
    this.socket = null;
    this.reconnectTimeout = 3000;
    this.init();
  }

  init() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    // When run via Vite proxy or direct port
    const wsUrl = `${protocol}//${host}/api/websocket`;

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('⚡ Connected to SmartFuel real-time WebSocket feed.');
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (this.onMessage) {
            this.onMessage(data);
          }
        } catch (e) {
          console.warn('Invalid JSON from WebSocket:', event.data);
        }
      };

      this.socket.onclose = () => {
        console.log('WebSocket disconnected. Retrying in 3s...');
        setTimeout(() => this.init(), this.reconnectTimeout);
      };

      this.socket.onerror = (err) => {
        console.warn('WebSocket encountered error:', err);
        this.socket.close();
      };
    } catch (e) {
      console.error('Failed to initialize WebSocket:', e);
      setTimeout(() => this.init(), this.reconnectTimeout);
    }
  }

  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }
}
