import React, { useState } from 'react';
import { getTransferSuggestions } from '../api';

export default function TransferSuggestions() {
  const [teamJson, setTeamJson] = useState('');
  const [budget, setBudget] = useState(100);
  const [gameweek, setGameweek] = useState(1);
  const [subscription, setSubscription] = useState('basic');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSuggest = async () => {
    setLoading(true);
    try {
      const team = JSON.parse(teamJson);
      const res = await getTransferSuggestions(team, budget, gameweek, subscription);
      setResult(res);
    } catch (e) {
      setResult({ error: 'Invalid team JSON or server error.' });
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>Transfer Suggestions</h2>
      <textarea
        rows={8}
        cols={60}
        placeholder="Paste your team JSON here"
        value={teamJson}
        onChange={e => setTeamJson(e.target.value)}
      />
      <br />
      <label>Budget: <input type="number" value={budget} onChange={e => setBudget(Number(e.target.value))} /></label>
      <br />
      <label>Gameweek: <input type="number" value={gameweek} onChange={e => setGameweek(Number(e.target.value))} /></label>
      <br />
      <label>Subscription: <select value={subscription} onChange={e => setSubscription(e.target.value)}>
        <option value="basic">Basic</option>
        <option value="premium">Premium</option>
        <option value="elite">Elite</option>
      </select></label>
      <br />
      <button onClick={handleSuggest} disabled={loading}>Suggest Transfers</button>
      {result && (
        <div style={{ marginTop: 16 }}>
          {Array.isArray(result) ? result.map((t, i) => (
            <div key={i}>
              OUT: {t.player_out?.name} IN: {t.player_in?.name} (Impact: {t.predicted_impact?.toFixed(2)})
            </div>
          )) : result.error && <div style={{ color: 'red' }}>{result.error}</div>}
        </div>
      )}
    </div>
  );
}
