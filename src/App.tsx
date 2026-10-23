import React, { useState } from 'react';
import { Phone, PhoneCall, Delete, Shield, Smartphone } from 'lucide-react';
import { Capacitor } from '@capacitor/core';

export default function App() {
  const [phoneNumber, setPhoneNumber] = useState<string>('');
  const [statusMessage, setStatusMessage] = useState<string>('');
  const defaultPlaceholder = '9995283835';

  const handleCall = (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    // Use entered number, or fallback to placeholder default
    const rawNumber = phoneNumber.trim() || defaultPlaceholder;
    // Clean string to retain digits and dialing symbols (+, #, *)
    const sanitized = rawNumber.replace(/[^0-9+*#]/g, '');

    if (!sanitized) {
      setStatusMessage('Please enter a valid phone number');
      return;
    }

    setStatusMessage(`Opening dialer for ${rawNumber}...`);

    // In Capacitor and mobile web, window.location.href with 'tel:' opens native dialer
    try {
      window.location.href = `tel:${sanitized}`;
    } catch (err) {
      console.error('Call launch error:', err);
      // Fallback
      window.open(`tel:${sanitized}`, '_system');
    }

    setTimeout(() => {
      setStatusMessage(`Call initiated: ${rawNumber}`);
    }, 1200);
  };

  const handleKeyPress = (val: string) => {
    setPhoneNumber((prev) => prev + val);
    setStatusMessage('');
  };

  const handleDelete = () => {
    setPhoneNumber((prev) => prev.slice(0, -1));
  };

  const handleClear = () => {
    setPhoneNumber('');
    setStatusMessage('');
  };

  const handleUsePlaceholder = () => {
    setPhoneNumber(defaultPlaceholder);
    setStatusMessage('');
  };

  return (
    <div className="app-container">
      <main className="dialer-card">
        {/* App Header */}
        <header className="app-header">
          <div className="logo-badge">
            <Shield className="shield-icon" size={26} />
            <PhoneCall className="phone-icon-badge" size={16} />
          </div>
          <h1 className="title">RakshaNet Dial</h1>
          <p className="subtitle">
            Running on{' '}
            <span className="platform-tag">
              <Smartphone size={13} />
              {Capacitor.getPlatform() === 'web' ? 'Web / Browser' : Capacitor.getPlatform()}
            </span>
          </p>
        </header>

        {/* Input Form */}
        <form onSubmit={handleCall} className="dialer-form">
          <div className="input-wrapper">
            <input
              id="phone-input"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              value={phoneNumber}
              onChange={(e) => {
                setPhoneNumber(e.target.value);
                setStatusMessage('');
              }}
              placeholder={defaultPlaceholder}
              className="phone-input"
              aria-label="Phone Number"
            />
            {phoneNumber && (
              <button
                type="button"
                className="clear-icon-btn"
                onClick={handleClear}
                aria-label="Clear input"
                title="Clear"
              >
                ✕
              </button>
            )}
          </div>

          {/* Quick preset hint */}
          <div className="preset-row">
            <span className="preset-label">Default: </span>
            <button
              type="button"
              className="preset-btn"
              onClick={handleUsePlaceholder}
            >
              {defaultPlaceholder}
            </button>
          </div>

          {/* Call Action Button */}
          <button
            type="submit"
            id="call-button"
            className="call-btn"
            aria-label="Call Number"
          >
            <div className="call-btn-inner">
              <div className="call-icon-circle">
                <Phone size={24} className="call-icon" />
              </div>
              <span className="call-text">
                Call {phoneNumber.trim() ? phoneNumber.trim() : defaultPlaceholder}
              </span>
            </div>
          </button>
        </form>

        {/* Keypad */}
        <div className="keypad-grid">
          {[
            { num: '1', sub: '' },
            { num: '2', sub: 'ABC' },
            { num: '3', sub: 'DEF' },
            { num: '4', sub: 'GHI' },
            { num: '5', sub: 'JKL' },
            { num: '6', sub: 'MNO' },
            { num: '7', sub: 'PQRS' },
            { num: '8', sub: 'TUV' },
            { num: '9', sub: 'WXYZ' },
            { num: '*', sub: '' },
            { num: '0', sub: '+' },
            { num: '#', sub: '' },
          ].map((item) => (
            <button
              key={item.num}
              type="button"
              className="keypad-key"
              onClick={() => handleKeyPress(item.num)}
            >
              <span className="key-num">{item.num}</span>
              {item.sub && <span className="key-sub">{item.sub}</span>}
            </button>
          ))}
        </div>

        {/* Keypad controls */}
        <div className="keypad-actions">
          <button
            type="button"
            className="action-btn backspace-btn"
            onClick={handleDelete}
            disabled={!phoneNumber}
            aria-label="Backspace"
          >
            <Delete size={20} />
            <span>Delete</span>
          </button>

          <button
            type="button"
            className="action-btn clear-all-btn"
            onClick={handleClear}
            disabled={!phoneNumber}
            aria-label="Clear all"
          >
            Clear
          </button>
        </div>

        {/* Status notification */}
        {statusMessage && (
          <div className="status-toast" role="status">
            {statusMessage}
          </div>
        )}
      </main>
    </div>
  );
}
