import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Download, FileDown } from 'lucide-react'
import type { ConfigExtraccion } from '@/types/expediente'

interface ExtraccionConfiguracionProps {
    config: ConfigExtraccion
    setConfig: (config: ConfigExtraccion) => void
    procesarConPDF: boolean
    setProcesarConPDF: (value: boolean) => void
    mostrarOpcionesAvanzadas: boolean
    setMostrarOpcionesAvanzadas: (value: boolean) => void
    onCargarBase: () => void
    onIniciar: () => void
}

export function ExtraccionConfiguracion({
    config,
    setConfig,
    procesarConPDF,
    setProcesarConPDF,
    mostrarOpcionesAvanzadas,
    setMostrarOpcionesAvanzadas,
    onCargarBase,
    onIniciar
}: ExtraccionConfiguracionProps) {
    return (
        <div className="space-y-6">
            {/* Opciones Básicas */}
            <div className="space-y-4">
                <h3 className="font-semibold text-lg">Opciones de Extracción</h3>

                {/* Headless */}
                <div className="flex items-center space-x-2">
                    <Checkbox
                        id="headless"
                        checked={config.headless}
                        onCheckedChange={(checked) => setConfig({ ...config, headless: checked as boolean })}
                    />
                    <label
                        htmlFor="headless"
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                        Modo invisible (más rápido, ejecutar sin interfaz gráfica)
                    </label>
                </div>

                {/* Umbral de errores */}
                <div className="space-y-2">
                    <label htmlFor="umbral-errores" className="text-sm font-medium">
                        Umbral de errores consecutivos (1-100)
                    </label>
                    <Input
                        id="umbral-errores"
                        type="number"
                        min={1}
                        max={100}
                        value={config.umbral_errores}
                        onChange={(e) => setConfig({ ...config, umbral_errores: parseInt(e.target.value) || 10 })}
                        className="w-32"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                        Detener extracción tras N errores consecutivos
                    </p>
                </div>

                <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <p className="text-sm text-blue-900 dark:text-blue-100">
                        ℹ️ La extracción puede tardar varios minutos dependiendo de la cantidad de expedientes.
                        El proceso se ejecuta de forma incremental para mayor confiabilidad.
                    </p>
                </div>
            </div>

            {/* Opciones Avanzadas (Colapsable) */}
            <div className="space-y-4 border-t pt-4">
                <button
                    type="button"
                    onClick={() => setMostrarOpcionesAvanzadas(!mostrarOpcionesAvanzadas)}
                    className="flex items-center justify-between w-full text-left"
                >
                    <h3 className="font-semibold text-lg">Opciones Avanzadas</h3>
                    <span className="text-sm text-gray-500">
                        {mostrarOpcionesAvanzadas ? '▼' : '▶'}
                    </span>
                </button>

                {mostrarOpcionesAvanzadas && (
                    <div className="space-y-4 pl-4">
                        {/* Timeout de página */}
                        <div className="space-y-2">
                            <label htmlFor="timeout-pagina" className="text-sm font-medium">
                                Timeout de página (5000-60000 ms)
                            </label>
                            <Input
                                id="timeout-pagina"
                                type="number"
                                min={5000}
                                max={60000}
                                step={1000}
                                value={config.timeout_pagina || 30000}
                                onChange={(e) => setConfig({ ...config, timeout_pagina: parseInt(e.target.value) || 30000 })}
                                className="w-40"
                            />
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Tiempo máximo de espera para cargar cada página
                            </p>
                        </div>

                        {/* Máximo de reintentos */}
                        <div className="space-y-2">
                            <label htmlFor="max-reintentos" className="text-sm font-medium">
                                Máximo de reintentos (1-10)
                            </label>
                            <Input
                                id="max-reintentos"
                                type="number"
                                min={1}
                                max={10}
                                value={config.max_reintentos || 3}
                                onChange={(e) => setConfig({ ...config, max_reintentos: parseInt(e.target.value) || 3 })}
                                className="w-32"
                            />
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Número de reintentos por página fallida
                            </p>
                        </div>

                        {/* Formatos de exportación */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">
                                Formatos de exportación
                            </label>
                            <div className="space-y-2">
                                {['json', 'excel', 'csv', 'html'].map((formato) => (
                                    <div key={formato} className="flex items-center space-x-2">
                                        <Checkbox
                                            id={`formato-${formato}`}
                                            checked={config.exportar_formatos?.includes(formato) ?? (formato === 'json')}
                                            onCheckedChange={(checked) => {
                                                const formatos = config.exportar_formatos || ['json']
                                                if (checked) {
                                                    setConfig({ ...config, exportar_formatos: [...formatos, formato] })
                                                } else {
                                                    setConfig({ ...config, exportar_formatos: formatos.filter(f => f !== formato) })
                                                }
                                            }}
                                        />
                                        <label
                                            htmlFor={`formato-${formato}`}
                                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                        >
                                            {formato.toUpperCase()}
                                        </label>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Separator */}
                        <div className="border-t my-4"></div>
                        <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">Control de Paginación</p>

                        {/* Detener en duplicado */}
                        <div className="flex items-center justify-between space-x-4">
                            <div className="flex-1">
                                <label htmlFor="detener-duplicado" className="text-sm font-medium">
                                    Detener al encontrar duplicados
                                </label>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                    Detiene la extracción cuando encuentra expedientes duplicados entre páginas
                                </p>
                            </div>
                            <Switch
                                id="detener-duplicado"
                                checked={config.detener_en_duplicado ?? true}
                                onCheckedChange={(checked) => setConfig({ ...config, detener_en_duplicado: checked })}
                            />
                        </div>

                        {/* Omitir duplicados */}
                        <div className="flex items-center justify-between space-x-4">
                            <div className="flex-1">
                                <label htmlFor="omitir-duplicado" className="text-sm font-medium">
                                    Omitir expedientes duplicados
                                </label>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                    Filtra automáticamente los expedientes duplicados de la lista final
                                </p>
                            </div>
                            <Switch
                                id="omitir-duplicado"
                                checked={config.omitir_duplicados ?? true}
                                onCheckedChange={(checked) => setConfig({ ...config, omitir_duplicados: checked })}
                            />
                        </div>

                        {/* Límite de páginas */}
                        <div className="space-y-2">
                            <label htmlFor="max-paginas" className="text-sm font-medium">
                                Límite de páginas (opcional)
                            </label>
                            <Input
                                id="max-paginas"
                                type="number"
                                min={1}
                                max={500}
                                placeholder="Sin límite"
                                value={config.max_paginas || ''}
                                onChange={(e) => setConfig({ ...config, max_paginas: e.target.value ? parseInt(e.target.value) : undefined })}
                                className="w-40"
                            />
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Detener tras procesar N páginas
                            </p>
                        </div>

                        {/* Fecha de corte */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">
                                Fecha de corte (opcional)
                            </label>
                            <Input
                                type="date"
                                value={config.fecha_corte || ''}
                                onChange={(e) => setConfig({ ...config, fecha_corte: e.target.value })}
                                className="w-48"
                            />
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Solo extraer expedientes desde esta fecha
                            </p>
                        </div>

                        {/* Procesar con PDF */}
                        <div className="flex items-center space-x-2">
                            <Checkbox
                                id="procesar-pdf"
                                checked={procesarConPDF}
                                onCheckedChange={(checked) => setProcesarConPDF(checked as boolean)}
                            />
                            <label
                                htmlFor="procesar-pdf"
                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                            >
                                Modo descarga de adjuntos (Descarga PDFs sin procesar vencimientos)
                            </label>
                        </div>
                    </div>
                )}
            </div>

            {/* Botón Iniciar */}
            <div className="flex gap-2">
                <Button
                    onClick={onCargarBase}
                    className="flex-1"
                    variant="outline"
                    size="lg"
                >
                    <FileDown className="h-4 w-4 mr-2" />
                    Cargar Última Extracción
                </Button>
                <Button
                    onClick={onIniciar}
                    className="flex-[2]"
                    size="lg"
                >
                    <Download className="h-4 w-4 mr-2" />
                    Iniciar Extracción Masiva Avanzada
                </Button>
            </div>
        </div>
    )
}
