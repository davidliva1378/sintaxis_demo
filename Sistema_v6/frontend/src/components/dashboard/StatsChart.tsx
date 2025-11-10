import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface StatsChartProps {
  data: Array<{
    name: string
    activos: number
    completados: number
    pendientes: number
  }>
}

export default function StatsChart({ data }: StatsChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Estadísticas por Estado</CardTitle>
        <CardDescription>Distribución de expedientes por estado</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
            <XAxis
              dataKey="name"
              className="text-xs text-gray-600 dark:text-gray-400"
              tick={{ fill: 'currentColor' }}
            />
            <YAxis
              className="text-xs text-gray-600 dark:text-gray-400"
              tick={{ fill: 'currentColor' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Bar dataKey="activos" fill="#10b981" name="Activos" radius={[8, 8, 0, 0]} />
            <Bar dataKey="completados" fill="#3b82f6" name="Completados" radius={[8, 8, 0, 0]} />
            <Bar dataKey="pendientes" fill="#f59e0b" name="Pendientes" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
