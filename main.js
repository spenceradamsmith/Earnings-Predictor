// List of the 20 largest stocks’ tickers (e.g. by market cap). Used for Yahoo Finance calls.
const top20Tickers = [
  'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
  'NVDA', 'BRK.B','META', 'UNH',  'V',
  'JPM',  'JNJ',  'MA',   'PG',   'HD',
  'ADBE', 'PYPL', 'XOM',  'KO',   'PFE'
];

// Lists of the 20 largest stocks for each category
const categoryTickers = {
  Technology: [
    'AAPL','MSFT','GOOGL','ORCL','IBM',
    'INTC','CSCO','NVDA','AMD','ADBE',
    'SAP','CRM','TXN','QCOM','AVGO',
    'AMAT','MU','NOW','SNPS','TEAM'
  ],
  Healthcare: [
    'JNJ','PFE','UNH','MRK','ABBV',
    'LLY','ABT','TMO','AMGN','CVS',
    'GILD','BMY','ZTS','DHR','MDT',
    'SYK','BDX','IQV','BSX','ILMN'
  ],
  Financials: [
    'BRK.B','JPM','BAC','WFC','C',
    'GS','MS','AXP','USB','PNC',
    'TFC','BK','SCHW','BLK','PRU',
    'MET','AIG','MMC','ALL','CME'
  ],
  ConsumerDiscretionary: [
    'AMZN','TSLA','HD','MCD','NKE',
    'SBUX','LOW','CMG','MAR','BKNG',
    'TJX','ULTA','ROST','DRI','DIS',
    'WHR','YUM','GM','F','LEG'
  ],
  ConsumerStaples: [
    'PG','KO','PEP','WMT','COST',
    'MO','PM','CL','KMB','STZ',
    'GIS','MDLZ','MKC','HSY','KR',
    'KR','DG','EL','SYY','MNST'
  ],
  Energy: [
    'XOM','CVX','COP','SLB','PSX',
    'VLO','HES','EOG','PXD','OXY',
    'DVN','APA','MRO','MUR','EQT',
    'FTI','HAL','KMI','OKE','ENB'
  ],
  Industrials: [
    'BA','HON','UPS','CAT','GE',
    'LMT','DE','MMM','RTX','EMR',
    'PCAR','CMI','UNP','FDX','ROK',
    'NSC','CSX','NOC','TXT','DOV'
  ],
  Materials: [
    'LIN','APD','ECL','SHW','FCX',
    'DD','OLN','NEM','VMC','PPG',
    'STLD','CLF','NUE','BLL','SEE',
    'IFF','MOS','PKG','MLM','CF'
  ],
  Utilities: [
    'NEE','DUK','SO','AEP','EXC',
    'SRE','XEL','ED','D','WEC',
    'NRG','AES','PPL','PCG','EIX',
    'PEG','FE','ES','ATO','OGE'
  ],
  RealEstate: [
    'AMT','PLD','SPG','PSA','WPC',
    'CBRE','AVB','EQR','HST','ESS',
    'VTR','O','UDR','DLR','EQIX',
    'KIM','IRM','FRT','REG','SLG'
  ],
  CommunicationServices: [
    'GOOGL','META','NFLX','DIS','CMCSA',
    'T','VZ','ATVI','EA','TTWO',
    'CHTR','VIAC','DISH','SPOT','ROKU',
    'PINS','SNAP','WB','OMC','MTCH'
  ]
};

document.addEventListener('DOMContentLoaded', () => {
    const nav = document.querySelector('.categories-nav');
    nav.addEventListener('click', (e) => {
        if (e.target.tagName === 'BUTTON') {
            nav.querySelectorAll('button').forEach(btn => btn.classList.remove('selected'));
            e.target.classList.add('selected');
            const category = e.target.textContent;
            const tickers = categoryTickers[category];
        }
    });
});
