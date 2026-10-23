import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageSquare, CheckCircle2, AlertCircle, Wifi, WifiOff, Settings2 } from 'lucide-react';
import { Capacitor, registerPlugin } from '@capacitor/core';

interface DirectSmsPlugin {
  sendSms(options: { number: string; message: string }): Promise<void>;
}

const DirectSms = registerPlugin<DirectSmsPlugin>('DirectSms');

export default function App() {
  const defaultPlaceholder = '9995283835';
  const defaultServerUrl = 'ws://192.168.2.38:8765';

  const [phoneNumber, setPhoneNumber] = useState<string>('');
  const [message, setMessage] = useState<string>('🚨 Alert: Automated response from RakshaNet. Received your call!');
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [isSending, setIsSending] = useState<boolean>(false);

  // WebSocket configuration & state
  const [serverUrl, setServerUrl] = useState<string>(() => {
    return localStorage.getItem('rakshanet_ws_url') || defaultServerUrl;
  });
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [autoSend, setAutoSend] = useState<boolean>(true);
  const [showSettings, setShowSettings] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  // Function to send SMS
  const sendSmsMessage = async (targetNumber: string, content: string, isAutomated = false) => {
    const rawNumber = targetNumber.trim() || defaultPlaceholder;
    const sanitizedNumber = rawNumber.replace(/[^0-9+*#]/g, '');
    const messageContent = content.trim();

    if (!sanitizedNumber) {
      setStatusMessage({ text: 'Please enter a valid phone number', type: 'error' });
      return;
    }
    if (!messageContent) {
      setStatusMessage({ text: 'Please enter a message to send', type: 'error' });
      return;
    }

    setIsSending(true);
    setStatusMessage(null);

    if (Capacitor.isNativePlatform()) {
      try {
        await DirectSms.sendSms({
          number: sanitizedNumber,
          message: messageContent,
        });

        setStatusMessage({
          text: isAutomated
            ? `⚡ Auto-sent SMS to ${rawNumber}!`
            : `Message sent to ${rawNumber}!`,
          type: 'success',
        });

        // Notify WebSocket server of successful send
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'SMS_SENT',
            number: rawNumber,
            automated: isAutomated,
            timestamp: new Date().toISOString(),
          }));
        }
      } catch (err: unknown) {
        console.error('Direct SMS error:', err);
        const errorMsg = err instanceof Error ? err.message : String(err);
        setStatusMessage({
          text: errorMsg || 'Failed to send SMS',
          type: 'error',
        });
      } finally {
        setIsSending(false);
      }
    } else {
      // Browser fallback
      try {
        window.location.href = `sms:${sanitizedNumber}?body=${encodeURIComponent(messageContent)}`;
        setStatusMessage({
          text: `SMS link opened for ${rawNumber}`,
          type: 'success',
        });
      } catch (err) {
        console.error('Web SMS error:', err);
        window.open(`sms:${sanitizedNumber}?body=${encodeURIComponent(messageContent)}`, '_system');
      } finally {
        setIsSending(false);
      }
    }
  };

  // WebSocket connection management
  useEffect(() => {
    let isCancelled = false;

    const connectWebSocket = () => {
      if (isCancelled) return;

      try {
        const ws = new WebSocket(serverUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (isCancelled) return;
          setWsConnected(true);
          console.log('Connected to WebSocket server:', serverUrl);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WS Message received:', data);

            if (data.type === 'CALL_DETECTED' && data.number) {
              const incomingNumber = data.number;
              setPhoneNumber(incomingNumber);

              // Auto-send SMS if enabled
              if (autoSend) {
                sendSmsMessage(incomingNumber, message, true);
              } else {
                setStatusMessage({
                  text: `Call detected: ${incomingNumber}. Tap Send to dispatch.`,
                  type: 'success',
                });
              }
            } else if (data.type === 'SERVER_READY') {
              if (data.last_number && !phoneNumber) {
                setPhoneNumber(data.last_number);
              }
            }
          } catch (e) {
            console.error('Failed to parse WS message:', e);
          }
        };

        ws.onclose = () => {
          if (isCancelled) return;
          setWsConnected(false);
          // Schedule reconnect in 3s
          reconnectTimeoutRef.current = window.setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (err) => {
          console.warn('WS Error:', err);
          ws.close();
        };
      } catch (err) {
        console.error('WS Connection initiation error:', err);
        reconnectTimeoutRef.current = window.setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    return () => {
      isCancelled = true;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [serverUrl, autoSend, message]);

  const handleManualSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    sendSmsMessage(phoneNumber, message, false);
  };

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('rakshanet_ws_url', serverUrl);
    setShowSettings(false);
    if (wsRef.current) wsRef.current.close(); // trigger reconnect with new URL
  };

  return (
    <div className="app-container">
      <main className="dialer-card">
        {/* Minimal Header */}
        <header className="app-header">
          <div className="header-top-row">
            <div className="logo-badge">
              <MessageSquare size={22} />
            </div>
            <button
              type="button"
              className="icon-settings-btn"
              onClick={() => setShowSettings(!showSettings)}
              title="WebSocket Settings"
              aria-label="Settings"
            >
              <Settings2 size={18} />
            </button>
          </div>
          <h1 className="title">RakshaNet</h1>

          {/* WebSocket Connection Status Pill */}
          <div className={`ws-status-pill ${wsConnected ? 'connected' : 'disconnected'}`}>
            {wsConnected ? <Wifi size={13} /> : <WifiOff size={13} />}
            <span>{wsConnected ? `Online: ${serverUrl.replace('ws://', '')}` : 'Connecting to Server...'}</span>
          </div>
        </header>

        {/* Settings Drawer (if toggled) */}
        {showSettings && (
          <form onSubmit={handleSaveSettings} className="settings-box">
            <label className="field-label" htmlFor="server-url-input">
              Server WebSocket URL:
            </label>
            <div className="settings-input-row">
              <input
                id="server-url-input"
                type="text"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                placeholder="ws://192.168.2.38:8765"
                className="settings-input"
              />
              <button type="submit" className="settings-save-btn">
                Save
              </button>
            </div>
          </form>
        )}

        {/* Auto-Send Toggle */}
        <div className="toggle-row">
          <label className="toggle-label" htmlFor="autosend-checkbox">
            <input
              id="autosend-checkbox"
              type="checkbox"
              checked={autoSend}
              onChange={(e) => setAutoSend(e.target.checked)}
              className="toggle-checkbox"
            />
            <span className="toggle-text">⚡ Auto-send SMS on incoming call</span>
          </label>
        </div>

        {/* Minimal Form */}
        <form onSubmit={handleManualSend} className="dialer-form">
          <div className="input-group">
            <input
              id="phone-input"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              value={phoneNumber}
              onChange={(e) => {
                setPhoneNumber(e.target.value);
                setStatusMessage(null);
              }}
              placeholder={defaultPlaceholder}
              className="phone-input"
              aria-label="Phone Number"
            />
          </div>

          <div className="input-group">
            <textarea
              id="message-input"
              rows={3}
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                setStatusMessage(null);
              }}
              placeholder="Enter message..."
              className="message-textarea"
              aria-label="Message"
            />
          </div>

          {/* Send Button */}
          <button
            type="submit"
            id="send-button"
            className="call-btn"
            disabled={isSending}
            aria-label="Send Message"
          >
            <div className="call-btn-inner">
              <Send size={18} className={isSending ? 'anim-spin' : ''} />
              <span className="call-text">
                {isSending ? 'Sending...' : 'Send Message Now'}
              </span>
            </div>
          </button>
        </form>

        {/* Status Toast */}
        {statusMessage && (
          <div className={`status-toast ${statusMessage.type}`} role="status">
            {statusMessage.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{statusMessage.text}</span>
          </div>
        )}
      </main>
    </div>
  );
}
