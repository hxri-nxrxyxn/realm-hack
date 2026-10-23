<script>
  import { registerPlugin } from '@capacitor/core';
  import { onMount } from 'svelte';

  const DefaultSms = registerPlugin('DefaultSms');

  let isDefault = $state(false);
  let statusChecked = $state(false);
  let triggerCount = $state(0);
  let lastTrigger = $state(null);
  let triggerHistory = $state([]);

  const TARGET_NUMBER = '9495364448';

  function onSmsTrigger(event) {
    console.log("[trigger] from:", event.sender, "msg:", event.message);
    triggerCount++;
    lastTrigger = {
      sender: event.sender,
      message: event.message,
      time: new Date(event.timestamp || Date.now()).toLocaleTimeString()
    };
    triggerHistory = [lastTrigger, ...triggerHistory.slice(0, 4)];
  }

  async function checkStatus() {
    try {
      const res = await DefaultSms.isDefaultSms();
      isDefault = !!res?.isDefault;
      statusChecked = true;
    } catch (e) {
      console.warn('default sms check failed', e);
    }
  }

  async function makeDefault() {
    try {
      await DefaultSms.requestDefaultSms();
      setTimeout(checkStatus, 1500);
    } catch (e) {
      console.error('request default sms error', e);
    }
  }

  let listenerHandle = null;

  onMount(async () => {
    checkStatus();
    const interval = setInterval(checkStatus, 3000);

    try {
      listenerHandle = await DefaultSms.addListener('smsReceived', (event) => {
        onSmsTrigger(event);
      });
      console.log("default sms listener attached");

      // Check if launched with initial trigger
      const last = await DefaultSms.getLastTrigger();
      if (last && last.sender) {
        onSmsTrigger(last);
      }
    } catch (e) {
      console.error("failed to add listener", e);
    }

    return () => {
      clearInterval(interval);
      if (listenerHandle && listenerHandle.remove) {
        listenerHandle.remove();
      }
    };
  });
</script>

<div class="app-container">
  <main class="system-panel">
    <!-- Header -->
    <header class="panel-header">
      <h1 class="brand-title">sampleapp</h1>
      <div class="header-right">
        <span class="status-indicator {isDefault ? 'online' : 'offline'}">
          {isDefault ? 'default' : 'not default'}
        </span>
        {#if !isDefault}
          <button type="button" class="header-action-btn" onclick={makeDefault}>
            [grant]
          </button>
        {/if}
      </div>
    </header>

    <!-- If Not Default SMS App -->
    {#if !isDefault}
      <div class="banner warning">
        <span class="banner-title">role required</span>
        <button type="button" class="submit-btn" onclick={makeDefault}>
          set as default sms app
        </button>
      </div>
    {/if}

    <!-- Filter Rule Info -->
    <div class="info-block">
      <div class="info-row">
        <span class="info-label">authorized</span>
        <span class="info-val">{TARGET_NUMBER}</span>
      </div>
      <div class="info-desc">
        only incoming sms from this number triggers auto-open and vibration
      </div>
    </div>

    <!-- Trigger Status Section -->
    <div class="trigger-section">
      <div class="section-header">
        <span class="section-title">trigger log</span>
        <span class="section-badge">[{triggerCount} triggers]</span>
      </div>

      {#if lastTrigger}
        <div class="trigger-card active">
          <div class="trigger-meta">
            <span class="meta-sender">from: {lastTrigger.sender}</span>
            <span class="meta-time">{lastTrigger.time}</span>
          </div>
          <div class="message-content">
            "{lastTrigger.message}"
          </div>
          <div class="status-tag">
            [auto-opened & vibrated]
          </div>
        </div>
      {:else}
        <div class="trigger-card standby">
          <span class="standby-dot"></span>
          <span>waiting for {TARGET_NUMBER}...</span>
        </div>
      {/if}

      <!-- History of Trigger Events -->
      {#if triggerHistory.length > 1}
        <div class="history-section">
          <span class="history-label">previous triggers</span>
          <div class="history-list">
            {#each triggerHistory.slice(1) as item}
              <div class="history-item">
                <span class="item-sender">{item.sender}</span>
                <span class="item-msg">"{item.message}"</span>
                <span class="item-time">{item.time}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  </main>
</div>

<style>
  .app-container {
    width: 100%;
    max-width: 400px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 0.5rem;
  }

  .system-panel {
    width: 100%;
    background: var(--bg-panel);
    border: 1px solid var(--border-mid);
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  /* Header Section */
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding-bottom: 0.85rem;
    border-bottom: 1px solid var(--border-dim);
  }

  .brand-title {
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0;
    color: var(--text-bright);
    margin: 0;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .status-indicator {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0;
  }

  .status-indicator.online {
    color: #ffffff;
  }

  .status-indicator.offline {
    color: var(--text-dim);
  }

  .header-action-btn {
    background: transparent;
    border: 1px solid var(--border-mid);
    color: var(--text-mid);
    font-family: inherit;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0;
    padding: 0.25rem 0.5rem;
    cursor: pointer;
    transition: all 0.1s ease;
  }

  .header-action-btn:hover,
  .header-action-btn:active {
    border-color: var(--border-active);
    color: var(--text-bright);
    background: rgba(255, 255, 255, 0.05);
  }

  /* Warning Banner */
  .banner {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 0.75rem;
    background: #000000;
    border: 1px solid var(--border-strong);
  }

  .banner-title {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-bright);
  }

  /* Primary Button - Strict: Zero Letter Spacing */
  .submit-btn {
    width: 100%;
    background: var(--btn-bg);
    color: var(--btn-text);
    border: 1px solid var(--btn-bg);
    padding: 0.8rem 1rem;
    font-family: inherit;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0 !important;
    cursor: pointer;
    transition: all 0.1s ease;
  }

  .submit-btn:hover {
    background: var(--btn-hover);
  }

  .submit-btn:active {
    background: #cccccc;
  }

  /* Filter Info Block */
  .info-block {
    background: #000000;
    border: 1px solid var(--border-mid);
    padding: 0.75rem 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .info-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.75rem;
  }

  .info-label {
    color: var(--text-mid);
    font-weight: 500;
  }

  .info-val {
    font-family: inherit;
    font-weight: 700;
    color: var(--text-bright);
    background: #111111;
    border: 1px solid var(--border-mid);
    padding: 0.2rem 0.5rem;
  }

  .info-desc {
    font-size: 0.68rem;
    color: var(--text-dim);
    line-height: 1.4;
  }

  /* Trigger Section */
  .trigger-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 0.35rem;
  }

  .section-title {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-mid);
  }

  .section-badge {
    font-size: 0.7rem;
    color: var(--text-dim);
  }

  /* Trigger Cards */
  .trigger-card {
    padding: 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }

  .trigger-card.active {
    background: #000000;
    border: 1px solid var(--border-active);
  }

  .trigger-card.standby {
    background: #000000;
    border: 1px dashed var(--border-mid);
    color: var(--text-dim);
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.72rem;
  }

  .standby-dot {
    width: 6px;
    height: 6px;
    background: var(--text-mid);
    display: inline-block;
  }

  .trigger-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.7rem;
    color: var(--text-mid);
  }

  .meta-sender {
    color: var(--text-bright);
    font-weight: 600;
  }

  .meta-time {
    color: var(--text-dim);
  }

  .message-content {
    background: #050505;
    border: 1px solid var(--border-dim);
    padding: 0.6rem 0.75rem;
    font-size: 0.78rem;
    color: var(--text-bright);
    line-height: 1.4;
    word-break: break-all;
  }

  .status-tag {
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--text-bright);
  }

  /* History Section */
  .history-section {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin-top: 0.4rem;
  }

  .history-label {
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--text-dim);
  }

  .history-list {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .history-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.45rem 0.6rem;
    background: #000000;
    border: 1px solid var(--border-dim);
    font-size: 0.68rem;
    gap: 0.5rem;
  }

  .item-sender {
    font-weight: 600;
    color: var(--text-bright);
    flex-shrink: 0;
  }

  .item-msg {
    color: var(--text-mid);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex-grow: 1;
  }

  .item-time {
    color: var(--text-dim);
    font-size: 0.65rem;
    flex-shrink: 0;
  }
</style>
