<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Send, MessageSquare, CheckCircle2, AlertCircle, Wifi, WifiOff, Settings2 } from '@lucide/svelte';
  import { Capacitor, registerPlugin } from '@capacitor/core';

  interface DirectSmsPlugin {
    sendSms(options: { number: string; message: string }): Promise<void>;
  }

  const DirectSms = registerPlugin<DirectSmsPlugin>('DirectSms');

  const defaultPlaceholder = '9995283835';
  const defaultServerUrl = 'ws://192.168.2.38:8765';

  let phoneNumber = $state('');
  let message = $state('🚨 Alert: Automated response from RakshaNet. Received your call!');
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
      statusMessage = { text: 'Please enter a valid phone number', type: 'error' };
      return;
    }
    if (!messageContent) {
      statusMessage = { text: 'Please enter a message to send', type: 'error' };
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
          text: isAutomated ? `⚡ Auto-sent SMS to ${rawNumber}!` : `Message sent to ${rawNumber}!`,
          type: 'success',
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
        statusMessage = { text: errorMsg || 'Failed to send SMS', type: 'error' };
      } finally {
        isSending = false;
      }
    } else {
      try {
        window.location.href = `sms:${sanitizedNumber}?body=${encodeURIComponent(messageContent)}`;
        statusMessage = { text: `SMS link opened for ${rawNumber}`, type: 'success' };
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
              console.log('Debounced: Ignoring duplicate CALL_DETECTED within 15s');
              return;
            }

            lastAutoSent = { number: incomingNumber, time: now };

            if (autoSend) {
              sendSmsMessage(incomingNumber, message, true);
            } else {
              statusMessage = {
                text: `Call detected: ${incomingNumber}. Tap Send to dispatch.`,
                type: 'success',
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
</script>

<div class="app-container">
  <main class="dialer-card">
    <!-- Minimal Header -->
    <header class="app-header">
      <div class="header-top-row">
        <div class="logo-badge">
          <MessageSquare size={22} />
        </div>
        <button
          type="button"
          class="icon-settings-btn"
          onclick={() => (showSettings = !showSettings)}
          title="WebSocket Settings"
          aria-label="Settings"
        >
          <Settings2 size={18} />
        </button>
      </div>
      <h1 class="title">RakshaNet</h1>

      <!-- WebSocket Connection Status Pill -->
      <div class="ws-status-pill {wsConnected ? 'connected' : 'disconnected'}">
        {#if wsConnected}
          <Wifi size={13} />
          <span>Online: {serverUrl.replace('ws://', '')}</span>
        {:else}
          <WifiOff size={13} />
          <span>Connecting to Server...</span>
        {/if}
      </div>
    </header>

    <!-- Settings Drawer (if toggled) -->
    {#if showSettings}
      <form onsubmit={handleSaveSettings} class="settings-box">
        <label class="field-label" for="server-url-input">
          Server WebSocket URL:
        </label>
        <div class="settings-input-row">
          <input
            id="server-url-input"
            type="text"
            bind:value={serverUrl}
            placeholder="ws://192.168.2.38:8765"
            class="settings-input"
          />
          <button type="submit" class="settings-save-btn">
            Save
          </button>
        </div>
      </form>
    {/if}

    <!-- Auto-Send Toggle -->
    <div class="toggle-row">
      <label class="toggle-label" for="autosend-checkbox">
        <input
          id="autosend-checkbox"
          type="checkbox"
          bind:checked={autoSend}
          class="toggle-checkbox"
        />
        <span class="toggle-text">⚡ Auto-send SMS on incoming call</span>
      </label>
    </div>

    <!-- Minimal Form -->
    <form onsubmit={handleManualSend} class="dialer-form">
      <div class="input-group">
        <input
          id="phone-input"
          type="tel"
          inputmode="tel"
          autocomplete="tel"
          bind:value={phoneNumber}
          oninput={() => (statusMessage = null)}
          placeholder={defaultPlaceholder}
          class="phone-input"
          aria-label="Phone Number"
        />
      </div>

      <div class="input-group">
        <textarea
          id="message-input"
          rows={3}
          bind:value={message}
          oninput={() => (statusMessage = null)}
          placeholder="Enter message..."
          class="message-textarea"
          aria-label="Message"
        ></textarea>
      </div>

      <!-- Send Button -->
      <button
        type="submit"
        id="send-button"
        class="call-btn"
        disabled={isSending}
        aria-label="Send Message"
      >
        <div class="call-btn-inner">
          <Send size={18} class={isSending ? 'anim-spin' : ''} />
          <span class="call-text">
            {isSending ? 'Sending...' : 'Send Message Now'}
          </span>
        </div>
      </button>
    </form>

    <!-- Status Toast -->
    {#if statusMessage}
      <div class="status-toast {statusMessage.type}" role="status">
        {#if statusMessage.type === 'success'}
          <CheckCircle2 size={16} />
        {:else}
          <AlertCircle size={16} />
        {/if}
        <span>{statusMessage.text}</span>
      </div>
    {/if}
  </main>
</div>
