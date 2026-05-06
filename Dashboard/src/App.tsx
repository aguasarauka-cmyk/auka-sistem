/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { HashRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Overview } from './pages/Overview';
import { MapView } from './pages/MapView';
import { Prospects } from './pages/Prospects';
import { AgentActivity } from './pages/AgentActivity';
import { Chat } from './pages/Chat';

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="map" element={<MapView />} />
          <Route path="prospects" element={<Prospects />} />
          <Route path="agent-activity" element={<AgentActivity />} />
          <Route path="chat" element={<Chat />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}
