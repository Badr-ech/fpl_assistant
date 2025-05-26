import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const getTeamScore = async (team, gameweek) => {
  const res = await axios.post(`${API_URL}/team_score/rate`, { team, gameweek });
  return res.data;
};

export const getTransferSuggestions = async (team, budget, gameweek, subscription_tier) => {
  const res = await axios.post(`${API_URL}/recommendations/transfers`, { team, budget, gameweek, subscription_tier });
  return res.data;
};

export const getCaptainPick = async (team, gameweek, subscription_tier) => {
  const res = await axios.post(`${API_URL}/captain/best`, { team, gameweek, subscription_tier });
  return res.data;
};
