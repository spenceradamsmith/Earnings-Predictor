const customLogos = window.customLogos || {};
const searchStocks = window.searchStocks || {};

function getLogoSrc(ticker, fallbackLogo) {
  return customLogos[ticker] || fallbackLogo;
}

// Add fade effect to categories navigation
const nav = document.querySelector('.categories-nav');
const wrapper = document.querySelector('.categories-wrapper');
function updateFade() {
  const atStart = nav.scrollLeft === 0;
  const atEnd = nav.scrollLeft + nav.clientWidth >= nav.scrollWidth;
  wrapper.classList.toggle('scrolled', !atStart);
  wrapper.classList.toggle('at-start', atStart);
  wrapper.classList.toggle('at-end', atEnd);
}
// whenever nav moves, update the wrapper’s classes
nav.addEventListener('scroll', updateFade);
updateFade();

const top20Tickers = [
  'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
  'NVDA', 'BRK.B', 'META', 'UNH', 'V',
  'JPM', 'JNJ', 'MA', 'PG', 'HD',
  'ADBE', 'PYPL', 'XOM', 'KO', 'PFE'
];

const categoryTickers = {
  'All': top20Tickers,
  'Technology': [
    'AAPL', 'MSFT', 'GOOGL', 'ORCL', 'IBM',
    'INTC', 'CSCO', 'NVDA', 'AMD', 'ADBE',
    'SAP', 'CRM', 'TXN', 'QCOM', 'AVGO',
    'AMAT', 'MU', 'NOW', 'SNPS', 'TEAM'
  ],
  'Healthcare': [
    'JNJ', 'PFE', 'UNH', 'MRK', 'ABBV',
    'LLY', 'ABT', 'TMO', 'AMGN', 'CVS',
    'GILD', 'BMY', 'ZTS', 'DHR', 'MDT',
    'SYK', 'BDX', 'IQV', 'BSX', 'ILMN'
  ],
  'Financials': [
    'BRK.B', 'JPM', 'BAC', 'WFC', 'C',
    'GS', 'MS', 'AXP', 'USB', 'PNC',
    'TFC', 'BK', 'SCHW', 'BLK', 'PRU',
    'MET', 'AIG', 'MMC', 'ALL', 'CME'
  ],
  'Consumer Discretionary': [
    'AMZN', 'TSLA', 'HD', 'MCD', 'NKE',
    'SBUX', 'LOW', 'CMG', 'MAR', 'BKNG',
    'TJX', 'ULTA', 'ROST', 'DRI', 'DIS',
    'WHR', 'YUM', 'GM', 'F', 'LEG'
  ],
  'Consumer Staples': [
    'PG', 'KO', 'PEP', 'WMT', 'COST',
    'MO', 'PM', 'CL', 'KMB', 'STZ',
    'GIS', 'MDLZ', 'MKC', 'HSY', 'KR',
    'DG', 'EL', 'SYY', 'MNST', 'KDP'
  ],
  'Energy': [
    'XOM', 'CVX', 'COP', 'SLB', 'PSX',
    'VLO', 'HES', 'EOG', 'PXD', 'OXY',
    'DVN', 'APA', 'MRO', 'MUR', 'EQT',
    'FTI', 'HAL', 'KMI', 'OKE', 'ENB'
  ],
  'Industrials': [
    'BA', 'HON', 'UPS', 'CAT', 'GE',
    'LMT', 'DE', 'MMM', 'RTX', 'EMR',
    'PCAR', 'CMI', 'UNP', 'FDX', 'ROK',
    'NSC', 'CSX', 'NOC', 'TXT', 'DOV'
  ],
  'Materials': [
    'LIN', 'APD', 'ECL', 'SHW', 'FCX',
    'DD', 'OLN', 'NEM', 'VMC', 'PPG',
    'STLD', 'CLF', 'NUE', 'BLL', 'SEE',
    'IFF', 'MOS', 'PKG', 'MLM', 'CF'
  ],
  'Utilities': [
    'NEE', 'DUK', 'SO', 'AEP', 'EXC',
    'SRE', 'XEL', 'ED', 'D', 'WEC',
    'NRG', 'AES', 'PPL', 'PCG', 'EIX',
    'PEG', 'FE', 'ES', 'ATO', 'OGE'
  ],
  'Real Estate': [
    'AMT', 'PLD', 'SPG', 'PSA', 'WPC',
    'CBRE', 'AVB', 'EQR', 'HST', 'ESS',
    'VTR', 'O', 'UDR', 'DLR', 'EQIX',
    'KIM', 'IRM', 'FRT', 'REG', 'SLG'
  ],
  'Communication Services': [
    'GOOGL', 'META', 'NFLX', 'DIS', 'CMCSA',
    'T', 'VZ', 'ABNB', 'EA', 'TTWO',
    'CHTR', 'PARA', 'DISH', 'SPOT', 'ROKU',
    'PINS', 'SNAP', 'WBD', 'OMC', 'MTCH'
  ]
};

document.addEventListener('DOMContentLoaded', () => {
  console.log('▶ DOM fully loaded');
  const nav = document.querySelector('.categories-nav');
  const cardsGrid = document.querySelector('.cards-grid');
  const now = Date.now();
  const MS_PER_DAY = 1000 * 60 * 60 * 24;

  // Fetch & render cards for a category
  async function fetchAndDisplay(category) {
    console.log(`→ Fetching category: ${category}`);
    const tickers = categoryTickers[category] || [];
    if (!tickers.length) {
      cardsGrid.innerHTML = `<div class="card"><div class="card-content">No tickers found for “${category}.”</div></div>`;
      return;
    }

    // parallel-fetch all tickers
    const responses = await Promise.all(tickers.map(async ticker => {
      try {
        const res  = await fetch(`https://earnings-predictor.onrender.com/predict?ticker=${encodeURIComponent(ticker)}`);
        if (!res.ok) throw new Error(res.status);
        const json = await res.json();

        // parse name and date
        const rawName = json.company_name || '';
        const name1 = rawName.replace(/\s*\(The\)$/, '');
        const name2 = name1.replace(/\s*\(T$/, '');
        const name3 = name2.replace(/\s*Packaging Corporation of Americ$/, 'Packaging Corporation of America');
        const name4 = name3.replace(/,\s*Inc(?!\.)\b/, ', Inc.');
        const name5 = name4.replace(/\s* \(Holdi$/, '');
        const name6 = name5.replace(/\s* \(D\/B\/A\)$/, '');
        const name7 = name6.replace(/\s* \(Holdin$/, '');
        const name8 = name7.replace(/\bDBA\b\s*/gi, '');
        const name9 = name8.replace(/\s*(?:\(?REIT\)?\s*)$/i, '');
        const name10 = name9.replace(/\s* \(REI$/, '');
        const name11 = name10.replace(/\s* \(Del$/, '');
        const name12 = name11.replace(/\s* \(HC\)$/, '');
        const name13 = name12.replace(/\s* S.A.$/, '');
        const name14 = name13.replace(/,\s*$/, '');
        const name = name14.replace(/-\s*$/, '');

        let date = null;
        if (json.earnings_date) {
          const d = new Date(json.earnings_date);
          date = isNaN(d.getTime()) ? null : d;
        } else if (json.days_until != null && !isNaN(json.days_until)) {
          date = new Date(now + json.days_until * MS_PER_DAY);
        }

        let expectedEps = null;
        if (json.expected_eps != null) {
          const epsNum = Number(json.expected_eps);
          expectedEps = isNaN(epsNum) ? null : epsNum;
        }

        // compute days until for countdown
        let daysUntil = null;
        if (json.days_until != null && !isNaN(json.days_until)) {
          daysUntil = json.days_until;
        } else if (date) {
          daysUntil = Math.ceil((date - now) / MS_PER_DAY);
        }

        return {
          ticker: ticker,
          name: name,
          logo: json.logo,
          date,
          expected_eps: expectedEps,
          days_until: daysUntil,
          raw_beat_pct: json.raw_beat_pct
        };
      } catch (err) {
        console.warn(`✖️ ${ticker} failed:`, err);
        return { ticker, name: ticker, logo: null, date: null, expected_eps: null, days_until: null, raw_beat_pct: null };
      }
    }));

    // filter out nulls, sort by proximity
    const items = responses
      .filter(x => x)
      .sort((a, b) => {
        const aDist = a.date ? Math.abs(a.date - now) : Infinity;
        const bDist = b.date ? Math.abs(b.date - now) : Infinity;
        return aDist - bDist;
      });

    // clear out old cards
    cardsGrid.innerHTML = '';

    // render
    items.forEach(item => {
      const fmtDate = item.date
        ? item.date.toLocaleDateString()
        : 'TBD';
      const fmtESP = item.expected_eps != null
        ? item.expected_eps.toFixed(2)
        : 'TBD';
      const fmtDays = item.days_until != null
        ? item.days_until
        : '–';
      const card = document.createElement('div');
      // choose mode based on presence of raw_beat_pct
      if (typeof item.raw_beat_pct === 'number') {
        card.classList.add('card', 'mode-prediction');
        const pct = item.raw_beat_pct;

        card.innerHTML = `
          <div class="card-content">
            <div class="header-row">
              <div class="logo">
          <img src="${getLogoSrc(item.ticker, item.logo)}" alt="${item.name} logo"/>
              </div>
              <div class="header">
          <h2 class="company">${item.name}</h2>
          <span class="ticker">${item.ticker}</span>
              </div>
            </div>
            <div class="details">
              <div class="info">
          <span class="label">Next Earnings:</span>
          <span class="value">${fmtDate}</span>
              </div>
              <div class="info">
          <span class="label">Expected EPS:</span>
          <span class="value">${fmtESP}</span>
              </div>
            </div>
            <div class="visual prediction">
              <svg class="gauge" viewBox="0 0 100 50">
          <path class="bg"
                d="M10,50 A40,40 0 0,1 90,50"
                fill="none"/>
          <path class="fg"
                d="M10,50 A40,40 0 0,1 90,50"
                fill="none"/>
              </svg>
              <div class="percent">${(item.raw_beat_pct).toFixed(1)}%</div>
            </div>
          </div>
        `;
        cardsGrid.appendChild(card);
        const fg = card.querySelector('.gauge .fg');
        const length = fg.getTotalLength();
        fg.style.strokeDasharray = length;
        const pctValue = item.raw_beat_pct;
        const pctFraction = pctValue / 100;
        fg.style.strokeDashoffset = length * (1 - pctFraction);
        fg.classList.toggle('red', pctValue < 50);
        fg.classList.toggle('green', pctValue >= 50);
      } else {
        card.classList.add('card', 'mode-countdown');
        card.innerHTML = `
          <div class="card-content">
            <div class="header-row">
              <div class="logo">
                <img src="${getLogoSrc(item.ticker, item.logo)}" alt="${item.name} logo"/>
              </div>
              <div class="header">
                <h2 class="company">${item.name}</h2>
                <span class="ticker">${item.ticker}</span>
              </div>
            </div>
            <div class="details">
              <div class="info">
                <span class="label">Next Earnings:</span>
                <span class="value">${fmtDate}</span>
              </div>
              <div class="info">
                <span class="label">Expected EPS:</span>
                <span class="value">${fmtESP}</span>
              </div>
            </div>
            <div class="visual countdown">
              <div class="count">${fmtDays}</div>
              <div class="days">days</div>
              <div class="unit">until prediction</div>
            </div>
          </div>
        `;
        cardsGrid.appendChild(card);
      }
    });
  }

  // Category buttons
  nav.addEventListener('click', e => {
    if (e.target.tagName !== 'BUTTON') return;
    nav.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
    e.target.classList.add('selected');
    fetchAndDisplay(e.target.textContent);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // Auto-click “All” on load
  const initial = nav.querySelector('button.selected') || nav.querySelector('button');
  if (initial) initial.click();

  const header = document.querySelector('.header-top h1');
  const allButton = document.getElementById('all-button');
  if (header && allButton) {
    header.addEventListener('click', () => {
      allButton.click();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // Search functionality
  const searchInput   = document.querySelector('.search-box input');
  const searchResults = document.querySelector('.search-results');
  const stocks        = window.searchStocks || [];

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();

    if (!q) {
      searchResults.innerHTML = '';
      return;
    }

    const matches = stocks.filter(s =>
      s.ticker.toLowerCase().includes(q) ||
      s.name.toLowerCase().includes(q)
    );

    searchResults.innerHTML = matches.map(item => `
      <div class="search-item" data-ticker="${item.ticker}">
        <strong>${item.ticker}</strong> – ${item.name}
      </div>
    `).join('');

    // attach click handlers
    searchResults.querySelectorAll('.search-item').forEach(el => {
      el.addEventListener('click', () => {
        const ticker = el.dataset.ticker;
        console.log('Clicked', ticker);
        searchResults.innerHTML = '';
        searchInput.value = ticker;
      });
    });
  });

  const searchContainer = document.querySelector('.search-container');
  document.addEventListener('click', (event) => {
    if (!searchContainer.contains(event.target)) {
      searchResults.innerHTML = '';
      searchResults.style.display = 'none';
    }
  });
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    if (!q) {
      searchResults.innerHTML = '';
      searchResults.style.display = 'none';
      return;
    }

    const matches = stocks.filter(s =>
      s.ticker.toLowerCase().includes(q) ||
      s.name.toLowerCase().includes(q)
    );

    searchResults.innerHTML = matches.map(item => `
      <div class="search-item" data-ticker="${item.ticker}">
        <div class="item-ticker"><strong>${item.ticker}</strong></div>
        <div class="item-name">${item.name}</div>
      </div>
    `).join('');

    // re-attach click handlers to the new items
    searchResults.querySelectorAll('.search-item').forEach(el => {
      el.addEventListener('click', () => {
        searchInput.value = el.dataset.ticker;
        searchResults.innerHTML = '';
        searchResults.style.display = 'none';
      });
    });

    // show the box if there are results, hide if empty
    searchResults.style.display = matches.length ? 'block' : 'none';
  });

  // when you click or tab back into the input, rerun the filter
  searchInput.addEventListener('focus', () => {
    if (searchInput.value.trim()) {
      searchInput.dispatchEvent(new Event('input'));
    }
  });
});
