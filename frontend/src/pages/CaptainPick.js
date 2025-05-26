import React, { useState } from 'react';
import { getCaptainPick } from '../api';

export default function CaptainPick() {
  const [teamJson, setTeamJson] = useState('');
  const [gameweek, setGameweek] = useState(1);
  const [subscription, setSubscription] = useState('basic');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePick = async () => {
    setLoading(true);
    try {
      const team = JSON.parse(teamJson);
      const res = await getCaptainPick(team, gameweek, subscription);
      setResult(res);
    } catch (e) {
      setResult({ error: 'Invalid team JSON or server error.' });
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>Captain Pick</h2>
      <textarea
        rows={8}
        cols={60}
        placeholder="Paste your team JSON here"
        value={teamJson}
        onChange={e => setTeamJson(e.target.value)}
      />
      <br />
      <label>Gameweek: <input type="number" value={gameweek} onChange={e => setGameweek(Number(e.target.value))} /></label>
      <br />
      <label>Subscription: <select value={subscription} onChange={e => setSubscription(e.target.value)}>
        <option value="basic">Basic</option>
        <option value="premium">Premium</option>
        <option value="elite">Elite</option>
      </select></label>
      <br />
      <button onClick={handlePick} disabled={loading}>Get Captain Pick</button>
      {result && (
        <div style={{ marginTop: 16 }}>
          {result.name ? (
            <div>
              <b>Captain:</b> {result.name} <br />
              <b>Predicted Points:</b> {result.predicted_points}
            </div>
          ) : result.error && <div style={{ color: 'red' }}>{result.error}</div>}
        </div>
      )}
    </div>
  );
}
