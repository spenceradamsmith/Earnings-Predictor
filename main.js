const customLogos = window.customLogos || {};

function getLogoSrc(ticker, fallbackLogo) {
  return customLogos[ticker] || fallbackLogo;
}

const top20Tickers = [
  'AAPL','MSFT','GOOGL','AMZN','TSLA',
  'NVDA','BRK.B','META','UNH','V',
  'JPM','JNJ','MA','PG','HD',
  'ADBE','PYPL','XOM','KO','PFE'
];

const categoryTickers = {
  'All': top20Tickers,
  'Technology': [
    'AAPL','MSFT','GOOGL','ORCL','IBM',
    'INTC','CSCO','NVDA','AMD','ADBE',
    'SAP','CRM','TXN','QCOM','AVGO',
    'AMAT','MU','NOW','SNPS','TEAM'
  ],
  'Healthcare': [
    'JNJ','PFE','UNH','MRK','ABBV',
    'LLY','ABT','TMO','AMGN','CVS',
    'GILD','BMY','ZTS','DHR','MDT',
    'SYK','BDX','IQV','BSX','ILMN'
  ],
  'Financials': [
    'BRK.B','JPM','BAC','WFC','C',
    'GS','MS','AXP','USB','PNC',
    'TFC','BK','SCHW','BLK','PRU',
    'MET','AIG','MMC','ALL','CME'
  ],
  'Consumer Discretionary': [
    'AMZN','TSLA','HD','MCD','NKE',
    'SBUX','LOW','CMG','MAR','BKNG',
    'TJX','ULTA','ROST','DRI','DIS',
    'WHR','YUM','GM','F','LEG'
  ],
  'Consumer Staples': [
    'PG','KO','PEP','WMT','COST',
    'MO','PM','CL','KMB','STZ',
    'GIS','MDLZ','MKC','HSY','KR',
    'DG','EL','SYY','MNST'
  ],
  'Energy': [
    'XOM','CVX','COP','SLB','PSX',
    'VLO','HES','EOG','PXD','OXY',
    'DVN','APA','MRO','MUR','EQT',
    'FTI','HAL','KMI','OKE','ENB'
  ],
  'Industrials': [
    'BA','HON','UPS','CAT','GE',
    'LMT','DE','MMM','RTX','EMR',
    'PCAR','CMI','UNP','FDX','ROK',
    'NSC','CSX','NOC','TXT','DOV'
  ],
  'Materials': [
    'LIN','APD','ECL','SHW','FCX',
    'DD','OLN','NEM','VMC','PPG',
    'STLD','CLF','NUE','BLL','SEE',
    'IFF','MOS','PKG','MLM','CF'
  ],
  'Utilities': [
    'NEE','DUK','SO','AEP','EXC',
    'SRE','XEL','ED','D','WEC',
    'NRG','AES','PPL','PCG','EIX',
    'PEG','FE','ES','ATO','OGE'
  ],
  'Real Estate': [
    'AMT','PLD','SPG','PSA','WPC',
    'CBRE','AVB','EQR','HST','ESS',
    'VTR','O','UDR','DLR','EQIX',
    'KIM','IRM','FRT','REG','SLG'
  ],
  'Communication Services': [
    'GOOGL','META','NFLX','DIS','CMCSA',
    'T','VZ','ATVI','EA','TTWO',
    'CHTR','VIAC','DISH','SPOT','ROKU',
    'PINS','SNAP','WB','OMC','MTCH'
  ]
};

document.addEventListener('DOMContentLoaded', () => {
  console.log('▶ DOM fully loaded');
  const nav       = document.querySelector('.categories-nav');
  const cardsGrid = document.querySelector('.cards-grid');
  const now       = Date.now();
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

        // parse date
        let date;
        if (json.earnings_date) {
          date = new Date(json.earnings_date);
        } else if (json.days_until != null) {
          date = new Date(now + json.days_until * MS_PER_DAY);
        } else {
          return null;
        }

        // compute days until for countdown
        const daysUntil = Math.ceil((date - now) / MS_PER_DAY);

        return {
          ticker:       ticker,
          name:         json.company_name,
          logo:         json.logo,
          date:         date,
          expected_eps: json.expected_eps,
          days_until:   daysUntil,
          raw_beat_pct: json.raw_beat_pct  // may be undefined
        };
      } catch (err) {
        console.warn(`✖️ ${ticker} failed:`, err);
        return null;
      }
    }));

    // filter out nulls, sort by proximity
    const items = responses
      .filter(x => x && x.date instanceof Date && !isNaN(x.date))
      .sort((a, b) => Math.abs(a.date - now) - Math.abs(b.date - now));

    // clear out old cards
    cardsGrid.innerHTML = '';

    // render
    items.forEach(item => {
      const card = document.createElement('div');
      // choose mode based on presence of raw_beat_pct
      if (typeof item.raw_beat_pct === 'number') {
        card.classList.add('card', 'mode-prediction');
        const pct = item.raw_beat_pct;
        // compute gauge arc
        const angle = item.raw_beat_pct * Math.PI;
        const cx = 50, cy = 50, r = 40;
        const x = cx + r * Math.cos(Math.PI - angle);
        const y = cy - r * Math.sin(Math.PI - angle);
        // large‐arc‐flag = raw_beat_pct > 0.5 ? 1 : 0
        const laf = item.raw_beat_pct > 0.5 ? 1 : 0;

        card.innerHTML = `
          <div class="card-content">
            <div class="logo">
              <img src="${getLogoSrc(item.ticker, item.logo)}" alt="${item.name} logo"/>
            </div>
            <div class="header">
              <h2 class="company">${item.name}</h2>
              <span class="ticker">${item.ticker}</span>
            </div>
            <div class="details">
              <div class="info">
                <span class="label">Next Release:</span>
                <span class="value">${item.date.toLocaleDateString()}</span>
              </div>
              <div class="info">
                <span class="label">Expected EPS:</span>
                <span class="value">${item.expected_eps}</span>
              </div>
            </div>
            <div class="visual prediction">
              <svg class="gauge" viewBox="0 0 100 50">
                <path class="bg" d="M10,50 A40,40 0 0,1 90,50"/>
                <path 
                  class="fg" 
                  d="M10,50 A40,40 0 ${laf},1 ${x.toFixed(1)},${y.toFixed(1)}"
                />
              </svg>
              <div class="percent">${pct}%</div>
            </div>
          </div>
        `;
      } else {
        card.classList.add('card', 'mode-countdown');
        card.innerHTML = `
          <div class="card-content">
            <div class="logo">
              <img src="${getLogoSrc(item.ticker, item.logo)}" alt="${item.name} logo"/>
            </div>
            <div class="header">
              <h2 class="company">${item.name}</h2>
              <span class="ticker">${item.ticker}</span>
            </div>
            <div class="details">
              <div class="info">
                <span class="label">Next Release:</span>
                <span class="value">${item.date.toLocaleDateString()}</span>
              </div>
              <div class="info">
                <span class="label">Expected EPS:</span>
                <span class="value">${item.expected_eps}</span>
              </div>
            </div>
            <div class="visual countdown">
              <div class="count">${item.days_until - 7}</div>
              <div class="unit">days until release</div>
            </div>
          </div>
        `;
      }

      cardsGrid.appendChild(card);
    });
  }

  //
  // 3) Wire up category buttons
  //
  nav.addEventListener('click', e => {
    if (e.target.tagName !== 'BUTTON') return;
    nav.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
    e.target.classList.add('selected');
    fetchAndDisplay(e.target.textContent);
  });

  //
  // 4) Auto-click “All” on load
  //
  const initial = nav.querySelector('button.selected') || nav.querySelector('button');
  if (initial) initial.click();
});