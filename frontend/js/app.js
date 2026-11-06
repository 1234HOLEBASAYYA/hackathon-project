/**
 * MEDVISION-AI Core Application Script
 * Global UI orchestration, alerts, and system health polling
 */

const App = {
  showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';

    toast.innerHTML = `
      <span>${icon}</span>
      <div style="flex:1;">${message}</div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4500);
  },

  async checkSystemHealth() {
    try {
      const data = await window.API.getHealth();
      const dot = document.querySelector('.status-dot');
      const text = document.querySelector('.system-status-text');
      
      if (data.status === 'healthy') {
        if (dot) dot.style.background = 'var(--emerald-primary)';
        if (text) text.textContent = 'All Services Online';
      } else {
        if (dot) dot.style.background = 'var(--amber-primary)';
        if (text) text.textContent = 'Degraded';
      }
    } catch (e) {
      const dot = document.querySelector('.status-dot');
      const text = document.querySelector('.system-status-text');
      if (dot) dot.style.background = 'var(--rose-primary)';
      if (text) text.textContent = 'Gateway Offline';
    }
  },

  openPatientModal() {
    let modal = document.getElementById('patientModal');
    if (modal) modal.style.display = 'flex';
  },

  closePatientModal() {
    let modal = document.getElementById('patientModal');
    if (modal) modal.style.display = 'none';
  }
};

window.App = App;

document.addEventListener('DOMContentLoaded', () => {
  App.checkSystemHealth();
  setInterval(() => App.checkSystemHealth(), 15000);
});

