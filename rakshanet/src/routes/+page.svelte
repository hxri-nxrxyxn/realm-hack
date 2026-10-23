<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Send from '@lucide/svelte/icons/send';
  import Settings2 from '@lucide/svelte/icons/settings-2';
  import RotateCcw from '@lucide/svelte/icons/rotate-ccw';
  import { Capacitor, registerPlugin } from '@capacitor/core';

  interface DirectSmsPlugin {
    sendSms(options: { number: string; message: string }): Promise<void>;
  }

  const DirectSms = registerPlugin<DirectSmsPlugin>('DirectSms');

  const defaultPlaceholder = '9995283835';
  const defaultServerUrl = 'ws://192.168.2.38:8765';

  const promptPresets = [
    { emoji: '🚨', label: 'Emergency', text: '🚨 Alert: Automated response from RakshaNet. Received your call!' },
    { emoji: '🚗', label: 'In Transit', text: '🚗 Auto-reply: Currently driving / in transit. Will call you back shortly.' },
    { emoji: '🛑', label: 'Busy', text: '🛑 Auto-reply: In an important meeting. Please text if urgent.' },
    { emoji: '🤖', label: 'AI Agent', text: '🤖 RakshaNet AI: Incoming call logged. Telephony daemon active.' }
  ];

  let phoneNumber = $state('');
  let message = $state(promptPresets[0].text);
  let statusMessage = $state<{ text: string; type: 'success' | 'error'; emoji: string } | null>(null);
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
      statusMessage = { text: 'Enter a valid target number', type: 'error', emoji: '⚠️' };
      return;
    }
    if (!messageContent) {
      statusMessage = { text: 'Response message cannot be empty', type: 'error', emoji: '⚠️' };
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
          text: isAutomated ? `Auto-dispatched SMS to ${rawNumber}` : `Dispatched SMS to ${rawNumber}`,
          type: 'success',
          emoji: '✅'
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
        statusMessage = { text: errorMsg || 'Failed to dispatch SMS', type: 'error', emoji: '❌' };
      } finally {
        isSending = false;
      }
    } else {
      try {
        window.location.href = `sms:${sanitizedNumber}?body=${encodeURIComponent(messageContent)}`;
        statusMessage = { text: `SMS intent dispatched for ${rawNumber}`, type: 'success', emoji: '💬' };
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
                text: `Call detected from ${incomingNumber}. Tap Dispatch to send.`,
                type: 'success',
                emoji: '📞'
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

  function selectPreset(presetText: string) {
    message = presetText;
    statusMessage = null;
  }

  function resetNumber() {
    phoneNumber = defaultPlaceholder;
    statusMessage = null;
  }
</script>

<div class="app-container">
  <main class="mono-card">
    <!-- Top Pill Bar -->
    <header class="top-bar">
      <div class="pill pill-status {wsConnected ? 'online' : 'offline'}">
        <span class="status-dot {wsConnected ? 'active' : 'inactive'}"></span>
        <span>{wsConnected ? `🟢 ${serverUrl.replace('ws://', '')}` : '⚪ CONNECTING...'}</span>
      </div>

      <div style="display: flex; gap: 0.35rem; align-items: center;">
        <div class="pill pill-sm pill-tag">
          <span>🤖 v2.0</span>
        </div>
        <button
          type="button"
          class="icon-pill-btn"
          onclick={() => (showSettings = !showSettings)}
          title="Server Settings"
          aria-label="Settings"
        >
          <Settings2 size={16} />
        </button>
      </div>
    </header>

    <!-- Header Title Section -->
    <div class="title-section">
      <h1 class="hero-title">
        <span>🛡️</span>
        <span>RAKSHANET</span>
      </h1>
      <p class="hero-subtitle">
        <span>⚡ Bluetooth Telephony Daemon</span>
      </p>
    </div>

    <!-- Settings Drawer (Collapsible) -->
    {#if showSettings}
      <form onsubmit={handleSaveSettings} class="settings-drawer">
        <div class="pill-carousel-label">
          <span>⚙️</span>
          <span>WEBSOCKET ENDPOINT</span>
        </div>
        <div class="settings-input-row">
          <input
            type="text"
            bind:value={serverUrl}
            placeholder="ws://192.168.2.38:8765"
            class="settings-input"
          />
          <button type="submit" class="settings-save-pill">
            <span>💾 Save</span>
          </button>
        </div>
      </form>
    {/if}

    <!-- Quick Prompt Pills Carousel -->
    <section class="pill-carousel-section">
      <div class="pill-carousel-label">
        <span>💡</span>
        <span>AI QUICK PROMPTS</span>
      </div>
      <div class="pill-chips-row">
        {#each promptPresets as preset}
          <button
            type="button"
            class="chip-btn {message === preset.text ? 'active' : ''}"
            onclick={() => selectPreset(preset.text)}
          >
            <span>{preset.emoji}</span>
            <span>{preset.label}</span>
          </button>
        {/each}
      </div>
    </section>

    <!-- Auto-Dispatch Toggle Pill -->
    <div class="toggle-pill-card">
      <div class="toggle-info">
        <span>⚡</span>
        <span>Auto-dispatch on call</span>
      </div>
      <button
        type="button"
        class="toggle-switch-btn {autoSend ? 'on' : 'off'}"
        onclick={() => (autoSend = !autoSend)}
      >
        <span>{autoSend ? 'ACTIVE 🟢' : 'MUTED ⚪'}</span>
      </button>
    </div>

    <!-- Monospace Input Form -->
    <form onsubmit={handleManualSend} class="mono-form">
      <!-- Target Number Field -->
      <div class="input-container">
        <div class="input-header-row">
          <span class="input-label">
            <span>📞</span>
            <span>TARGET RECIPIENT</span>
          </span>
          <button
            type="button"
            class="chip-btn"
            style="padding: 0.15rem 0.5rem; font-size: 0.68rem;"
            onclick={resetNumber}
            title="Reset to default number"
          >
            <RotateCcw size={11} />
            <span>DEFAULT</span>
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
          class="mono-input"
          aria-label="Target Phone Number"
        />
      </div>

      <!-- Response Prompt Field -->
      <div class="input-container">
        <div class="input-header-row">
          <span class="input-label">
            <span>💬</span>
            <span>RESPONSE PROMPT</span>
          </span>
          <span class="pill pill-sm pill-tag">
            {message.length} CHARS
          </span>
        </div>
        <textarea
          id="message-input"
          rows={3}
          bind:value={message}
          oninput={() => (statusMessage = null)}
          placeholder="Enter response message..."
          class="mono-textarea"
          aria-label="Response Message"
        ></textarea>
      </div>

      <!-- Primary White Pill Action Button -->
      <button
        type="submit"
        id="send-button"
        class="primary-pill-btn"
        disabled={isSending}
        aria-label="Dispatch SMS"
      >
        {#if isSending}
          <span class="anim-spin">⏳</span>
          <span>DISPATCHING...</span>
        {:else}
          <Send size={16} />
          <span>DISPATCH SMS NOW →</span>
        {/if}
      </button>
    </form>

    <!-- Status Toast Pill -->
    {#if statusMessage}
      <div class="status-pill-toast {statusMessage.type}" role="status">
        <span>{statusMessage.emoji}</span>
        <span>{statusMessage.text}</span>
      </div>
    {/if}

    <!-- Telemetry Footer Pills -->
    <footer class="telemetry-footer">
      <div class="pill pill-sm pill-tag">
        <span>🧠 PIPEWIRE</span>
      </div>
      <div class="pill pill-sm pill-tag">
        <span>🛡️ HFP HELVUM</span>
      </div>
      <div class="pill pill-sm pill-tag">
        <span>⏱️ 15S COOLDOWN</span>
      </div>
      <div class="pill pill-sm pill-tag">
        <span>🔒 LOCAL LINK</span>
      </div>
    </footer>
  </main>
</div>
