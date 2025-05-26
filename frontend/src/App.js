import React from 'react';
import { BrowserRouter as Router, Route, Switch, NavLink } from 'react-router-dom';
import TeamAnalyzer from './pages/TeamAnalyzer';
import TransferSuggestions from './pages/TransferSuggestions';
import CaptainPick from './pages/CaptainPick';
import './index.css';

function App() {
  return (
    <Router>
      <nav>
        <NavLink to="/" exact activeClassName="active">Team Analyzer</NavLink>
        <NavLink to="/transfers" activeClassName="active">Transfer Suggestions</NavLink>
        <NavLink to="/captain" activeClassName="active">Captain Pick</NavLink>
      </nav>
      <div className="container">
        <Switch>
          <Route path="/" exact component={TeamAnalyzer} />
          <Route path="/transfers" component={TransferSuggestions} />
          <Route path="/captain" component={CaptainPick} />
        </Switch>
      </div>
    </Router>
  );
}

export default App;
