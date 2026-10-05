import { useCallback, useMemo, useState } from 'react'
import { demoReports } from '../data/demoReports'
import { ReportsContext } from './ReportsContext'

export default function ReportsProvider({ children }) {
  const [reports, setReports] = useState(() => structuredClone(demoReports))

  const addReport = useCallback(({ description, location }) => {
    const report = {
      id: 'demo-' + crypto.randomUUID(),
      description,
      location,
      createdAt: new Date().toISOString(),
      source: 'session',
      analysis: null,
    }
    setReports((current) => [report, ...current])
    return report
  }, [])

  const value = useMemo(() => ({ reports, addReport }), [reports, addReport])

  return (
    <ReportsContext.Provider value={value}>{children}</ReportsContext.Provider>
  )
}
