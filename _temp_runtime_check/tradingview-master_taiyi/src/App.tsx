import TradingView from "./tradingview";

function App() {
  const defaultSymbol = process.env.REACT_APP_DEFAULT_SYMBOL;

  if (!defaultSymbol) {
    return <div>Please set REACT_APP_DEFAULT_SYMBOL before running this demo.</div>;
  }

  return (
    <div className="App">
      <TradingView symbol={defaultSymbol} />
    </div>
  );
}

export default App;
