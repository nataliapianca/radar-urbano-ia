import { BrowserRouter, Route, Routes } from 'react-router'
import AppLayout from './components/AppLayout'
import ReportsProvider from './context/ReportsProvider'
import RegisterPage from './pages/RegisterPage'
import ReportsPage from './pages/ReportsPage'
import ReportDetailPage from './pages/ReportDetailPage'
import MapPage from './pages/MapPage'
import DashboardPage from './pages/DashboardPage'
import NotFoundPage from './pages/NotFoundPage'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <ReportsProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<RegisterPage />} />
            <Route path="relatos" element={<ReportsPage />} />
            <Route path="relatos/:reportId" element={<ReportDetailPage />} />
            <Route path="mapa" element={<MapPage />} />
            <Route path="painel" element={<DashboardPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </ReportsProvider>
    </BrowserRouter>
  )
}
