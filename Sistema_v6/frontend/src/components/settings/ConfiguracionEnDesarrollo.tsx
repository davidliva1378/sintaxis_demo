/**
 * ConfiguracionEnDesarrollo - Placeholder para futuras configuraciones
 */

import { Code, Sparkles } from 'lucide-react'

export default function ConfiguracionEnDesarrollo() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg">
          <Code className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configuraciones En Desarrollo
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Funcionalidades experimentales y próximas configuraciones
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Banner de sección en construcción */}
        <div className="p-4 bg-yellow-50 dark:bg-yellow-900/10 rounded-lg border border-yellow-200 dark:border-yellow-800">
          <div className="flex items-start gap-3">
            <Sparkles className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
            <div>
              <h3 className="font-medium text-yellow-900 dark:text-yellow-300 mb-1">
                ⚠️ Sección en construcción
              </h3>
              <p className="text-sm text-yellow-800 dark:text-yellow-400">
                Esta sección contendrá configuraciones avanzadas y experimentales en futuras versiones.
              </p>
            </div>
          </div>
        </div>

        {/* Lista de próximas configuraciones */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            Próximas configuraciones planificadas:
          </h3>

          <ul className="space-y-3">
            <li className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <span className="text-blue-500 dark:text-blue-400 text-lg leading-none">•</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Notificaciones multi-canal:</strong>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Email, Telegram, WhatsApp, Discord
                </p>
              </div>
            </li>

            <li className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <span className="text-blue-500 dark:text-blue-400 text-lg leading-none">•</span>
              <div>
                <strong className="text-gray-900 dark:text-white">OCR para PDFs:</strong>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Extracción de texto de archivos escaneados
                </p>
              </div>
            </li>

            <li className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <span className="text-blue-500 dark:text-blue-400 text-lg leading-none">•</span>
              <div>
                <strong className="text-gray-900 dark:text-white">IA Local:</strong>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Integración con Ollama para análisis automático
                </p>
              </div>
            </li>

            <li className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <span className="text-blue-500 dark:text-blue-400 text-lg leading-none">•</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Procesamiento de PDFs:</strong>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  NER, búsqueda semántica, clasificación
                </p>
              </div>
            </li>

            <li className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <span className="text-blue-500 dark:text-blue-400 text-lg leading-none">•</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Configuración de plugins:</strong>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Habilitar/deshabilitar plugins del sistema
                </p>
              </div>
            </li>

            <li className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <span className="text-blue-500 dark:text-blue-400 text-lg leading-none">•</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Backup y exportación:</strong>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Configuración de respaldos automáticos
                </p>
              </div>
            </li>
          </ul>
        </div>

        {/* Info adicional */}
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-800 dark:text-blue-400">
            <strong>¿Tienes sugerencias?</strong> Si hay alguna configuración que te gustaría ver aquí,
            no dudes en solicitarla. Estamos constantemente mejorando el sistema.
          </p>
        </div>
      </div>
    </div>
  )
}
