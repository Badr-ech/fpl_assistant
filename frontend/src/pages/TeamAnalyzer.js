import React, { useState } from 'react';
import { getTeamScore } from '../api';

export default function TeamAnalyzer() {
  const [teamJson, setTeamJson] = useState('');
  const [gameweek, setGameweek] = useState(1);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const team = JSON.parse(teamJson);
      const res = await getTeamScore(team, gameweek);
      setResult(res);
    } catch (e) {
      setResult({ error: 'Invalid team JSON or server error.' });
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>Team Analyzer</h2>
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
      <button onClick={handleAnalyze} disabled={loading}>Analyze</button>
      {result && (
        <div style={{ marginTop: 16 }}>
          <b>Score:</b> {result.score}
          {result.suggestions && (
            <div><b>Suggestions:</b> {result.suggestions.join(', ')}</div>
          )}
          {result.error && <div style={{ color: 'red' }}>{result.error}</div>}
        </div>
      )}
    </div>
  );
}
