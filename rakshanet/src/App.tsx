import React, { useState } from 'react';
import { Send, MessageSquare, Shield, Smartphone, CheckCircle2, AlertCircle } from 'lucide-react';
import { Capacitor, registerPlugin } from '@capacitor/core';

interface DirectSmsPlugin {
  sendSms(options: { number: string; message: string }): Promise<void>;
}

const DirectSms = registerPlugin<DirectSmsPlugin>('DirectSms');

interface SentMessageItem {
  id: string;
  recipient: string;
  text: string;
  time: string;
}

export default function App() {
  const defaultPlaceholder = '9995283835';
  const defaultMessage = '🚨 Alert: Need immediate assistance from RakshaNet!';

  const [phoneNumber, setPhoneNumber] = useState<string>('');
  const [message, setMessage] = useState<string>(defaultMessage);
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [sentHistory, setSentHistory] = useState<SentMessageItem[]>([]);

  const quickTemplates = [
    '🚨 Alert: Need immediate assistance!',
    '📍 Sharing status: Please contact me urgently.',
    '✅ Update: I have reached safely.',
    '📞 Please call me back as soon as possible.',
  ];

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const rawNumber = phoneNumber.trim() || defaultPlaceholder;
    const sanitizedNumber = rawNumber.replace(/[^0-9+*#]/g, '');
    const messageContent = message.trim() || defaultMessage;

    if (!sanitizedNumber) {
      setStatusMessage({ text: 'Please enter a valid phone number', type: 'error' });
      return;
    }

    if (!messageContent) {
      setStatusMessage({ text: 'Please enter a message to send', type: 'error' });
      return;
    }

    setIsSending(true);
    setStatusMessage({ text: `Sending SMS to ${rawNumber}...`, type: 'info' });

    if (Capacitor.isNativePlatform()) {
      try {
        await DirectSms.sendSms({
          number: sanitizedNumber,
          message: messageContent,
        });

        setStatusMessage({
          text: `Message sent seamlessly to ${rawNumber}!`,
          type: 'success',
        });

        const newEntry: SentMessageItem = {
          id: Date.now().toString(),
          recipient: rawNumber,
          text: messageContent,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setSentHistory((prev) => [newEntry, ...prev.slice(0, 4)]);
      } catch (err: unknown) {
        console.error('Direct SMS error:', err);
        const errorMsg = err instanceof Error ? err.message : String(err);
        setStatusMessage({
          text: errorMsg || 'Failed to send SMS. Ensure SMS permission is granted.',
          type: 'error',
        });
      } finally {
        setIsSending(false);
      }
    } else {
      // Browser fallback via sms: protocol
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

  const handleClearNumber = () => {
    setPhoneNumber('');
    setStatusMessage(null);
  };

  const handleUsePlaceholder = () => {
    setPhoneNumber(defaultPlaceholder);
    setStatusMessage(null);
  };

  const targetNumberDisplay = phoneNumber.trim() || defaultPlaceholder;

  return (
    <div className="app-container">
      <main className="dialer-card">
        {/* App Header */}
        <header className="app-header">
          <div className="logo-badge">
            <Shield className="shield-icon" size={26} />
            <MessageSquare className="phone-icon-badge" size={16} />
          </div>
          <h1 className="title">RakshaNet Messenger</h1>
          <p className="subtitle">
            Running on{' '}
            <span className="platform-tag">
              <Smartphone size={13} />
              {Capacitor.getPlatform() === 'web' ? 'Web / Browser' : Capacitor.getPlatform()}
            </span>
          </p>
        </header>

        {/* Messaging Form */}
        <form onSubmit={handleSendMessage} className="dialer-form">
          {/* Recipient Input Box */}
          <div className="form-group">
            <label className="field-label" htmlFor="phone-input">
              Recipient Phone Number
            </label>
            <div className="input-wrapper">
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
              {phoneNumber && (
                <button
                  type="button"
                  className="clear-icon-btn"
                  onClick={handleClearNumber}
                  aria-label="Clear number"
                  title="Clear"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Quick preset hint */}
            <div className="preset-row">
              <span className="preset-label">Placeholder default: </span>
              <button
                type="button"
                className="preset-btn"
                onClick={handleUsePlaceholder}
              >
                {defaultPlaceholder}
              </button>
            </div>
          </div>

          {/* Message Text Input */}
          <div className="form-group">
            <div className="label-with-clear">
              <label className="field-label" htmlFor="message-input">
                Message Content
              </label>
              {message && (
                <button
                  type="button"
                  className="preset-btn text-xs"
                  onClick={() => setMessage('')}
                >
                  Clear text
                </button>
              )}
            </div>
            <textarea
              id="message-input"
              rows={3}
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                setStatusMessage(null);
              }}
              placeholder="Type your message here..."
              className="message-textarea"
            />
          </div>

          {/* Quick Message Templates */}
          <div className="templates-section">
            <span className="templates-label">Quick Templates:</span>
            <div className="templates-grid">
              {quickTemplates.map((template, idx) => (
                <button
                  key={idx}
                  type="button"
                  className={`template-chip ${message === template ? 'active' : ''}`}
                  onClick={() => {
                    setMessage(template);
                    setStatusMessage(null);
                  }}
                >
                  {template}
                </button>
              ))}
            </div>
          </div>

          {/* Send SMS Action Button */}
          <button
            type="submit"
            id="send-button"
            className="call-btn send-btn"
            disabled={isSending}
            aria-label="Send SMS"
          >
            <div className="call-btn-inner">
              <div className="call-icon-circle">
                <Send size={20} className={isSending ? 'anim-spin' : ''} />
              </div>
              <span className="call-text">
                {isSending ? 'Sending Seamlessly...' : `Send Message to ${targetNumberDisplay}`}
              </span>
            </div>
          </button>
        </form>

        {/* Status notification */}
        {statusMessage && (
          <div className={`status-toast ${statusMessage.type}`} role="status">
            {statusMessage.type === 'success' && <CheckCircle2 size={16} />}
            {statusMessage.type === 'error' && <AlertCircle size={16} />}
            <span>{statusMessage.text}</span>
          </div>
        )}

        {/* Sent History */}
        {sentHistory.length > 0 && (
          <div className="history-section">
            <h2 className="history-title">Recently Sent</h2>
            <div className="history-list">
              {sentHistory.map((item) => (
                <div key={item.id} className="history-card">
                  <div className="history-header">
                    <span className="history-recipient">To: {item.recipient}</span>
                    <span className="history-time">{item.time}</span>
                  </div>
                  <p className="history-text">{item.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
