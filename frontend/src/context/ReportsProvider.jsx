import { useCallback, useEffect, useMemo, useState } from 'react'
import { createReport, listReports } from '../services/api'
import { ReportsContext } from './ReportsContext'

export default function ReportsProvider({ children }) {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    listReports({ signal: controller.signal })
      .then((list) => {
        // A API lista do mais antigo para o mais novo.
        setReports(list.reverse())
        setError('')
      })
      .catch((err) => {
        if (err.name !== 'AbortError') setError(err.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [attempt])

  const reload = useCallback(() => {
    setLoading(true)
    setAttempt((current) => current + 1)
  }, [])

  const addReport = useCallback(async (data) => {
    const report = await createReport(data)
    setReports((current) => [report, ...current])
    return report
  }, [])

  const value = useMemo(
    () => ({ reports, loading, error, reload, addReport }),
    [reports, loading, error, reload, addReport],
  )

  return (
    <ReportsContext.Provider value={value}>{children}</ReportsContext.Provider>
  )
}
