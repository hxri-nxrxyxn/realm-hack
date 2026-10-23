<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Capacitor, registerPlugin } from '@capacitor/core';

  interface DirectSmsPlugin {
    sendSms(options: { number: string; message: string }): Promise<void>;
  }

  const DirectSms = registerPlugin<DirectSmsPlugin>('DirectSms');

  const defaultPlaceholder = '9995283835';
  const defaultServerUrl = 'ws://192.168.2.38:8765';
  const defaultMessage = 'Alert: Automated response from RakshaNet. Received your call!';

  let phoneNumber = $state('');
  let message = $state(defaultMessage);
  let statusMessage = $state<{ text: string; type: 'success' | 'error' } | null>(null);
  let isSending = $state(false);

  let serverUrl = $state(defaultServerUrl);
  let wsConnected = $state(false);
  let autoSend = $state(true);
  let showSettings = $state(false);

  let ws: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let lastAutoSent: { number: string; time: number } | null = null;

  async function sendSmsMessage(targetNumber: string, content: string, isAutomated = false) {
    const rawNumber = targetNumber.trim() || defaultPlaceholder;
    const sanitizedNumber = rawNumber.replace(/[^0-9+*#]/g, '');
    const messageContent = content.trim();

    if (!sanitizedNumber) {
      statusMessage = { text: 'ERROR: Target recipient number is invalid.', type: 'error' };
      return;
    }
    if (!messageContent) {
      statusMessage = { text: 'ERROR: Message payload cannot be empty.', type: 'error' };
      return;
    }

    isSending = true;
    statusMessage = null;

    if (Capacitor.isNativePlatform()) {
      try {
        await DirectSms.sendSms({
          number: sanitizedNumber,
          message: messageContent,
        });

        statusMessage = {
          text: isAutomated
            ? `AUTO-DISPATCH CONFIRMED: SMS transmitted to ${rawNumber}`
            : `TRANSMISSION CONFIRMED: SMS dispatched to ${rawNumber}`,
          type: 'success'
        };

        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: 'SMS_SENT',
            number: rawNumber,
            automated: isAutomated,
            timestamp: new Date().toISOString(),
          }));
        }
      } catch (err: unknown) {
        console.error('Direct SMS error:', err);
        const errorMsg = err instanceof Error ? err.message : String(err);
        statusMessage = { text: `TRANSMISSION FAILED: ${errorMsg}`, type: 'error' };
      } finally {
        isSending = false;
      }
    } else {
      try {
        window.location.href = `sms:${sanitizedNumber}?body=${encodeURIComponent(messageContent)}`;
        statusMessage = { text: `WEB INTENT OPENED FOR ${rawNumber}`, type: 'success' };
      } catch (err) {
        console.error('Web SMS error:', err);
        window.open(`sms:${sanitizedNumber}?body=${encodeURIComponent(messageContent)}`, '_system');
      } finally {
        isSending = false;
      }
    }
  }

  function connectWebSocket() {
    if (typeof window === 'undefined') return;

    try {
      if (ws) {
        ws.close();
      }

      ws = new WebSocket(serverUrl);

      ws.onopen = () => {
        wsConnected = true;
        console.log('Connected to WebSocket server:', serverUrl);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WS Message received:', data);

          if (data.type === 'CALL_DETECTED' && data.number) {
            const incomingNumber = data.number;
            phoneNumber = incomingNumber;

            const now = Date.now();
            if (lastAutoSent && lastAutoSent.number === incomingNumber && now - lastAutoSent.time < 15000) {
              console.log('Debounced duplicate CALL_DETECTED within 15s');
              return;
            }

            lastAutoSent = { number: incomingNumber, time: now };

            if (autoSend) {
              sendSmsMessage(incomingNumber, message, true);
            } else {
              statusMessage = {
                text: `CALL DETECTED: ${incomingNumber}. Ready for manual dispatch.`,
                type: 'success'
              };
            }
          } else if (data.type === 'SERVER_READY') {
            if (data.last_number && !phoneNumber) {
              phoneNumber = data.last_number;
            }
          }
        } catch (e) {
          console.error('Failed to parse WS message:', e);
        }
      };

      ws.onclose = () => {
        wsConnected = false;
        if (reconnectTimer) clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (err) => {
        console.warn('WS Error:', err);
        ws?.close();
      };
    } catch (err) {
      console.error('WS Connection error:', err);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectWebSocket, 3000);
    }
  }

  onMount(() => {
    const savedUrl = localStorage.getItem('rakshanet_ws_url');
    if (savedUrl) {
      serverUrl = savedUrl;
    }
    connectWebSocket();
  });

  onDestroy(() => {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (ws) ws.close();
  });

  function handleManualSend(e: Event) {
    e.preventDefault();
    sendSmsMessage(phoneNumber, message, false);
  }

  function handleSaveSettings(e: Event) {
    e.preventDefault();
    localStorage.setItem('rakshanet_ws_url', serverUrl);
    showSettings = false;
    connectWebSocket();
  }

  function resetNumber() {
    phoneNumber = defaultPlaceholder;
    statusMessage = null;
  }
</script>

<div class="app-container">
  <main class="system-panel">
    <!-- Header -->
    <header class="panel-header">
      <div class="header-top">
        <div class="brand-section">
          <h1 class="brand-title">RAKSHANET</h1>
          <span class="brand-sub">TELEPHONY CONTROLLER // BLUEZ HFP</span>
        </div>
        <button
          type="button"
          class="header-action-btn"
          onclick={() => (showSettings = !showSettings)}
          aria-label="Toggle Configuration"
        >
          {showSettings ? '[CLOSE]' : '[CONFIG]'}
        </button>
      </div>

      <!-- Network Status Bar -->
      <div class="status-bar">
        <span class="status-badge {wsConnected ? 'online' : 'offline'}">
          STATUS: {wsConnected ? 'ONLINE' : 'CONNECTING'}
        </span>
        <span class="status-endpoint">
          {serverUrl.replace('ws://', '')}
        </span>
      </div>
    </header>

    <!-- Configuration Drawer -->
    {#if showSettings}
      <form onsubmit={handleSaveSettings} class="config-drawer">
        <label class="field-label" for="ws-input">WEBSOCKET ENDPOINT</label>
        <div class="config-input-group">
          <input
            id="ws-input"
            type="text"
            bind:value={serverUrl}
            placeholder="ws://192.168.2.38:8765"
            class="config-input"
          />
          <button type="submit" class="config-submit-btn">
            APPLY
          </button>
        </div>
      </form>
    {/if}

    <!-- Form Section -->
    <form onsubmit={handleManualSend} class="panel-form">
      <!-- Auto-dispatch Checkbox -->
      <label class="control-row" for="auto-toggle">
        <input
          id="auto-toggle"
          type="checkbox"
          bind:checked={autoSend}
          class="raw-checkbox"
        />
        <span class="control-label">
          AUTO-DISPATCH SMS ON INCOMING CALL
        </span>
      </label>

      <!-- Target Recipient Number -->
      <div class="field-group">
        <div class="field-meta-row">
          <label class="field-label" for="phone-input">RECIPIENT NUMBER</label>
          <button type="button" class="field-text-btn" onclick={resetNumber}>
            [RESET]
          </button>
        </div>
        <input
          id="phone-input"
          type="tel"
          inputmode="tel"
          autocomplete="tel"
          bind:value={phoneNumber}
          oninput={() => (statusMessage = null)}
          placeholder={defaultPlaceholder}
          class="tech-input"
          aria-label="Recipient Number"
        />
      </div>

      <!-- Message Payload -->
      <div class="field-group">
        <div class="field-meta-row">
          <label class="field-label" for="message-input">MESSAGE PAYLOAD</label>
          <span class="field-meta">{message.length} BYTES</span>
        </div>
        <textarea
          id="message-input"
          rows={3}
          bind:value={message}
          oninput={() => (statusMessage = null)}
          placeholder="Enter message text..."
          class="tech-textarea"
          aria-label="Message Payload"
        ></textarea>
      </div>

      <!-- Action Button -->
      <button
        type="submit"
        id="send-button"
        class="submit-btn"
        disabled={isSending}
      >
        {isSending ? 'TRANSMITTING...' : 'DISPATCH SMS'}
      </button>
    </form>

    <!-- Status Banner -->
    {#if statusMessage}
      <div class="status-banner {statusMessage.type}" role="status">
        {statusMessage.text}
      </div>
    {/if}

    <!-- Telemetry Footer -->
    <footer class="panel-footer">
      <div class="footer-line">
        <span>DAEMON: PIPEWIRE</span>
        <span>HFP: ACTIVE</span>
      </div>
      <div class="footer-line">
        <span>DEBOUNCE: 15 SECONDS</span>
        <span>LINK: LOCAL WS</span>
      </div>
    </footer>
  </main>
</div>
