import React, { useState } from 'react';
import { Send, MessageSquare, CheckCircle2, AlertCircle } from 'lucide-react';
import { Capacitor, registerPlugin } from '@capacitor/core';

interface DirectSmsPlugin {
  sendSms(options: { number: string; message: string }): Promise<void>;
}

const DirectSms = registerPlugin<DirectSmsPlugin>('DirectSms');

export default function App() {
  const defaultPlaceholder = '9995283835';

  const [phoneNumber, setPhoneNumber] = useState<string>('');
  const [message, setMessage] = useState<string>('Hello from RakshaNet!');
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [isSending, setIsSending] = useState<boolean>(false);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const rawNumber = phoneNumber.trim() || defaultPlaceholder;
    const sanitizedNumber = rawNumber.replace(/[^0-9+*#]/g, '');
    const messageContent = message.trim();

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
          text: `Message sent to ${rawNumber}!`,
          type: 'success',
        });
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
      // Browser fallback via sms: protocol
      try {
        window.location.href = `sms:${sanitizedNumber}?body=${encodeURIComponent(messageContent)}`;
        setStatusMessage({
          text: `SMS opened for ${rawNumber}`,
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

  return (
    <div className="app-container">
      <main className="dialer-card">
        {/* Minimal Header */}
        <header className="app-header">
          <div className="logo-badge">
            <MessageSquare size={24} />
          </div>
          <h1 className="title">RakshaNet</h1>
        </header>

        {/* Minimal Form */}
        <form onSubmit={handleSendMessage} className="dialer-form">
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
                {isSending ? 'Sending...' : 'Send Message'}
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
