/**
 * SettingsPage - Página de configuración del usuario
 */

import { useState } from 'react'
import { Settings, User, Key, Lock, Sliders, Activity, Globe, Download, Cog, Code, Server, Brain } from 'lucide-react'
import PerfilUsuario from '@/components/settings/PerfilUsuario'
import CredencialesPJN from '@/components/settings/CredencialesPJN'
import CambiarPassword from '@/components/settings/CambiarPassword'
import PreferenciasUsuario from '@/components/settings/PreferenciasUsuario'
import ConfiguracionMonitoreo from '@/components/settings/ConfiguracionMonitoreo'
import ConfiguracionBrowser from '@/components/settings/ConfiguracionBrowser'
import ConfiguracionScraping from '@/components/settings/ConfiguracionScraping'
import ConfiguracionAvanzada from '@/components/settings/ConfiguracionAvanzada'
import ConfiguracionEnDesarrollo from '@/components/settings/ConfiguracionEnDesarrollo'
import { ConfiguracionMCP } from '@/components/settings/ConfiguracionMCP'
import ConfiguracionIA from '@/components/settings/ConfiguracionIA'

type TabId = 'perfil' | 'credenciales' | 'password' | 'preferencias' | 'monitoreo' | 'browser' | 'scraping' | 'ia' | 'mcp' | 'avanzado' | 'desarrollo'

interface Tab {
  id: TabId
  label: string
  icon: React.ComponentType<{ className?: string }>
  description: string
}

const tabs: Tab[] = [
  {
    id: 'perfil',
    label: 'Perfil',
    icon: User,
    description: 'Información personal',
  },
  {
    id: 'credenciales',
    label: 'Credenciales PJN',
    icon: Key,
    description: 'Portal Judicial',
  },
  {
    id: 'password',
    label: 'Contraseña',
    icon: Lock,
    description: 'Cambiar contraseña',
  },
  {
    id: 'preferencias',
    label: 'Preferencias',
    icon: Sliders,
    description: 'Configuración general',
  },
  {
    id: 'monitoreo',
    label: 'Monitoreo',
    icon: Activity,
    description: 'Monitoreo automático',
  },
  {
    id: 'browser',
    label: 'Navegador',
    icon: Globe,
    description: 'Config. del navegador',
  },
  {
    id: 'scraping',
    label: 'Extracción',
    icon: Download,
    description: 'Timeouts y límites',
  },
  {
    id: 'ia',
    label: 'IA / RAG',
    icon: Brain,
    description: 'LLM y búsqueda',
  },
  {
    id: 'mcp',
    label: 'Servidor MCP',
    icon: Server,
    description: 'Claude Code',
  },
  {
    id: 'avanzado',
    label: 'Avanzado',
    icon: Cog,
    description: 'Storage y más',
  },
  {
    id: 'desarrollo',
    label: 'En Desarrollo',
    icon: Code,
    description: 'Features experimentales',
  },
]

export default function SettingsPage() {
  const [tabActiva, setTabActiva] = useState<TabId>('perfil')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
          <Settings className="h-6 w-6 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Configuración
          </h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">
            Gestiona tu perfil, credenciales y preferencias del sistema
          </p>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = tabActiva === tab.id

            return (
              <button
                key={tab.id}
                onClick={() => setTabActiva(tab.id)}
                className={`
                  group inline-flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                  transition-colors
                  ${isActive
                    ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:border-gray-300 dark:hover:border-gray-600'}
                `}
              >
                <Icon
                  className={`h-5 w-5 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300'}`}
                />
                <div className="text-left">
                  <div>{tab.label}</div>
                  <div className={`text-xs ${isActive ? 'text-blue-500 dark:text-blue-400' : 'text-gray-500 dark:text-gray-500'}`}>
                    {tab.description}
                  </div>
                </div>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="py-6">
        {tabActiva === 'perfil' && <PerfilUsuario />}
        {tabActiva === 'credenciales' && <CredencialesPJN />}
        {tabActiva === 'password' && <CambiarPassword />}
        {tabActiva === 'preferencias' && <PreferenciasUsuario />}
        {tabActiva === 'monitoreo' && <ConfiguracionMonitoreo />}
        {tabActiva === 'browser' && <ConfiguracionBrowser />}
        {tabActiva === 'scraping' && <ConfiguracionScraping />}
        {tabActiva === 'ia' && <ConfiguracionIA />}
        {tabActiva === 'mcp' && <ConfiguracionMCP />}
        {tabActiva === 'avanzado' && <ConfiguracionAvanzada />}
        {tabActiva === 'desarrollo' && <ConfiguracionEnDesarrollo />}
      </div>
    </div>
  )
}
