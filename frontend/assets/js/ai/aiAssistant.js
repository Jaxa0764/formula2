import { ApiClient } from '../api/client.js';
import { getLang, t } from '../i18n/translations.js';

export class AIAssistant {
  constructor(options = {}) {
    this.container = null;
    this.isOpen = false;
    this.history = [];
    this.onAction = options.onAction || (() => {});
    this.getUserLocation = options.getUserLocation || (() => ({ lat: 41.311081, lng: 69.240562 }));
    this.init();
  }

  init() {
    this.createWidget();
    this.attachEvents();
  }

  createWidget() {
    const html = `
      <div id="ai-assistant-widget" class="ai-widget">
        <!-- Floating Glow Trigger Button -->
        <button id="ai-trigger-btn" class="ai-trigger" aria-label="AI Yordamchi">
          <div class="ai-trigger-halo"></div>
          <div class="ai-trigger-inner">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a10 10 0 0 1 10 10c0 4.42-2.87 8.17-6.84 9.5-.5.08-.66-.23-.66-.5v-1.9c0-1.7-1.3-3.1-3-3.1s-3 1.4-3 3.1v1.9c0 .27-.16.58-.66.5A10 10 0 0 1 2 12 10 10 0 0 1 12 2z"/>
              <path d="m9 9 1 2 2 1-2 1-1 2-1-2-2-1 2-1 1-2z"/>
            </svg>
            <span class="ai-trigger-badge">AI</span>
          </div>
        </button>

        <!-- Floating Chat Window -->
        <div id="ai-chat-window" class="ai-chat-card hidden">
          <div class="ai-chat-header">
            <div class="ai-header-info">
              <div class="ai-avatar">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
              </div>
              <div>
                <h3 class="ai-header-title">${t('ai_title')}</h3>
                <span class="ai-header-status">● Real-vaqt ma'lumotlar bazasi</span>
              </div>
            </div>
            <button id="ai-close-btn" class="ai-btn-close" aria-label="Yopish">✕</button>
          </div>

          <!-- Messages stream -->
          <div id="ai-messages-list" class="ai-messages-container">
            <div class="ai-message ai-message-system">
              <div class="ai-msg-bubble">
                Assalomu alaykum! Men <b>SmartFuel UZ</b> sun'iy intellekt yordamchisiman. Sizga O'zbekistondagi eng arzon yoqilg'i, yaqin metan (CNG) bosimi yoki bo'sh EV zaryadlash stansiyasini topishda yordam beraman.
              </div>
            </div>
          </div>

          <!-- Suggested Query Chips -->
          <div class="ai-chips-container" id="ai-chips-list">
            <button class="ai-chip" data-prompt="Eng arzon AI-92 qayerda?">⛽ Eng arzon AI-92</button>
            <button class="ai-chip" data-prompt="Eng yaqin yuqori bosimli metan zapravka">🟢 Yaqin metan (CNG)</button>
            <button class="ai-chip" data-prompt="Bo'sh EV zaryadkalar bormi?">⚡ Tezkor EV stansiya</button>
            <button class="ai-chip" data-prompt="Yaqin 3 ta zapravkani taqqosla">📊 Zapravkalarni taqqosla</button>
            <button class="ai-chip" data-prompt="Navbatsiz zapravkalar">🚗 Kam navbatli zapravka</button>
          </div>

          <!-- Chat Input -->
          <form id="ai-chat-form" class="ai-input-form">
            <input 
              type="text" 
              id="ai-user-input" 
              placeholder="${t('ai_placeholder')}" 
              autocomplete="off"
            />
            <button type="submit" id="ai-send-btn" aria-label="Yuborish">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </form>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', html);
    this.container = document.getElementById('ai-assistant-widget');
  }

  attachEvents() {
    const triggerBtn = document.getElementById('ai-trigger-btn');
    const closeBtn = document.getElementById('ai-close-btn');
    const chatWindow = document.getElementById('ai-chat-window');
    const form = document.getElementById('ai-chat-form');
    const input = document.getElementById('ai-user-input');
    const chips = document.getElementById('ai-chips-list');

    triggerBtn.addEventListener('click', () => {
      this.isOpen = !this.isOpen;
      chatWindow.classList.toggle('hidden', !this.isOpen);
      if (this.isOpen) {
        input.focus();
      }
    });

    closeBtn.addEventListener('click', () => {
      this.isOpen = false;
      chatWindow.classList.add('hidden');
    });

    chips.addEventListener('click', (e) => {
      const chip = e.target.closest('.ai-chip');
      if (chip) {
        const prompt = chip.getAttribute('data-prompt');
        input.value = prompt;
        this.handleSendMessage(prompt);
      }
    });

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      this.handleSendMessage(text);
      input.value = '';
    });
  }

  async handleSendMessage(text) {
    this.appendMessage('user', text);
    this.showTypingIndicator();

    const loc = this.getUserLocation();
    const lang = getLang();

    try {
      const res = await ApiClient.askAI(text, loc.lat, loc.lng, this.history, lang);
      this.removeTypingIndicator();

      this.appendMessage('assistant', res.answer, res.actions, res.stations);
      this.history.push({ role: 'user', content: text });
      this.history.push({ role: 'assistant', content: res.answer });
    } catch (err) {
      this.removeTypingIndicator();
      this.appendMessage('system', "Kechirasiz, ma'lumot olishda xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.");
    }
  }

  appendMessage(role, text, actions = [], stations = []) {
    const list = document.getElementById('ai-messages-list');
    const msgDiv = document.createElement('div');
    msgDiv.className = `ai-message ai-message-${role}`;

    // Convert newlines to breaks and bold markers
    const formattedText = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>');

    let actionsHtml = '';
    if (actions && actions.length > 0) {
      actionsHtml = `
        <div class="ai-msg-actions">
          ${actions.map(act => `
            <button class="ai-action-btn" data-type="${act.type}" data-station-id="${act.station_id || ''}">
              ${act.title}
            </button>
          `).join('')}
        </div>
      `;
    }

    msgDiv.innerHTML = `
      <div class="ai-msg-bubble">
        <div class="ai-msg-text">${formattedText}</div>
        ${actionsHtml}
      </div>
    `;

    // Attach click events on action buttons
    const btns = msgDiv.querySelectorAll('.ai-action-btn');
    btns.forEach(btn => {
      btn.addEventListener('click', () => {
        const type = btn.getAttribute('data-type');
        const stId = parseInt(btn.getAttribute('data-station-id'));
        this.onAction(type, stId);
      });
    });

    list.appendChild(msgDiv);
    list.scrollTop = list.scrollHeight;
  }

  showTypingIndicator() {
    const list = document.getElementById('ai-messages-list');
    const typing = document.createElement('div');
    typing.id = 'ai-typing-indicator';
    typing.className = 'ai-message ai-message-assistant';
    typing.innerHTML = `
      <div class="ai-msg-bubble ai-typing-bubble">
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      </div>
    `;
    list.appendChild(typing);
    list.scrollTop = list.scrollHeight;
  }

  removeTypingIndicator() {
    const typing = document.getElementById('ai-typing-indicator');
    if (typing) typing.remove();
  }
}
